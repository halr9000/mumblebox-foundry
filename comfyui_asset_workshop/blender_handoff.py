"""Open a recorded mesh in a visible Blender window without shell interpolation."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import json
import tempfile
import time
import uuid


def find_blender():
    configured = os.environ.get('MUMBLEBOX_BLENDER')
    if configured:
        path = Path(configured).expanduser()
        if path.is_file():
            return path.resolve()
        raise ValueError('The Blender location in MUMBLEBOX_BLENDER does not exist.')
    on_path = shutil.which('blender')
    if on_path:
        return Path(on_path).resolve()
    candidates = []
    if sys.platform == 'win32':
        for location in ('ProgramW6432', 'ProgramFiles', 'ProgramFiles(x86)'):
            if os.environ.get(location):
                candidates.extend((Path(os.environ[location]) / 'Blender Foundation').glob('Blender */blender.exe'))
    elif sys.platform == 'darwin':
        candidates = [Path('/Applications/Blender.app/Contents/MacOS/Blender')]
    candidates = sorted({p.resolve() for p in candidates if p.is_file()},
                        key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]
    raise ValueError('Blender was not found. Install Blender, or set MUMBLEBOX_BLENDER to its executable, then retry.')


def open_mesh(path):
    path = Path(path).resolve()
    if path.suffix.lower() != '.glb' or not path.is_file():
        raise ValueError('Choose an existing exported GLB mesh.')
    executable = find_blender()
    script = Path(__file__).with_name('blender_open_asset.py')
    # A new, visible scene keeps existing Blender documents and unsaved work intact.
    receipt = Path(tempfile.gettempdir()) / ('mumblebox-blender-' + uuid.uuid4().hex + '.json')
    process = subprocess.Popen([str(executable), '--factory-startup', '--python', str(script), '--', str(path), str(receipt)],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               cwd=str(path.parent), start_new_session=True)
    for _ in range(90):
        if receipt.is_file():
            try:
                result = json.loads(receipt.read_text(encoding='utf-8'))
            except (ValueError, OSError):
                time.sleep(.5)
                continue
            receipt.unlink(missing_ok=True)
            if result.get('error'):
                raise ValueError('Blender could not import the mesh: ' + result['error'])
            return {'status': 'opened', 'pid': process.pid, **result}
        if process.poll() is not None:
            raise ValueError('Blender closed before importing the mesh. Try opening the downloaded GLB in Blender.')
        time.sleep(.5)
    return {'status': 'opening', 'pid': process.pid}
