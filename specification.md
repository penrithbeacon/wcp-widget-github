# GitHub — Specification

## Overview
GitHub repositories — browse all repos for the authenticated account, sorted by last push. Manage credentials via the Settings component.

- **Port:** 3743
- **Container:** `wcp-widget-github`
- **Image:** `docker.io/penrithbeacon/wcp-widget-github`

## Version
- **Widget:** 1.4.0
- **WCP:** 2.1.0
- **Docker tag:** `1.4.0-wcp2.1.0`

## Controls (HTML Templates)

| Template | Route | Purpose | Default Size |
|----------|-------|---------|--------------|
| widget.html | `/widget/` | Compact overview card | (compact) |
| repos.html | `/widget/repos` | Repository browser | 12×12 |
| settings.html | `/widget/settings` | PAT configuration | 12×12 |
| help.html | `/widget/help` | Setup guide | 12×12 |

## Components

| ID | Name | Role | Size |
|----|------|------|------|
| gh-repos | GitHub Repositories | widget | 12×12 |
| gh-settings | GitHub Settings | widget | 12×12 |
| gh-help | GitHub Help | widget | 12×12 |

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/wcp` | Container directory |
| GET | `/widget/wcp` | Widget manifest |
| GET | `/widget/index` | Widget index directory |
| GET | `/widget/` | Compact view |
| GET | `/widget/repos` | Repository browser |
| GET | `/widget/settings` | Settings page |
| GET | `/widget/help` | Help page |
| GET | `/widget/health` | Health check |
| GET | `/widget/icon.svg` | Widget icon |
| GET | `/widget/api/guids` | Component UUIDs |
| GET | `/widget/export.wcp` | WCP export package |
| GET | `/widget/api/config-status` | Check if PAT is configured |
| GET | `/widget/api/repos` | List repositories |
| POST | `/widget/configure` | Save PAT configuration |
| POST | `/widget/publish` | Publish SPA |
| DELETE | `/widget/publish` | Remove published SPA |
| GET | `/` | Serve published SPA |

## Features
- Browse all repositories for authenticated GitHub account
- Sorted by last push date
- Repository details (stars, forks, language, visibility)
- PAT-based authentication
- Per-orchestration credential storage
- Help/setup guide
- Publish to Web support

## Configuration
- GitHub Personal Access Token (via `POST /widget/configure`)
- Persisted per orchestration/application context in `/app/data/`

## Data Persistence
- Named volume: `gh-data:/app/data`
- Stores PAT credentials per context

## Dependencies
- Python: `flask`, `requests`
- External API: GitHub REST API (requires user's PAT)
