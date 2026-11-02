"""Host-owned live worker registry. No directory scans, network calls or model imports."""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import threading
import time

_lock = threading.Lock()
_workers = {}

def update(key, name, state='unknown', **details):
    if state not in ('loaded','offloaded','empty','unknown'): state='unknown'
    with _lock: _workers[key] = {'name':name,'state':state,**details}

def remove(key):
    with _lock: _workers.pop(key, None)

def snapshot():
    with _lock: return copy.deepcopy(list(_workers.values()))

def owned_pid(reported, root):
    if reported==root:return True
    if not isinstance(reported,int) or reported<=0:return False
    # Windows venv python.exe can be a redirector. Its real interpreter remains
    # in the owned job tree; accept that child, never an arbitrary reported PID.
    import psutil
    try:return root in [p.pid for p in psutil.Process(reported).parents()[:16]]
    except (psutil.NoSuchProcess,psutil.AccessDenied):return False

@contextmanager
def tracked(key, name):
    update(key, name)
    try: yield
    finally: remove(key)

def read_worker(key, name, path, pid):
    """Only accept this live child's recent, bounded status; stale is unknown."""
    try:
        path=Path(path)
        if path.stat().st_size>8192: raise ValueError('Oversized worker status')
        value=json.loads(path.read_text(encoding='utf-8'))
        if not owned_pid(value.get('pid'),pid) or not 0<=time.time()-value['time']<5: raise ValueError('Stale worker status')
        state=value.get('state','unknown')
        update(key,name,state,device=value.get('device','unknown'))
    except (OSError,ValueError,KeyError,TypeError,AttributeError): update(key,name)

def host_residency(loaded):
    """Comfy retains model patchers even when their weights have been offloaded."""
    states=[]
    for item in loaded:
        try:
            size=item.model.loaded_size()
            device=str(item.model.load_device)
            states.append('loaded' if size>0 and not device.startswith('cpu') else 'offloaded')
        except (AttributeError,TypeError,RuntimeError): states.append('unknown')
    return [{'name':'ComfyUI','state':state,'count':states.count(state)} for state in ('loaded','offloaded','unknown') if state in states]
