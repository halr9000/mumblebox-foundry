"""Small worker-side model-residency sampler; uses existing model objects only."""
import atexit
import json
import os
from pathlib import Path
import threading
import time

def residency(pipeline):
    candidates=list(pipeline.models.values())+[getattr(pipeline,'image_cond_model',None)]
    devices=[]
    unknown=False
    for model in candidates:
        if model is None: continue
        try:
            module=model if hasattr(model,'parameters') else getattr(model,'model',None)
            parameter=next(module.parameters(),None) if module is not None else None
            if parameter is None: unknown=True
            else: devices.append(str(parameter.device).split(':')[0])
        except (AttributeError,RuntimeError): unknown=True
    if 'cuda' in devices: return {'state':'loaded','device':'CUDA + CPU offload' if 'cpu' in devices else 'CUDA'}
    if unknown or 'meta' in devices: return {'state':'unknown','device':'unknown'}
    if devices: return {'state':'offloaded','device':'CPU'}
    # Lazy model construction may temporarily leave the pipeline slots empty.
    # An active worker without observable parameters is unknown, not unloaded.
    return {'state':'unknown','device':'unknown'}

def monitor(pipeline, request_path):
    path=Path(request_path).with_name('model-residency.json')
    stopped=threading.Event()
    def sample():
        while not stopped.is_set():
            try:
                value={**residency(pipeline),'pid':os.getpid(),'time':time.time()}
                temporary=path.with_suffix('.tmp')
                temporary.write_text(json.dumps(value),encoding='utf-8')
                temporary.replace(path)
            except (OSError,RuntimeError): pass
            stopped.wait(.5)
    thread=threading.Thread(target=sample,name='foundry-model-residency',daemon=True)
    thread.start()
    atexit.register(stopped.set)
    return stopped
