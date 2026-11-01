"""Bounded local image-weight inventory and confirmed, exact-file deletion.

No caller supplies a path. IDs resolve only within the current model inventory.
Linked/shared files and active model sessions are intentionally read-only.
"""
import hashlib
import os
from pathlib import Path
import secrets
import threading
import time


class ResourceInventory:
    CATEGORIES={"checkpoints":"image_model","diffusion_models":"image_model","loras":"lora"}
    EXTENSIONS={".safetensors",".gguf",".ckpt",".pt",".pth",".bin"}

    def __init__(self, root, busy):
        self.root=Path(root).resolve()
        self.busy=busy
        self.tokens={}
        self.lock=threading.RLock()

    def _reason(self, path):
        if not path.resolve().is_relative_to(self.root):return "Stored outside this model directory."
        for part in (path,*path.parents):
            if part==self.root:break
            if part.is_symlink() or getattr(part,"is_junction",lambda:False)():return "Linked file or directory; manage it at its original location."
        if path.stat().st_nlink>1:return "Shared file with multiple links; manage it at its original location."
        if self.busy():return "Unload models and finish active jobs or downloads before deleting."
        return ""

    @staticmethod
    def _fingerprint(path):
        stat=path.stat()
        return (stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)

    def _scan(self):
        items=[];seen=0;truncated=False
        for category,kind in self.CATEGORIES.items():
            folder=self.root/category
            if not folder.is_dir():continue
            for directory,dirs,files in os.walk(folder,followlinks=False):
                seen+=1
                dirs[:]=sorted(d for d in dirs if not (Path(directory)/d).is_symlink() and not getattr(Path(directory)/d,"is_junction",lambda:False)())
                if seen>2000 or len(items)>=1000:truncated=True;break
                for name in sorted(files):
                    path=Path(directory)/name
                    if path.suffix.lower() not in self.EXTENSIONS:continue
                    try:
                        relative=path.relative_to(self.root).as_posix()
                        reason=self._reason(path)
                        items.append({"id":hashlib.sha256(relative.encode()).hexdigest()[:24],"name":name,
                            "relative_path":relative,"kind":kind,"bytes":path.stat().st_size,
                            "deletable":not reason,"reason":reason})
                    except OSError:continue
                    if len(items)>=1000:truncated=True;break
            if truncated:break
        return {"items":items,"truncated":truncated}

    def list(self):
        with self.lock:return self._scan()

    def _target(self, ident):
        item=next((i for i in self._scan()["items"] if i["id"]==ident),None)
        if item is None:raise ValueError("This resource is no longer in the model inventory. Refresh the list.")
        if not item["deletable"]:raise ValueError(item["reason"])
        return self.root/item["relative_path"],item

    def preview(self, ident):
        with self.lock:
            path,item=self._target(ident)
            now=time.monotonic()
            self.tokens={k:v for k,v in self.tokens.items() if v["expires"]>now}
            if len(self.tokens)>=32:raise ValueError("Close older deletion requests and try again shortly.")
            token=secrets.token_urlsafe(24)
            self.tokens[token]={"id":ident,"fingerprint":self._fingerprint(path),"expires":now+300}
            return {"token":token,"name":item["name"],"relative_path":item["relative_path"],"bytes":item["bytes"]}

    def remove(self, token):
        with self.lock:
            receipt=self.tokens.pop(token,None)
            if not receipt or receipt["expires"]<time.monotonic():raise ValueError("This deletion confirmation expired. Refresh and select the resource again.")
            path,item=self._target(receipt["id"])
            if self._fingerprint(path)!=receipt["fingerprint"]:raise ValueError("The file changed after confirmation. Nothing was deleted; refresh the list.")
            path.unlink()
            return {"removed":True,"id":item["id"],"bytes":item["bytes"]}
