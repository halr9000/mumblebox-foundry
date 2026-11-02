"""Read-only GitHub release checks. Never downloads or installs executable code."""
import json
import threading
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from packaging.version import Version, InvalidVersion
from . import VERSION

REPOSITORY = "https://github.com/mumblebox-gpt/mumblebox-foundry"
RELEASES_API = "https://api.github.com/repos/mumblebox-gpt/mumblebox-foundry/releases?per_page=20"
AUTOMATIC_INTERVAL = 5 * 60
MAX_RESPONSE = 1024 * 1024


def fetch_releases(headers):
    """Public metadata only: no token, references, paths or hardware information."""
    request = Request(RELEASES_API, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "Mumblebox-Foundry/" + VERSION,
        "X-GitHub-Api-Version": "2022-11-28", **headers})
    try:
        with urlopen(request, timeout=8) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError("Release response exceeds the size limit")
            return response.status, json.loads(raw), dict(response.headers)
    except HTTPError as error:
        return error.code, None, dict(error.headers)


def trusted_link(value, section):
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        return ""
    url = urlsplit(value)
    prefix = "/mumblebox-gpt/mumblebox-foundry/releases/" + section + "/"
    if url.scheme == "https" and url.netloc == "github.com" and url.path.startswith(prefix):
        return value
    return ""


def select_release(releases, current):
    candidates = []
    for release in releases[:20]:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        tag = str(release.get("tag_name", ""))
        try:
            version = Version(tag)
        except InvalidVersion:
            continue
        if not current.is_prerelease and (version.is_prerelease or release.get("prerelease")):
            continue
        release_url = trusted_link(release.get("html_url"), "tag")
        if not release_url:
            continue
        download = next((trusted_link(asset.get("browser_download_url"), "download")
                         for asset in release.get("assets", [])[:50]
                         if isinstance(asset, dict) and str(asset.get("name", "")).startswith("mumblebox-foundry-")
                         and str(asset.get("name", "")).endswith(".zip")
                         and trusted_link(asset.get("browser_download_url"), "download")), "")
        candidates.append((version, {"latest": tag.removeprefix("v"), "release_url": release_url,
                                    "download_url": download, "notes": str(release.get("body") or "")[:8000]}))
    return max(candidates, key=lambda item: item[0]) if candidates else None


class ReleaseUpdates:
    def __init__(self, path, preferences, *, current=VERSION, fetch=fetch_releases, clock=time.time):
        self.path = Path(path)
        self.preferences = preferences
        self.current = current
        self.fetch = fetch
        self.clock = clock
        self.lock = threading.Lock()

    def read(self):
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(saved, dict) and saved.get("current") == self.current:
                return saved
        except (OSError, ValueError):
            pass
        return {"current": self.current, "state": "unchecked", "checked_at": None,
                "message": "No update check has been made yet."}

    def status(self):
        return self.public(self.read())

    def public(self, saved):
        return {key: value for key, value in saved.items() if key not in ("etag", "retry_at", "releases")}

    def check(self, manual=False):
        with self.lock:
            saved = self.read()
            if not manual and not self.preferences.read()["auto_check_updates"]:
                return {**self.public(saved), "state": "disabled", "message": "Automatic update checks are off."}
            now = self.clock()
            checked_at = saved.get("checked_at")
            if now < saved.get("retry_at", 0) or (not manual and checked_at is not None and now - checked_at < AUTOMATIC_INTERVAL):
                return self.public(saved)
            result = {**saved, "current": self.current, "checked_at": now, "retry_at": 0}
            try:
                headers = {"If-None-Match": saved["etag"]} if saved.get("etag") else {}
                status, releases, response_headers = self.fetch(headers)
                response_headers = {key.lower(): value for key, value in response_headers.items()}
                if status == 304:
                    releases = saved.get("releases", [])
                elif status != 200:
                    delay = 300
                    try:
                        delay = max(60, float(response_headers.get("retry-after", 300)),
                                    float(response_headers.get("x-ratelimit-reset", 0)) - now)
                    except (ValueError, TypeError):
                        pass
                    result["retry_at"] = now + min(delay, AUTOMATIC_INTERVAL)
                    raise ValueError("GitHub did not provide release information")
                if not isinstance(releases, list):
                    raise ValueError("Invalid release response")
                current = Version(self.current)
                selected = select_release(releases, current)
                result.update(releases=releases[:20], etag=response_headers.get("etag", saved.get("etag", "")))
                for key in ("latest", "notes", "release_url", "download_url"):
                    result.pop(key, None)
                if selected:
                    version, details = selected
                    result.update(details)
                    result["state"] = "available" if version > current else "current"
                    result["message"] = ("Version " + details["latest"] + " is available." if version > current
                                         else "You are up to date with the published releases for this channel.")
                else:
                    result.update(state="no_release", message="No published release is available for this channel yet.")
            except (OSError, ValueError, TypeError):
                result.update(state="unavailable", message="Could not check GitHub. Check your connection and try again later.")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(result), encoding="utf-8")
            temporary.replace(self.path)
            return self.public(result)
