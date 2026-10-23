"""Build production recipes for schema validation only. Never submits a prompt."""
import argparse
import copy
import importlib
import io
import json
from pathlib import Path
import sys
import types
import urllib.request

from PIL import Image


def read(path):
    with urllib.request.urlopen('http://127.0.0.1:8188'+path, timeout=30) as response:
        return json.load(response)


def build(project_id, destination):
    source = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(source.parents[1]))
    package = types.ModuleType('_mumblebox_native_graphs')
    package.__path__ = [str(source)]
    sys.modules[package.__name__] = package
    runtime = types.ModuleType(package.__name__+'.runtime')
    sys.modules[runtime.__name__] = runtime
    runtime.configuration = lambda: {'root': read('/asset-workshop/status')['root']}
    store = importlib.import_module(package.__name__+'.store')
    library = store.AssetStore(runtime.configuration()['root'])
    runtime.store = lambda: library
    recipes = importlib.import_module(package.__name__+'.recipes')
    edits = importlib.import_module(package.__name__+'.image_edits')
    profiles = importlib.import_module(package.__name__+'.profiles')
    project = library.load(project_id)
    assert project['name'] == 'Control fixture — no generation', 'Use an explicitly named, disposable control fixture.'
    primary = library.mesh_input(project_id)
    mask = io.BytesIO()
    with Image.open(library.path(project_id, primary['file'])) as original:
        Image.new('L', original.size, 255).save(mask, format='PNG')
    edit = edits.create(library,project_id,'mesh_input',primary['id'],'Change only the selected color',mask.getvalue())
    result = {'purpose':'schema validation only; no inference', 'project_id':project_id, 'graphs':{}}
    required = set()
    for profile in profiles.PROFILES:
        for task, role in [('create_image','design'),('three_quarter','mesh_input'),('edit_image','mesh_input'),
                           *[('reference_view','reference_'+side) for side in ('front','back','left','right')]]:
            snapshot = copy.deepcopy(project)
            snapshot['profile'] = profile
            snapshot['settings']['seed'] = 42
            snapshot['task_payload'] = {'edit':edit} if task=='edit_image' else {}
            built = recipes.image_task_recipe(project,snapshot,task,role,'schema-check')
            result['graphs'][profile+'/'+task+'/'+role] = built['graph']
            required.update(recipes.required_models(snapshot,'image'))
    for label, prepare in [('prepare',True),('mesh',False)]:
        graph,details,bindings = recipes.mesh_recipe(project,{'id':'schema-check'},prepare_only=prepare)
        result['graphs'][label] = graph.nodes
        required.update(recipes.required_models(project,'prepare' if prepare else 'mesh'))
    raw = {'id':'schema-master','kind':'master','stale':False}
    result['graphs']['finish'] = recipes.finish_saved_master_recipe(project,raw,'schema-check')['graph']
    snapshot = copy.deepcopy(project)
    snapshot['task_payload'] = {'export_kind':'game'}
    snapshot['artifacts'].append({'id':'schema-finished','kind':'mesh','export_kind':'master','master':'schema-master','stale':False})
    result['graphs']['game'] = recipes.finish_saved_master_recipe(snapshot,raw,'schema-check')['graph']
    result['models'] = {}
    for key in sorted(required):
        model = recipes.MODELS[key]
        path = source.parents[1] / 'models' / model['category'] / model['name']
        result['models'][key] = {'name':model['name'], 'exists_in_this_installation':path.is_file(),
            'size_matches':path.is_file() and path.stat().st_size==model['size'], 'expected_sha256':model['sha256']}
    Path(destination).write_text(json.dumps(result), encoding='utf-8')
    print(json.dumps({'graphs':len(result['graphs']),'models':len(result['models']),
        'missing_or_wrong_size':[key for key,value in result['models'].items() if not value['size_matches']], 'inference_calls':0}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--project-id',required=True)
    parser.add_argument('--output',required=True)
    options=parser.parse_args()
    build(options.project_id,options.output)
