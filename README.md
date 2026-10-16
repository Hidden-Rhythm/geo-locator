 <div align="center">

# 📍 GEO LOCATOR

### `Locate. Analyze. Report.`

**A Python-based geolocation tool with OS, Wi-Fi, and IP detection — built with Discord webhook reporting.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-181717?style=for-the-badge&logo=linux&logoColor=white)](#-platform-support)
[![Version](https://img.shields.io/badge/Version-1.0.0-8A2BE2?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-Check%20Repository-gray?style=for-the-badge)](#)

<br>

**A lightweight, multi-source location utility designed for the terminal.**

[Features](#-features) · [Installation](#-installation) · [Configuration](#-configuration) · [Usage](#-usage)

</div>

---

## ◈ Overview

**Geo Locator** is a Python command-line tool that gathers location and network information using multiple detection methods. It attempts to determine location through operating-system services and Wi-Fi positioning, with IP geolocation as a fallback.

It can then format the collected information into a Discord embed and send it to a configured webhook.

> Designed for a simple workflow: run the script, collect available information, and review the generated report.

## ✦ Features

<table>
<tr>
<td width="50%">

### 🌐 Multi-Source Location
Uses available OS location services, Wi-Fi positioning, and IP-based geolocation.

</td>
<td width="50%">

### 🛰️ Provider Fallback
Tries alternative location providers when earlier methods are unavailable.

</td>
</tr>
<tr>
<td width="50%">

### 🖥️ System Information
Collects available details such as operating system, Python version, hostname, and local IP.

</td>
<td width="50%">

### 📡 Network Details
Can report public IP, ISP or organization, and IP-derived region information.

</td>
</tr>
<tr>
<td width="50%">

### 💬 Discord Integration
Formats results into an embed and sends them to a configured Discord webhook.

</td>
<td width="50%">

### 🧪 Dry-Run Mode
Preview the generated Discord embed as JSON without sending a webhook message.

</td>
</tr>
</table>

## ⚡ How It Works

```text
          ┌─────────────────────┐
          │     GEO LOCATOR     │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  OS Location APIs   │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Wi-Fi Positioning  │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  IP Geolocation     │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Build Report       │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │ Discord Webhook     │
          └─────────────────────┘
```

*Actual location accuracy and available methods depend on the operating system, hardware, network, and external services.*

## ⬇ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Hidden-Rhythm/geo-locator.git
cd geo-locator
```

### 2. Check Python

```bash
python --version
```

Python 3.10 or newer is recommended.

### 3. Configure the tool

Open `geo-locator.py` and find the configuration section near the top of the file.

## ⚙ Configuration

Set the values you need directly in the script.

```python
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"
DISCORD_USERNAME = "geolocate"

LOCATION_TIMEOUT = 20.0
IP_TIMEOUT = 8.0
WEBHOOK_TIMEOUT = 10.0
```

| Setting | Purpose |
|---|---|
| `DISCORD_WEBHOOK_URL` | Discord webhook used to deliver reports |
| `DISCORD_USERNAME` | Username displayed for webhook messages |
| `LOCATION_TIMEOUT` | Maximum wait for location detection |
| `IP_TIMEOUT` | Maximum wait for IP lookup |
| `WEBHOOK_TIMEOUT` | Maximum wait for webhook requests |

**Keep your webhook URL private.** Anyone with access to it may be able to send messages through your webhook.

## 🚀 Usage

Run the script:

```bash
python geo-locator.py
```

### Available options

| Command | Description |
|---|---|
| `python geo-locator.py --help` | Display available command-line options |
| `python geo-locator.py --version` | Display the current version |
| `python geo-locator.py --dry-run` | Print the Discord embed JSON without sending it |
| `python geo-locator.py --verbose` | Display additional diagnostic information |
| `python geo-locator.py --timeout 30` | Set the location timeout to 30 seconds |

Combine diagnostic mode with a dry run:

```bash
python geo-locator.py --dry-run --verbose
```

**Note:** Normal execution requires a configured Discord webhook URL.

## 🖥️ Platform Support

| Platform | Available location methods |
|---|---|
| Windows | Windows location API, Wi-Fi positioning, IP lookup |
| macOS | CoreLocation when the required PyObjC support is available, Wi-Fi positioning, IP lookup |
| Linux | GPS through `gpsd` when configured, Wi-Fi positioning, IP lookup |

Some platform-specific methods require additional system setup or optional dependencies. A fallback method may be used when a preferred method is unavailable.

## 🔐 Privacy & Responsible Use

Geo Locator can collect sensitive information, including public IP addresses, local network details, hostnames, and potentially geographic coordinates.

- Use it only on systems and networks you own or have permission to inspect.
- Configure only a Discord webhook you control or are authorized to use.
- Remember that external geolocation services may receive network information or Wi-Fi access-point identifiers.
- Review generated reports before sharing them.
- Do not publish webhook URLs or collected location data in public repositories.

Location results may be approximate or unavailable. IP-based geolocation does not reliably identify an exact physical address.

## 🛠 Troubleshooting

<details>
<summary><strong>Location could not be detected</strong></summary>

Check whether location services are enabled, the required platform dependencies are available, and the network connection is working. The tool may fall back to IP-based geolocation.

</details>

<details>
<summary><strong>Discord report was not delivered</strong></summary>

Verify the webhook URL in `geo-locator.py`, check your internet connection, and run with `--verbose` to inspect diagnostic output.

</details>

<details>
<summary><strong>Want to test without sending a message?</strong></summary>

Use `python geo-locator.py --dry-run` to inspect the generated embed JSON.

</details>

---

## ◈ Developer

<div align="center">

### Hidden-Rhythm

*Building useful tools, one project at a time.*

[![GitHub](https://img.shields.io/badge/GitHub-Hidden--Rhythm-181717?style=for-the-badge&logo=github)](https://github.com/Hidden-Rhythm)

**Explore more projects:** [github.com/Hidden-Rhythm](https://github.com/Hidden-Rhythm)

<br>

*Made with Python 🐍*

</div>
