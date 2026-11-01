"""Portable accepted-image package and its single human/agent-readable index."""
import hashlib
import html
import io
import json
import re
import zipfile
from PIL import Image
from .definition import profiles

def safe_text(value):return html.escape(str(value)).replace('|','\\|').replace('\n',' ')

def provenance(revision):
    source=revision['provenance']
    profile=source.get('profile')
    license_info=profiles.capabilities(profile)['license'] if profile in profiles.PROFILES else {'label':'Not recorded','url':None}
    def fields(item,keys):return {k:item[k] for k in keys if k in item}
    return {'profile':profile,'model_license':license_info,
        **fields(source,('seed','steps','cfg','task','requested_view','camera_verification')),
        'models':{key:fields(value,('name','repo','revision','sha256','license','license_url','url','source')) for key,value in source.get('models',{}).items()},
        'checkpoint':fields(source.get('checkpoint',{}),('model_name','version_name','source_url','sha256','permissions')),
        'loras':[fields(item,('name','profile','strength','strength_clip','sha256','civitai')) for item in source.get('loras',[])]}

def build(library,record):
    sides=('front','back') if record['config']['paired'] else ('single',)
    if any(side not in record['accepted'] for side in sides):raise ValueError('Finish the image set before downloading it.')
    members={};manifest={'schema':'foundry-image-package/1','name':record['config']['name'],'category':record['config']['category'],'images':[]}
    for side in sides:
        revision=library.revision(record,record['accepted'][side]);path=library.file(record,revision['id'])
        # Export pixels, not embedded local recipe paths or private prompt metadata.
        with Image.open(path) as original:
            output=io.BytesIO();original.convert('RGBA').save(output,format='PNG');data=output.getvalue()
        filename='Images/'+side+'.png';members[filename]=data
        manifest['images'].append({'file':filename,'side':side,'size':revision['size'],'bytes':len(data),
            'sha256':hashlib.sha256(data).hexdigest(),'revision':revision['id'],'provenance':provenance(revision)})
    lines=['# '+safe_text(record['config']['name'])+' — Image Package','',
        'This package contains the accepted images and recorded generation details listed below. Retained editing revisions remain in the local Gallery.','',
        '## Images/','',
        'Front and back reference images describe opposite sides of the same subject for asset development. Their consistency requires visual review.' if record['config']['paired'] else 'A standalone image for general creative use. No matching rear view or 3D asset is included.','',
        '| File | Contents |','| --- | --- |']
    lines += [f"| [{item['side']}.png]({item['file']}) | Accepted {item['side']} image. |" for item in manifest['images']]
    lines += ['','Recorded image statistics:']
    lines += [f"- {item['side']}.png: {item['size'][0]} × {item['size'][1]} pixels; {item['bytes']:,} bytes; PNG RGBA." for item in manifest['images']]
    lines += ['','## Metadata/','','Machine-readable file inventory, checksums and generation provenance. Prompts, reference uploads, local paths and model weights are not included.','',
        '- [creation.json](Metadata/creation.json): image roles, revisions, dimensions, hashes, model and LoRA records.','',
        '## Models and resource terms','']
    for item in manifest['images']:
        p=item['provenance'];license_info=p['model_license']
        lines.append('- '+item['side'].title()+': '+safe_text(p['profile'] or 'Model not recorded')+'. '+safe_text(license_info['label'])+
            (' — '+license_info['url'] if license_info.get('url') else ''))
        if p['checkpoint']:
            lines.append('  - Checkpoint: '+safe_text(p['checkpoint'].get('model_name','External checkpoint'))+'. Source: '+safe_text(p['checkpoint'].get('source_url','not recorded')))
        for lora in p['loras']:
            lines.append('  - LoRA: '+safe_text(lora.get('name','Unnamed'))+'. Source: '+safe_text(lora.get('civitai',{}).get('source_url','not recorded; check the original provider.')))
    lines += ['','Model and tool licenses are separate from rights in the generated images and supplied references. No asset license is inferred by this package.','',
        '## Mumblebox 3D Asset Foundry','','Image creation, editing and configurable 3D asset workflows.','',
        'Project: https://github.com/mumblebox-gpt/mumblebox-foundry','',
        'Foundry code is Apache-2.0 licensed. Third-party resources retain their own terms.','']
    members['README.md']='\n'.join(lines).encode('utf-8')
    manifest['files']=[
        {'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in members.items()]
    members['Metadata/creation.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
    slug=re.sub(r'[^a-zA-Z0-9_-]+','-',record['config']['name']).strip('-')[:64] or 'images'
    signature=hashlib.sha256(members['Metadata/creation.json']).hexdigest()[:16]
    target=library.directory(record['id'])/(slug+'-'+signature+'.zip');temporary=target.with_suffix('.partial')
    if target.exists():
        library.track_file(record,target)
        return target
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for name,data in members.items():archive.writestr(name,data)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() or set(archive.namelist())!=set(members):raise ValueError('The image package failed archive verification.')
            for name,data in members.items():
                if archive.read(name)!=data:raise ValueError('An image package member failed verification.')
        temporary.replace(target)
        library.track_file(record,target);return target
    finally:temporary.unlink(missing_ok=True)
