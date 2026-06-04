"""
WCP Widget: GitHub
Three components: Repositories, Settings, Help — each 12×6, full-stave default.
Port: 3743  |  GitHub API: https://api.github.com
Specification: https://widgetcontextprotocol.com
"""

import io
import json
import os
import time
import zipfile
import requests
from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

# ── CORS ──────────────────────────────────────────────────────────────────────

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = (
        'Content-Type, Wcp-Instance-Id, Wcp-Dashboard-Id, Wcp-Version, Wcp-Widget-Id, '
        'Wcp-Orchestration-Id, Wcp-Application-Id'
    )
    return response

@app.route('/widget/<path:p>', methods=['OPTIONS'])
@app.route('/widget/', methods=['OPTIONS'])
@app.route('/wcp', methods=['OPTIONS'])
def cors_preflight(p=''):
    return Response('', status=204)

DATA_DIR = "/app/data"
GLOBAL_CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
GH_BASE = "https://api.github.com"
REPOS_TTL = 60

# ── Instance ID helpers (WCP 1.5.0) ──────────────────────────────────────────

def get_instance_id():
    iid = request.headers.get("Wcp-Instance-Id", "").strip()
    if not iid:
        iid = (request.args.get("wcpInstanceId", "") or "").strip()
    return iid

def get_orchestration_id():
    oid = request.headers.get("Wcp-Orchestration-Id", "").strip()
    if not oid:
        oid = (request.args.get("wcpOrchestrationId", "") or "").strip()
    return oid

def get_application_id():
    aid = request.headers.get("Wcp-Application-Id", "").strip()
    if not aid:
        aid = (request.args.get("wcpApplicationId", "") or "").strip()
    return aid

def get_state_key():
    """WCP 1.5.0 compound state key. See widgetcontextprotocol.com — WCP Request Headers."""
    orch_id = get_orchestration_id()
    app_id  = get_application_id()
    if orch_id and app_id: return f"{orch_id}:{app_id}"
    if orch_id:            return orch_id
    return "global"

def _safe_iid(iid):
    return "".join(c for c in iid if c.isalnum() or c == "-")[:64]

def config_file_for(iid):
    iid = _safe_iid(iid)
    if not iid:
        return GLOBAL_CONFIG_FILE
    return os.path.join(DATA_DIR, f"config-{iid}.json")

# ── Config helpers ────────────────────────────────────────────────────────────

def read_config(iid=None):
    if iid is None:
        iid = get_instance_id()
    path = config_file_for(iid)
    instance_cfg = None
    try:
        with open(path) as f:
            instance_cfg = json.load(f)
    except Exception:
        pass
    # Fall back to global config if per-instance config has no token
    # (covers both missing file and empty {} created by Add Widget flow)
    if (instance_cfg is None or not instance_cfg.get("githubToken")) and path != GLOBAL_CONFIG_FILE:
        try:
            with open(GLOBAL_CONFIG_FILE) as f:
                global_cfg = json.load(f)
            return {**(instance_cfg or {}), **global_cfg}
        except Exception:
            pass
    return instance_cfg or {}

def write_config(data, iid=None):
    if iid is None:
        iid = get_instance_id()
    os.makedirs(DATA_DIR, exist_ok=True)
    path = config_file_for(iid)
    current = {}
    try:
        with open(path) as f:
            current = json.load(f)
    except Exception:
        pass
    current.update({k: v for k, v in data.items() if v is not None})
    with open(path, "w") as f:
        json.dump(current, f, indent=2)
    return current

def mask_token(token):
    if not token or len(token) < 4:
        return ""
    return "****" + token[-4:]

# ── Cache ─────────────────────────────────────────────────────────────────────

_cache = {}

def _cache_for(iid):
    if iid not in _cache:
        _cache[iid] = {"repos": {"data": None, "time": 0}}
    return _cache[iid]

def clear_cache(iid=None):
    if iid is None:
        _cache.clear()
    else:
        _cache.pop(iid, None)

# ── GitHub API helper ─────────────────────────────────────────────────────────

def gh_fetch(path, token):
    return requests.get(
        f"{GH_BASE}{path}",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=15,
    )

def gh_get_user(token):
    try:
        r = gh_fetch("/user", token)
        if r.status_code == 200:
            return r.json().get("login", "")
    except Exception:
        pass
    return ""

# ── WCP Manifest ──────────────────────────────────────────────────────────────

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <path fill="#e6edf3" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
    0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52
    -.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2
    -3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64
    -.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12
    .51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93
    -.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
</svg>"""

WCP_MANIFEST = {
    "wcp": "2.0.0",
    "uuid": "47b58468-2ad8-4cbd-a7f3-58ad8fcf213c",
    "name": "GitHub",
    "version": "1.1.0",
    "description": (
        "GitHub repositories — browse all repos for the authenticated account, "
        "sorted by last push. Manage credentials via the Settings component."
    ),
    "icon": "/widget/icon.svg",
    "health": "/widget/health",
    "container": {
        "image":            "docker.io/penrithbeacon/wcp-widget-github",
        "source":           {"type": "registry"},
        "tag":              "1.1.0-wcp2.0.0",
        "port":             3743,
        "volumes":          [{"name": "gh-data", "mountPath": "/app/data"}],
        "defaultLifecycle": "always",
    },
    "configuration": {
        "submitEndpoint": "/widget/configure",
        "fields": [
            {
                "id": "githubToken",
                "type": "password",
                "sensitive": True,
                "label": "GitHub Personal Access Token",
                "placeholder": "ghp_… token with repo scope",
            },
        ],
    },
    "pages": [
        {"id": "repos",    "path": "/widget/repos",    "title": "GitHub Repositories"},
        {"id": "settings", "path": "/widget/settings", "title": "GitHub Settings"},
        {"id": "help",     "path": "/widget/help",     "title": "GitHub Help"},
    ],
    "components": [
        {
            "id": "gh-repos",
            "uuid": "71fb6300-f563-44bd-9d74-214c3991c8b7",
            "name": "GitHub Repositories",
            "role": "widget",
            "path": "/widget/repos",
            "icon": "/widget/icon.svg",
            "renderMode": "iframe",
            "defaultSize": {"w": 12, "h": 6},
        },
        {
            "id": "gh-settings",
            "uuid": "e9bdc801-526b-4994-971a-decbef6fb46d",
            "name": "GitHub Settings",
            "role": "widget",
            "path": "/widget/settings",
            "icon": "/widget/icon.svg",
            "renderMode": "iframe",
            "defaultSize": {"w": 12, "h": 6},
        },
        {
            "id": "gh-help",
            "uuid": "0b0eb22d-9a1e-4ad4-8998-d4f49e4d6160",
            "name": "GitHub Help",
            "role": "widget",
            "path": "/widget/help",
            "icon": "/widget/icon.svg",
            "renderMode": "iframe",
            "defaultSize": {"w": 12, "h": 6},
        },
    ],
}

# ── WCP boilerplate endpoints ─────────────────────────────────────────────────

@app.route("/wcp")
def container_directory():
    return jsonify({
        "type":    "directory",
        "wcp":     "2.0.0",
        "widgets": [{
            "id":          "github",
            "uuid":        WCP_MANIFEST["uuid"],
            "name":        WCP_MANIFEST["name"],
            "description": WCP_MANIFEST["description"],
            "icon":        WCP_MANIFEST["icon"],
            "manifest":    "/widget/wcp",
        }]
    })

@app.route("/widget/")
@app.route("/widget/index.html")
def widget_root():
    return render_template("widget.html", manifest=WCP_MANIFEST, wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route("/widget/wcp")
def widget_wcp():
    return jsonify(WCP_MANIFEST)

@app.route("/widget/health")
def widget_health():
    return jsonify({"status": "ok", "name": WCP_MANIFEST["name"]})

@app.route("/widget/icon.svg")
def widget_icon():
    return Response(ICON_SVG, mimetype="image/svg+xml")

@app.route("/widget/api/guids")
def api_guids():
    return jsonify({
        "uuid": WCP_MANIFEST["uuid"],
        "components": [
            {"id": c["id"], "uuid": c["uuid"], "name": c["name"]}
            for c in WCP_MANIFEST.get("components", [])
        ]
    })

@app.route("/widget/export.wcp")
def export_wcp():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(WCP_MANIFEST, indent=2))
        z.writestr("icon.svg", ICON_SVG)
        z.writestr("DOCKER.md", f"""# {WCP_MANIFEST['name']} — WCP Container

## Pull
```
docker pull penrithbeacon/wcp-widget-github
```

## Run
```
docker compose up -d
```

Port: 3743 | Spec: https://widgetcontextprotocol.com
""")
    buf.seek(0)
    resp = Response(buf.read(), mimetype="application/zip")
    resp.headers["Content-Disposition"] = 'attachment; filename="github.wcp"'
    return resp

# ── Component pages ───────────────────────────────────────────────────────────

@app.route("/widget/repos")
def page_repos():
    return render_template("repos.html", manifest=WCP_MANIFEST, wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route("/widget/settings")
def page_settings():
    return render_template("settings.html", manifest=WCP_MANIFEST, wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route("/widget/help")
def page_help():
    return render_template("help.html", manifest=WCP_MANIFEST, wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

# ── Configuration ─────────────────────────────────────────────────────────────

@app.route("/widget/configure", methods=["POST"])
def widget_configure():
    try:
        iid = get_instance_id()
        data = request.get_json(force=True) or {}
        token = (data.get("githubToken") or "").strip() or None
        cfg_data = {"githubToken": token}
        cfg = write_config(cfg_data, iid=iid)
        # Mirror credentials to global config so all other staves find them
        if token:
            write_config(cfg_data, iid="")
        clear_cache(iid)
        clear_cache("")
        return jsonify({"success": True, "configured": bool(cfg.get("githubToken"))})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/widget/api/config-status")
def config_status():
    cfg = read_config()
    token = cfg.get("githubToken", "")
    github_user = gh_get_user(token) if token else ""
    return jsonify({
        "configured": bool(token),
        "githubTokenMasked": mask_token(token),
        "githubUser": github_user,
    })

# ── Data endpoints ────────────────────────────────────────────────────────────

def _not_configured_response():
    return jsonify({
        "success": False,
        "error": "GitHub not configured. Open the Settings component to add your Personal Access Token.",
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

@app.route("/widget/api/repos")
def api_repos():
    iid = get_instance_id()
    cache = _cache_for(iid)
    now = time.time()
    if cache["repos"]["data"] and now - cache["repos"]["time"] < REPOS_TTL:
        return jsonify(cache["repos"]["data"])

    cfg = read_config(iid)
    token = cfg.get("githubToken")
    if not token:
        return _not_configured_response()

    try:
        all_repos = []
        page = 1
        while True:
            r = gh_fetch(f"/user/repos?type=all&sort=pushed&per_page=100&page={page}", token)
            if r.status_code == 401:
                return jsonify({"success": False, "error": "Invalid or expired GitHub token. Update it in the Settings component."})
            if r.status_code == 403:
                return jsonify({"success": False, "error": "GitHub API rate limit exceeded or token lacks required scopes."})
            if not r.ok:
                return jsonify({"success": False, "error": f"GitHub API error: {r.status_code}"})
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            all_repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1

        repos = [
            {
                "name":        repo["name"],
                "full_name":   repo["full_name"],
                "html_url":    repo["html_url"],
                "description": repo.get("description") or "",
                "private":     repo["private"],
                "language":    repo.get("language") or "",
                "pushed_at":   repo["pushed_at"],
                "archived":    repo["archived"],
                "fork":        repo["fork"],
                "stars":       repo["stargazers_count"],
            }
            for repo in all_repos
        ]

        result = {
            "success": True,
            "data": {"repos": repos},
            "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        cache["repos"]["data"] = result
        cache["repos"]["time"] = now
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs("/app/data", exist_ok=True)
    app.run(host="0.0.0.0", port=3743, debug=False)
