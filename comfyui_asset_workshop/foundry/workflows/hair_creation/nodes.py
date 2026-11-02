"""Durable HairDeck boundary nodes. Upstream owns inference, materials and VRM export."""
import copy
import json
import re
import uuid
from pathlib import Path
import numpy as np
import torch
from PIL import Image
import folder_paths
from ...artifacts import owned_path, digest
from .integration import upstream, models_root
from .definition import validate


def output_path(relative):
    root = Path(folder_paths.get_output_directory()).resolve()
    return owned_path(root/'foundry-hair', root/relative)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def checkpoint_result(result, directory):
    directory.mkdir(parents=True, exist_ok=False)
    from hairdeck_core.cards.mesh import cards_to_json
    arrays = dict(tokens=result.hair.tokens)
    for name in ('crop', 'hair_mask', 'face_mask', 'preview'):
        arrays[name] = getattr(result, name).detach().cpu().numpy()
    np.savez_compressed(directory/'data.npz', **arrays)
    data = dict(schema='foundry-hair-checkpoint/1', cards=cards_to_json(result.hair.cards), color=result.hair.color,
                signature=result.hair.signature, model_signature=result.hair.model_signature,
                chains=result.rig.chains if result.rig else None, seed=result.seed, steps=result.steps, cfg=result.cfg,
                seconds=result.seconds, preprocess_cache_hit=result.preprocess_cache_hit, data_sha256=digest(directory/'data.npz'))
    write_json(directory/'checkpoint.json', data)
    return directory/'checkpoint.json'


def restore(relative):
    native=upstream(); path=output_path(relative)
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema')!='foundry-hair-checkpoint/1' or digest(path.parent/'data.npz')!=data['data_sha256']:
        raise ValueError('The saved hair checkpoint changed; regenerate this variation.')
    cards=[(np.asarray(c['seq'], dtype=np.float64), ('square','triangle').index(c['shape'])) for c in data['cards']]
    with np.load(path.parent/'data.npz', allow_pickle=False) as values:
        hair=native.runtime.HairData(models_root(), data['model_signature'], data['signature'], data['seed'], cards,
                                    values['tokens'].copy(), data['color'])
        rig=native.runtime.RigData(hair.signature, data['chains']) if data['chains'] is not None else None
        tensors=[torch.from_numpy(values[key].copy()) for key in ('crop','hair_mask','face_mask','preview')]
    return native.generation.GenerationResult(hair,rig,*tensors,data['seed'],data['steps'],data['cfg'],data['preprocess_cache_hit'],data['seconds'])


def fitted(result, scale, offset):
    result=copy.deepcopy(result)
    for seq, _ in result.hair.cards:
        seq[:,:3]=seq[:,:3]*scale+np.asarray(offset)
        seq[:,3:5]*=scale
    if result.rig:
        for chain in result.rig.chains:
            for key in ('path','joints'): chain[key]=(np.asarray(chain[key])*scale+np.asarray(offset)).tolist()
    return result


def export_result(result, prefix, config):
    native=upstream()
    formats='GLB + VRM + 动画' if config['motion'] else ('GLB + VRM' if config['vrm'] else 'GLB')
    # Motion alone still uses the validated VRM path; the package selector owns
    # which files are delivered. Static GLB remains the review artifact.
    if config['motion']: formats='GLB + VRM + 动画'
    return native.output.save(None, fitted(result,config['scale'],config['offset']), formats,prefix,
        config['color'],config['show_head'],False,True,'',config['head_profile'],
        {'shared':'共享图集','unique':'独立展开'}[config['uv_mode']],config['texture_size'],
        {'volume':'体积发束','ribbon':'透明发片','solid':'纯色诊断','checker':'UV 检查'}[config['material']])


def summary(saved, checkpoint):
    root=Path(folder_paths.get_output_directory()).resolve()
    info=json.loads((saved.directory/'result.json').read_text(encoding='utf-8'))
    rig={}
    for path in saved.directory.glob('*.check.json'):
        raw=json.loads(path.read_text(encoding='utf-8'))
        rig={key:raw[key] for key in ('ok','problems','n_cards','n_chains_in','n_chains','n_spring_groups','hair_verts') if key in raw}
        if not rig.get('ok') or not rig.get('n_spring_groups',0):raise ValueError('No validated bound spring groups were exported. Keep the generation and revise the head/seed.')
    return {'checkpoint':str(checkpoint.relative_to(root)).replace('\\','/'),
            'directory':saved.directory.relative_to(root).as_posix(), 'files':info['files'], 'measurements':{
            'hair_cards':info['hair_cards'],'generated_chains':info['generated_chains'],
            'generation_seconds':info['generation_seconds'],'seed':info['seed'], 'steps':info['steps'], 'cfg':info['cfg'],
            'rig':rig,'geometry':info['geometry']},'model':saved.model.relative_to(root).as_posix()}


def clean_new_scratch(before):
    # Delete exact new helper files only. Never touch another workflow's files,
    # preprocess cache, weights, checkpoints or rendered outputs.
    base=Path(folder_paths.get_temp_directory()).resolve()/'hairdeck'
    for directory in list(base.iterdir()) if base.exists() else []:
        if directory.name in before or not directory.is_dir() or directory.is_symlink():continue
        if not directory.name.startswith(('export_','surface_')):continue
        files=list(directory.rglob('*'))
        if any(p.is_symlink() for p in files):continue
        for path in sorted(files,key=lambda p:len(p.parts),reverse=True):
            if path.is_file():path.unlink()
            elif path.is_dir():path.rmdir()
        directory.rmdir()


class FoundryHairCheckpoint:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{'result':('HAIRDECK_RESULT',),'creation_id':('STRING',),'variant':('INT',{'default':0,'min':0,'max':3})}}
    RETURN_TYPES=('STRING',); FUNCTION='save'; CATEGORY='Mumblebox Foundry/Hair'; OUTPUT_NODE=True

    def save(self,result,creation_id,variant):
        if not re.fullmatch('[0-9a-f]{32}',creation_id) or not 0<=variant<=3:raise ValueError('Invalid hair generation identity.')
        root=Path(folder_paths.get_output_directory()).resolve()
        directory=output_path(f'foundry-hair/{creation_id}/variant-{variant}-{uuid.uuid4().hex[:8]}')
        checkpoint=checkpoint_result(result,directory)
        before={p.name for p in (Path(folder_paths.get_temp_directory())/'hairdeck').glob('*')}
        try:
            config={**__import__(__package__+'.definition',fromlist=['DEFAULTS']).DEFAULTS,'bones':result.rig is not None,'vrm':False,'motion':False}
            saved=export_result(result,directory.relative_to(root).as_posix()+'/review',config)
            # A separate diagnostic overlay never replaces the clean hair GLB.
            if result.rig:
                native=upstream()
                native.output.exporting.save_glb(result.hair,result.rig,True,'auto',directory.relative_to(root).as_posix()+'/bones')
            details=summary(saved,checkpoint)
            bones=next(directory.glob('bones*.glb'),None)
            if bones:details['bone_model']=bones.relative_to(root).as_posix()
            return {'ui':{**saved.ui,'foundry_hair':[details]},'result':(details['checkpoint'],)}
        finally:clean_new_scratch(before)


class FoundryHairExport:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{'checkpoint':('STRING',),'options':('STRING',)}}
    RETURN_TYPES=('STRING',);FUNCTION='save';CATEGORY='Mumblebox Foundry/Hair';OUTPUT_NODE=True
    @classmethod
    def IS_CHANGED(cls,**kwargs):return float('nan')

    def save(self,checkpoint,options):
        config=validate(json.loads(options));result=restore(checkpoint)
        if config['bones'] and result.rig is None:raise ValueError('Regenerate with spring bones before requesting rigged output.')
        before={p.name for p in (Path(folder_paths.get_temp_directory())/'hairdeck').glob('*')}
        try:
            saved=export_result(result,output_path(checkpoint).parent.relative_to(Path(folder_paths.get_output_directory())).as_posix()+'/export',config)
            details=summary(saved,output_path(checkpoint))
            return {'ui':{**saved.ui,'foundry_hair':[details]},'result':(details['directory'],)}
        finally:clean_new_scratch(before)


NODE_CLASS_MAPPINGS={cls.__name__:cls for cls in (FoundryHairCheckpoint,FoundryHairExport)}
