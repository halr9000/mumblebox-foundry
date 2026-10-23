"""Hugging Face download credentials, private to this Comfy installation."""

import hashlib
import json
import os
import re
import threading
from pathlib import Path

import folder_paths
import keyring
from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

SERVICE = "Mumblebox-Comfy-" + hashlib.sha256(
    os.path.normcase(str(Path(folder_paths.base_path).resolve())).encode()
).hexdigest()[:20]
ACCOUNT = "hugging-face"
LOCK = threading.RLock()
_loaded = False
_credential = {}
_storage_error = ""


def vault():
    backend = keyring.get_keyring()
    # Do not silently accept a third-party plaintext keyring on another machine.
    trusted = ("keyring.backends.Windows", "keyring.backends.macOS",
               "keyring.backends.SecretService", "keyring.backends.kwallet")
    if not type(backend).__module__.startswith(trusted):
        raise ValueError("Secure credential storage is unavailable. Enable or unlock your operating system's credential vault, then restart Comfy.")
    return backend


def load():
    global _loaded, _credential, _storage_error
    with LOCK:
        if _loaded:
            return
        try:
            saved = vault().get_password(SERVICE, ACCOUNT)
            _credential = json.loads(saved) if saved else {}
            if not isinstance(_credential, dict):
                raise ValueError()
            _loaded = True
            _storage_error = ""
        except Exception:
            _credential = {}
            _storage_error = "The operating system's credential vault could not be read. Unlock it or check that secure credential storage is available."


def token():
    load()
    with LOCK:
        return _credential.get("token")


def status():
    load()
    with LOCK:
        return {"connected": bool(_credential.get("token")),
                "account": _credential.get("account", ""),
                "storage": "Operating system credential vault",
                "error": _storage_error}


def identify(value):
    if not isinstance(value, str) or not re.fullmatch(r"hf_[A-Za-z0-9]{10,200}", value):
        raise ValueError("Paste a Hugging Face access token beginning with hf_. Your existing connection has not changed.")
    try:
        result = HfApi(endpoint="https://huggingface.co").whoami(token=value, cache=False)
    except HfHubHTTPError as error:
        if error.response is not None and error.response.status_code in (401, 403):
            raise ValueError("Hugging Face rejected this token. Check that it is active and has permission to read the models you want.") from None
        raise ValueError("Hugging Face could not verify the connection. Try again when the service is reachable.") from None
    except Exception:
        raise ValueError("Could not reach Hugging Face to verify the token. Check your connection and try again.") from None
    name = result.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("Hugging Face did not return an account name. The connection was not saved.")
    return name


def connect(value):
    global _loaded, _credential, _storage_error
    value = value.strip() if isinstance(value, str) else value
    name = identify(value)
    record = {"token": value, "account": name}
    with LOCK:
        try:
            vault().set_password(SERVICE, ACCOUNT, json.dumps(record))
        except Exception:
            raise ValueError("The token was verified but could not be saved securely. Unlock your operating system's credential vault and try again.") from None
        _credential = record
        _loaded = True
        _storage_error = ""
        return status()


def test_connection():
    value = token()
    if not value:
        raise ValueError("Connect your Hugging Face account first.")
    identify(value)
    return status()


def disconnect():
    global _loaded, _credential, _storage_error
    with LOCK:
        try:
            backend = vault()
            if backend.get_password(SERVICE, ACCOUNT):
                backend.delete_password(SERVICE, ACCOUNT)
        except Exception:
            raise ValueError("The saved connection could not be removed from the credential vault. Unlock it and try again.") from None
        _credential = {}
        _loaded = True
        _storage_error = ""
        return status()
