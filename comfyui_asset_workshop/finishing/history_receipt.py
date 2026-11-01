"""Publish history metadata after a successful export without changing the asset package."""
import hashlib
import json
from pathlib import Path

def publish(archive_path, export_id, user_directory):
    outbox = Path(user_directory) / "mumblebox-foundry" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(str(export_id).encode()).hexdigest()
    receipt = {"schema": "mumblebox.history-receipt/1", "producer": "asset-package/v2",
               "role": "finished_package", "export_id": str(export_id), "archive_path": str(archive_path)}
    temporary = outbox / (name + ".tmp")
    temporary.write_text(json.dumps(receipt), encoding="utf-8")
    temporary.replace(outbox / (name + ".json"))
