# 📍 Geo Locator

<div align="center">

**A lightweight Python-based geolocation tool with Discord webhook reporting.**

Detect your machine's approximate or available device location, collect network information, and send a detailed location report directly to Discord.

[Features](#-features) · [Installation](#-installation) · [Configuration](#-configuration) · [Usage](#-usage) · [Disclaimer](#-disclaimer)

</div>

---

## ✨ Features

- 📍 **Multi-source location detection** — Attempts operating-system location services, Wi-Fi positioning, and IP geolocation.
- 🌐 **IP information** — Collects public IP, local IP, ISP, and available geographic information.
- 🖥️ **System information** — Reports hostname, operating system, and Python version.
- 🎯 **Accuracy information** — Displays reported location accuracy when available.
- 🗺️ **Google Maps integration** — Generates a direct map link for the detected coordinates.
- 💬 **Discord webhook reporting** — Sends the results in a formatted Discord embed.
- 🔄 **Provider fallback** — Tries alternative location sources when a provider fails.
- 🛠️ **Configurable timeouts** — Control how long location providers can take.
- 🧪 **Dry-run mode** — Preview the Discord embed as JSON without sending it.
- 🔍 **Verbose diagnostics** — Inspect provider attempts and troubleshooting information.
- 🐍 **Python standard library** — Core functionality uses Python's built-in modules, with optional platform-specific support.

## ⚙️ How It Works

Geo Locator follows a fallback-based detection process:

1. **OS location services** — Attempts to obtain coordinates from supported operating-system location APIs.
2. **Wi-Fi positioning** — Uses visible Wi-Fi access points with supported positioning services.
3. **IP geolocation** — Falls back to external IP geolocation providers when other methods fail.
4. **Report generation** — Formats the available coordinates and system/network information into a Discord embed.
5. **Discord delivery** — Sends the report through your configured webhook.

> Location accuracy depends on your operating system, available hardware, network configuration, and external providers. IP-based locations may identify only your approximate area.

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Hidden-Rhythm/geo-locator.git
cd geo-locator
```

### 2. Check Python

Python 3.10 or newer is recommended.

```bash
python --version
```

### 3. Configure Discord

Create a webhook in a Discord channel you control:

1. Open the channel's settings.
2. Find **Integrations → Webhooks**.
3. Create a webhook and copy its URL.
4. Open `geo-locator.py` and update the configuration.

## 🔧 Configuration

At the top of `geo-locator.py`, configure these values:

```python
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"
DISCORD_USERNAME = "geolocate"

LOCATION_TIMEOUT = 20.0
IP_TIMEOUT = 8.0
WEBHOOK_TIMEOUT = 10.0
```

| Setting | Description |
|---|---|
| `DISCORD_WEBHOOK_URL` | Discord webhook used to deliver reports |
| `DISCORD_USERNAME` | Username displayed by the webhook |
| `LOCATION_TIMEOUT` | Timeout for each location provider |
| `IP_TIMEOUT` | Timeout for IP information requests |
| `WEBHOOK_TIMEOUT` | Timeout for Discord HTTP requests |

**Security:** Keep your webhook URL private. Anyone who obtains it may be able to post messages to its associated channel. Do not publish a real webhook URL in your repository.

## 🚀 Usage

Run Geo Locator from your terminal.

### Standard execution

```bash
python geo-locator.py
```

This attempts to resolve the location and send the report to Discord.

### Preview the report without sending it

```bash
python geo-locator.py --dry-run
```

Prints the generated embed payload as JSON. This is useful for testing the report format without configuring a webhook.

### Enable diagnostic output

```bash
python geo-locator.py --verbose
```

Displays diagnostic messages about provider attempts, network errors, and execution progress.

### Change the location timeout

```bash
python geo-locator.py --timeout 30
```

Sets the per-provider location timeout to 30 seconds.

### Display the version

```bash
python geo-locator.py --version
```

### View all available options

```bash
python geo-locator.py --help
```

## 📊 Discord Report

When a location is resolved, the embed can include:

- Latitude and longitude
- Reported accuracy, when available
- Detection method
- Public and local IP addresses
- ISP or network organization
- Hostname and operating system
- Python version
- IP-derived city, region, country, and timezone when available
- Execution time
- Google Maps link

If no provider can resolve the location, Geo Locator generates a failure report instead.

## 🖥️ Platform Support

| Platform | Location methods |
|---|---|
| Windows | Windows Location API, Wi-Fi positioning, IP geolocation |
| macOS | CoreLocation when the required PyObjC bindings are available, Wi-Fi positioning, IP geolocation |
| Linux | GPS through `gpsd` when configured, Wi-Fi positioning, IP geolocation |

Availability depends on installed components, permissions, hardware, and provider access. Some location methods may be unavailable on a particular machine.

## 🧰 Troubleshooting

**No location detected**

- Check your internet connection.
- Ensure your device's location services are enabled.
- Check Wi-Fi availability and location permissions.
- Run with `--verbose` to inspect provider failures.

**Discord report not received**

- Verify `DISCORD_WEBHOOK_URL`.
- Make sure the webhook still exists and has permission to post.
- Check the terminal output for HTTP or network errors.

**Location is inaccurate**

- IP geolocation is approximate and may identify your ISP's network location rather than your physical location.
- Device and Wi-Fi positioning accuracy varies by environment.

**Test without Discord**

```bash
python geo-locator.py --dry-run --verbose
```

## 🔒 Disclaimer

Geo Locator is intended for legitimate device diagnostics, geolocation experiments, and systems you own or are authorized to inspect.

Running the tool may transmit network information and Wi-Fi access point identifiers to external location providers. When Discord reporting is enabled, the generated report may disclose IP addresses, coordinates, hostname, and system details to the configured Discord channel.

Use it responsibly, protect your webhook URL, and obtain appropriate permission before collecting or sharing device information.

## 👨‍💻 Author

**Hidden-Rhythm**

- GitHub: [@Hidden-Rhythm](https://github.com/Hidden-Rhythm)
- Repository: [geo-locator](https://github.com/Hidden-Rhythm/geo-locator)

---

<div align="center">

**Built with Python 🐍**

*Locate. Analyze. Report.*

</div>
