"""Derive explicitly named companion channels from actual material maps."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
def add_companions(req):
    root=Path(req["export_dir"]);report_path=Path(req["job"])/"package-report.json"
    report=json.loads(report_path.read_text(encoding="utf-8"))
    variants={v["id"]:v for v in report["variants"]}
    for file in list(report["files"]):
        if file["kind"]!="texture":continue
        pairs=[]
        pixels=np.asarray(Image.open(root/file["path"]).convert("RGB"))
        if file["role"]=="metallic-roughness":
            pairs=[("roughness",pixels[:,:,1],"Linear roughness data"),("metallic",pixels[:,:,2],"Linear metallic data")]
        if file["role"]=="normal-opengl":
            dx=pixels.copy();dx[:,:,1]=255-dx[:,:,1]
            pairs=[("normal-directx",dx,"Tangent-space normal, DirectX -Y; green inverted once; alternative to OpenGL map")]
        for role,data,meaning in pairs:
            rel=file["path"].replace(file["role"],role);path=root/rel
            Image.fromarray(data).save(path)
            record={"path":rel,"kind":"texture","variant_id":file["variant_id"],"description":meaning+".","format":"png","role":role,"depends_on":[],"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
            report["files"].append(record);v=variants[file["variant_id"]];v["file_paths"].append(rel)
            v["measurements"]["textures"].append({"path":rel,"dimensions":[pixels.shape[1],pixels.shape[0]],"interpretation":meaning})
    report_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
