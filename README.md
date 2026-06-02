# WCP Widget — GitHub

A [Widget Context Protocol (WCP)](https://widgetcontextprotocol.com) widget container
that brings your GitHub repositories into any WCP-compatible dashboard. Browse all your
repos with live metadata — language, visibility, last push time — without leaving your
dashboard. Authenticates via your own Personal Access Token; no data passes through any
third party.

**Specification:** [widgetcontextprotocol.com](https://widgetcontextprotocol.com)  
**Part of the** [Penrith Beacon WCP](https://penrithbeacon.com) widget suite.

> **WCP 1.4.0 certified.** This widget implements the full
> [Widget Context Protocol 1.4.0](https://widgetcontextprotocol.com) specification,
> including server UUID, Container Directory (`GET /wcp`), and all four `Wcp-*` request headers.

---

## Components

The widget exposes **three components**, each sized at `12 × 6` by default — a full stave
in standard Penrith Beacon WCP layout. The intended usage is a dedicated **GitHub
orchestration** with components on separate staves, switched to via the Orchestration
Manager whenever you want to browse your repositories.

| Component | Default size | What it shows |
|-----------|:------------:|---------------|
| **Repositories** | 12 × 6 | All GitHub repos sorted by last push. Name, language, visibility badge, archived/fork badge, relative push time, and Open button per card. |
| **Settings** | 12 × 6 | Personal Access Token configuration. Shows the connected account name once saved. |
| **Help** | 12 × 6 | Step-by-step setup guide, FAQ, and reference links. |

---

## Requirements

- Docker and Docker Compose
- A GitHub account with a Personal Access Token

---

## Quick Start

```bash
docker run -d \
  --name wcp-widget-github \
  -p 3743:3743 \
  -v gh-data:/app/data \
  --restart unless-stopped \
  penrithbeacon/wcp-widget-github:latest
```

Then add it to your WCP dashboard at `http://localhost:3743`.

---

## Docker Compose

Clone this repository and run:

```bash
docker compose up -d
```

Or use this compose snippet directly:

```yaml
services:
  github:
    image: penrithbeacon/wcp-widget-github:latest
    container_name: wcp-widget-github
    ports:
      - "3743:3743"
    volumes:
      - gh-data:/app/data
    restart: unless-stopped

volumes:
  gh-data:
```

---

## Setup Guide

You need a GitHub Personal Access Token before the widget can show your repositories.

### 1. Create a Personal Access Token (classic)

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token** → **Generate new token (classic)**
3. Give it a descriptive name (e.g. "Penrith Beacon WCP")
4. Set an expiry that suits your security policy
5. Select the required scope:

   | Scope | Access |
   |-------|--------|
   | `repo` | Public and private repositories (recommended) |
   | `public_repo` | Public repositories only |

6. Click **Generate token**
7. Copy the token immediately — GitHub only shows it once

> **Fine-grained tokens.** If you prefer GitHub's fine-grained tokens, select
> **Repository access → All repositories** and grant **Contents: Read-only** and
> **Metadata: Read-only** permissions.

### 2. Configure the widget

Open the **Settings** component, paste your token, and click **Save Settings**.
The connected account name appears in the status bar once the token is verified.
The Repositories component will immediately show your live data.

---

## WCP Request Headers

This widget supports the WCP 1.3.1 instance headers for multi-instance deployment:

| Header | Required | Description |
|--------|----------|-------------|
| `Wcp-Instance-Id` | Required | UUID identifying this widget instance |
| `Wcp-Dashboard-Id` | Optional | UUID identifying the requesting dashboard |
| `Wcp-Version` | Optional | Protocol version the dashboard speaks |

Each instance stores its token separately inside the Docker volume
(`config-<instance-id>.json`), so a single container can serve multiple dashboards
with independent GitHub accounts.

---

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /widget/` | GET | Compact widget card (iframe) |
| `GET /widget/wcp` | GET | WCP 1.3.1 manifest |
| `GET /widget/health` | GET | `{"status":"ok","name":"GitHub"}` |
| `GET /widget/icon.svg` | GET | Widget icon (SVG) |
| `GET /widget/repos` | GET | Repositories component page |
| `GET /widget/settings` | GET | Settings component page |
| `GET /widget/help` | GET | Help component page |
| `POST /widget/configure` | POST | Save Personal Access Token |
| `GET /widget/api/config-status` | GET | Configuration status (token masked, account name) |
| `GET /widget/api/repos` | GET | Repository list (60 s cache) |
| `GET /widget/api/guids` | GET | Component UUIDs for Bonjour discovery |
| `GET /widget/export.wcp` | GET | Self-export as a `.wcp` package |

---

## Data Storage

Your token is stored in `/app/data/config.json` (or `/app/data/config-<instance-id>.json`
for multi-instance deployments) inside the container's named Docker volume. **Credentials
never leave your machine** — they are used only in direct API calls to GitHub.

| Data | Cache TTL |
|------|-----------|
| Repositories | 60 seconds |

Click the Refresh button to bypass the cache immediately.

---

## FAQ

**Where is the token stored?**  
Inside the Docker volume `gh-data` at `/app/data/`. Nothing is sent to any third party
other than the GitHub API.

**Can I use this with a GitHub organisation?**  
Yes. The widget fetches `GET /user/repos?type=all`, which includes personal repos and
any organisation repos you have access to under the authenticated account.

**Can I run multiple instances for different GitHub accounts?**  
Yes. Each WCP dashboard instance sends a `Wcp-Instance-Id` header; the widget stores
separate tokens per instance in the same volume.

**What are the rate limits?**  
GitHub allows 5 000 authenticated API requests per hour. Fetching all repositories for
a typical account uses 1–3 requests, well within the limit.

**What if my token expires or leaks?**  
Revoke it from [github.com/settings/tokens](https://github.com/settings/tokens),
generate a new one, and paste it into the Settings component.

---

## WCP Compatibility

| Property | Value |
|----------|-------|
| WCP Version | 1.3.1 |
| Widget Version | 1.0.0 |
| Render mode | iframe |
| Auth | none (token stored server-side) |
| Default card size | 12 × 6 |
| Multi-instance | Yes — per `Wcp-Instance-Id` |

---

## Technical Details

- **Base image:** `python:3.12-slim`
- **Port:** `3743`
- **Framework:** Flask
- **External calls:** GitHub API only (`api.github.com`)
- **Persistent storage:** Named Docker volume `gh-data`

---

## Links

- [Penrith Beacon](https://penrithbeacon.com)
- [Widget Context Protocol specification](https://widgetcontextprotocol.com)
- [GitHub REST API documentation](https://docs.github.com/en/rest)
- [Docker Hub — penrithbeacon/wcp-widget-github](https://hub.docker.com/r/penrithbeacon/wcp-widget-github)
