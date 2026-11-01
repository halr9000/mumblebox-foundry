"""Explicit, bounded ingestion of durable successful-export notifications."""
import itertools
import json
import zipfile
from pathlib import Path

def sync(library):
    outbox = library.root / "outbox"
    if not outbox.is_dir(): return {"imported": 0, "failed": 0, "more": False,"previews":link_front_previews(library)}
    paths = list(itertools.islice(outbox.glob("*.json"), 33))
    imported, failed = 0, 0
    for path in paths[:32]:
        try:
            if path.stat().st_size > 16384: raise ValueError("Receipt is too large.")
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if receipt.get("schema") != "mumblebox.history-receipt/1":
                raise ValueError("Unsupported receipt schema.")
            if receipt.get("producer") == "asset-package/v2" and receipt.get("role") == "finished_package":
                library.import_package(receipt["archive_path"])
            else:
                raise ValueError("Only completed asset packages are published by the current workflow.")
            path.replace(path.with_suffix(".processed"))
            imported += 1
        except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile):
            failed += 1
            try: path.replace(path.with_suffix(".failed"))
            except OSError: pass
    return {"imported": imported, "failed": failed, "more": len(paths) > 32,"previews":link_front_previews(library)}


def link_front_previews(library):
    """Explicit sync backfills known completed runs, without rerunning or rewriting ZIPs."""
    linked=0
    checked=getattr(library,"_preview_sync",{})
    current={}
    for path in itertools.islice((library.root/"wizard-runs").glob("*.json"),128):
        try:
            stat=path.stat()
            fingerprint=(stat.st_size,stat.st_mtime_ns)
            current[str(path)]=fingerprint
            if checked.get(str(path))==fingerprint or stat.st_size>8*1024**2:continue
            run=json.loads(path.read_text(encoding="utf-8"))
            package=run.get("package")
            front=run.get("outputs",{}).get("340",{}).get("images",[])
            if not package or not front or front[0].get("type")!="output":continue
            record=library.import_package(package["archive_path"])
            if record.get("preview_id"):continue
            item=front[0]
            library.attach_front(record["id"],library.output_root/item.get("subfolder","")/item["filename"])
            linked+=1
        except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile):continue
    library._preview_sync=current
    return linked
