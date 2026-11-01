"""Disposable finishing files, explicitly registered inside one owned job.

Masters, export folders, inputs and the reusable quad geometry cache are never
registered. Failed jobs retain their diagnostics; publication calls cleanup.
"""
import json
import shutil
from pathlib import Path

def checked(job, relative):
    job=Path(job).absolute()
    if not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Scratch path must be inside its job')
    target=job/relative
    for parent in (target,*target.parents):
        if parent.is_symlink() or (hasattr(parent,'is_junction') and parent.is_junction()):
            raise ValueError('Linked scratch paths are not disposable')
    root=job.resolve();target=target.resolve()
    if target==root or not target.is_relative_to(root):raise ValueError('Scratch path escapes its job')
    if target.is_dir():
        for item in target.rglob('*'):
            if item.is_symlink() or (hasattr(item,'is_junction') and item.is_junction()) or not item.resolve().is_relative_to(root):
                raise ValueError('Linked content inside scratch directory')
    return target

def register(job, paths, purpose):
    job=Path(job)
    for path in paths:checked(job,path)
    record={'schema':'mumblebox.owned-scratch/1','root':str(job.resolve()),'purpose':purpose,'paths':list(paths)}
    (job/'scratch.json').write_text(json.dumps(record,indent=2),encoding='utf-8')

def cleanup(job):
    job=Path(job)
    record=json.loads((job/'scratch.json').read_text(encoding='utf-8'))
    if record.get('schema')!='mumblebox.owned-scratch/1' or record.get('root')!=str(job.resolve()):
        raise ValueError('Scratch ownership does not match this job')
    targets=[checked(job,p) for p in record['paths']]
    result={'status':'complete','removed':[],'failures':[]}
    for target in targets:
        try:
            if target.is_dir():shutil.rmtree(target)
            elif target.exists():target.unlink()
            result['removed'].append(target.relative_to(job.resolve()).as_posix())
        except OSError as error:result['failures'].append({'path':target.name,'error':str(error)})
    if result['failures']:result['status']='partial'
    (job/'cleanup.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result