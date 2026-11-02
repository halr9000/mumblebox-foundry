"""Connect the existing Foundry MCP to this Pinokio installation's current port.

Keep this filename distinct from ``mcp`` so it cannot shadow the SDK package.
"""
import argparse
import json
from pathlib import Path
import runpy
import sys
from urllib.parse import urlsplit
from bootstrap import Layout

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--input-root',action='append',default=[])
    parser.add_argument('--input-file',action='append',default=[])
    args=parser.parse_args();layout=Layout(args.root)
    runtime=layout.state/'runtime.json'
    if not runtime.is_file():raise RuntimeError('Start Foundry in Pinokio before connecting its MCP.')
    url=json.loads(runtime.read_text())['comfy_url'];parsed=urlsplit(url)
    if parsed.scheme!='http' or parsed.hostname!='127.0.0.1' or parsed.username or parsed.password:
        raise ValueError('The installed Foundry endpoint must be local.')
    entry=layout.root/'comfyui_asset_workshop'/'agent'/'foundry_server.py'
    sys.argv=[str(entry),'--comfy-url',url,'--input-root',str(layout.data/'input')]
    for name in ('input_root','input_file'):
        for value in getattr(args,name):sys.argv+=['--'+name.replace('_','-'),value]
    sys.path.insert(0,str(entry.parent));runpy.run_path(str(entry),run_name='__main__')

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError) as error:print(str(error),file=sys.stderr);sys.exit(1)
