import copy
import json
import importlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_reference_pair import recipes, store


class ImportedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = store.AssetStore(self.temp.name)
        self.project = self.library.create_project()
        self.project.update(profile='sdxl_base', prompt='One toy camera')
        self.library.save(self.project)

    def test_imported_sdxl_checkpoint_reaches_native_loader(self):
        self.project['settings']['image_checkpoint'] = '123'
        selected = {'relative_path': 'Mumblebox/sdxl/example.safetensors', 'sha256': 'a'*64,
                    'source_url': 'https://civitai.com/models/1', 'file_id': 123, 'model_name': 'Example'}
        with patch.object(recipes, 'selected_image_model', return_value=selected):
            result = recipes.image_task_recipe(self.project, copy.deepcopy(self.project), 'create_image', 'design', 'test')
            loaders = [n for n in result['graph'].values() if n['class_type'] == 'AW_LoadSDXLCheckpoint']
            self.assertEqual(loaders[0]['inputs']['checkpoint_name'], selected['relative_path'])
            self.assertNotIn('sdxl_base', recipes.required_models(self.project, 'image'))
            self.assertEqual(result['details']['checkpoint']['file_id'], 123)
            saved = next(n for n in result['graph'].values() if n['class_type']=='AW_SaveImage')
            self.assertEqual(json.loads(saved['inputs']['recipe'])['checkpoint']['file_id'], 123)
            exporter = importlib.import_module('_aw_pair_contract.package_export')
            self.assertEqual(exporter.recipe_parameters(result['details'])['checkpoint']['file_id'], 123)

    def test_selection_is_saved_and_profile_change_clears_it(self):
        record = self.library.update_project(self.project['id'], self.project['revision'], {'settings': {'image_checkpoint': '123'}})
        self.assertEqual(record['settings']['image_checkpoint'], '123')
        record = self.library.update_project(record['id'], record['revision'], {'profile': 'klein4'})
        self.assertEqual(record['settings']['image_checkpoint'], '')

    def test_imported_modern_model_uses_native_platform_path(self):
        self.project['profile'] = 'klein4'
        selected = {'relative_path': 'Mumblebox/klein4/example.safetensors', 'file_id': 123}
        with patch.object(recipes, 'selected_image_model', return_value=selected):
            result = recipes.image_task_recipe(self.project, copy.deepcopy(self.project), 'create_image', 'design', 'test')
        loader = next(n for n in result['graph'].values() if n['class_type']=='UNETLoader')
        self.assertEqual(loader['inputs']['unet_name'], str(Path(selected['relative_path'])))
        saved = next(n for n in result['graph'].values() if n['class_type']=='AW_SaveImage')
        self.assertEqual(json.loads(saved['inputs']['recipe'])['checkpoint']['file_id'], 123)

    def test_nested_lora_uses_native_platform_path(self):
        name = 'Mumblebox/sdxl/example.safetensors'
        self.project['loras']=[{'name':name,'profile':'sdxl_base','enabled':True,'strength':1,'strength_clip':1}]
        with patch.object(recipes, 'local_lora', return_value='fixture'), patch.object(recipes, 'lora_provenance', return_value={'sha256':'a'*64}):
            result = recipes.image_task_recipe(self.project, copy.deepcopy(self.project), 'create_image', 'design', 'test')
        loader = next(n for n in result['graph'].values() if n['class_type']=='AW_LoadSDXLLoRA')
        self.assertEqual(loader['inputs']['lora_name'], str(Path(name)))


if __name__ == '__main__': unittest.main()
