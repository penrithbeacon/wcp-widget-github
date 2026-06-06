# WCP Widget: GitHub

A [Widget Context Protocol (WCP)](https://widgetcontextprotocol.com) compliant widget
container that brings your GitHub repositories into any WCP-compatible dashboard. Browse
all your repos with live metadata — language, visibility, last push time — without leaving
your dashboard. Authenticates via your own Personal Access Token; no data passes through
any third party.

**Specification:** [widgetcontextprotocol.com](https://widgetcontextprotocol.com)

## Quick Start

```bash
docker run -d \
  --name wcp-widget-github \
  -p 3743:3743 \
  -v gh-data:/app/data \
  --restart unless-stopped \
  docker.io/penrithbeacon/wcp-widget-github:latest
```

Then add it to your WCP dashboard at the container's network address.

## Docker Compose

```yaml
services:
  github:
    image: docker.io/penrithbeacon/wcp-widget-github:latest
    container_name: wcp-widget-github
    ports:
      - "3743:3743"
    volumes:
      - gh-data:/app/data
    restart: unless-stopped

volumes:
  gh-data:
```

## Components

The widget exposes three components, each `12 × 6` by default (full stave in Penrith Beacon WCP):

| Component | What it shows |
|-----------|---------------|
| **Repositories** | All GitHub repos sorted by last push. Name, language, visibility, archived/fork badges, relative push time, Open button. |
| **Settings** | Personal Access Token configuration. Shows connected account name once saved. |
| **Help** | Step-by-step setup guide, FAQ, and reference links. |

## Setup

Create a GitHub Personal Access Token at [github.com/settings/tokens](https://github.com/settings/tokens)
with the `repo` scope (or `public_repo` for public repos only). Open the **Settings** component
and paste it in.

## WCP Request Headers

This widget supports the WCP 2.0.0 request headers:

| Header | Required | Description |
|--------|----------|-------------|
| `Wcp-Instance-Id` | Required | UUID identifying this widget instance |
| `Wcp-Dashboard-Id` | Optional | UUID identifying the requesting dashboard |
| `Wcp-Version` | Optional | Protocol version the dashboard speaks |
| `Wcp-Widget-Id` | Optional | Widget ID from Container Directory selection |
| `Wcp-Orchestration-Id` | Optional | UUID of the active orchestration — shared state key for multi-component coordination |
| `Wcp-Application-Id` | Optional | UUID of the active application window (kiosk only) — combined with orchestration ID for full isolation |

## WCP Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /wcp` | WCP 2.0.0 Container Directory |
| `GET /widget/` | Compact widget card (iframe) |
| `GET /widget/wcp` | WCP 2.0.0 manifest |
| `GET /widget/health` | Health check |
| `GET /widget/icon.svg` | Widget icon (SVG) |
| `GET /widget/repos` | Repositories component page |
| `GET /widget/settings` | Settings component page |
| `GET /widget/help` | Help component page |
| `POST /widget/configure` | Save Personal Access Token |
| `GET /widget/api/config-status` | Configuration status (token masked, account name) |
| `GET /widget/api/repos` | Repository list (60 s cache) |
| `GET /widget/api/guids` | Component UUIDs for Bonjour discovery |
| `GET /widget/export.wcp` | Self-export as a `.wcp` package |

## WCP Compatibility

| Property | Value |
|----------|-------|
| WCP Version | 2.0.0 |
| Widget Version | 1.1.0 |
| Render mode | iframe |
| Auth | none (token stored server-side) |
| Default card size | 12 × 6 |
| Multi-instance | Yes — per `Wcp-Instance-Id` |

## Technical Details

- **Base image:** `python:3.12-slim`
- **Platforms:** `linux/amd64`, `linux/arm64`
- **Port:** `3743`
- **Dependencies:** Flask, requests
- **Persistent storage:** Named Docker volume `gh-data` stores per-instance tokens
- **External calls:** GitHub API only — no third-party services

## Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release — multi-arch (`linux/amd64`, `linux/arm64`) |
| `1.3.0-wcp2.1.0` | Widget v1.3.0, WCP 2.1.0 — `/widget/health` returns `container` name |
| `1.2.0-wcp2.1.0` | Widget v1.2.0, WCP 2.1.0 — WCP 2.1.0 upgrade, orchestration ID context |
| `1.1.0-wcp2.0.0` | Widget v1.1.0, WCP 2.0.0 — container block, manifest image source |
| `1.0.1-wcp1.4.0` | Widget v1.0.1, WCP 2.0.0 — server UUID, Container Directory, CORS, Wcp-Widget-Id |
| `1.0.0-wcp1.3.1` | Widget v1.0.0, WCP 1.3.1 — initial release |

> **Platform history:** `latest` was rebuilt as a multi-arch image on 2026-06-05, adding `linux/amd64` support (Synology NAS, Intel/AMD servers). All version-specific tags (`1.0.0-wcp1.3.1` through `1.1.0-wcp2.0.0`) were originally built on Apple Silicon and are `linux/arm64` only.

## Source

- Docker Hub: [penrithbeacon/wcp-widget-github](https://hub.docker.com/r/penrithbeacon/wcp-widget-github)
- GitHub: [penrithbeacon/wcp-widget-github](https://github.com/penrithbeacon/wcp-widget-github)
- WCP Specification: [widgetcontextprotocol.com](https://widgetcontextprotocol.com)
