"""SDXL native wiring, source preservation, dependencies and saved controls."""
import copy
import importlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

from test_reference_pair import recipes, store, runtime, prompt_contracts

profiles = importlib.import_module('_aw_pair_contract.profiles')


class SDXLWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        paths = patch.object(recipes.folder_paths, 'base_path', self.directory.name, create=True)
        paths.start()
        self.addCleanup(paths.stop)
        self.library = store.AssetStore(self.directory.name)
        recipes.store = runtime.store = lambda: self.library
        self.project = self.library.create_project()
        self.project['profile'] = 'sdxl_base'
        self.project['prompt'] = 'A small teal toy camera, one large round lens, three-quarter view.'

    def image(self, role='source', name='source1'):
        path = self.library.path(self.project['id'], f'images/{name}.png')
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (384, 256), 'orange' if name == 'two' else 'teal').save(path)
        record = {'id': name, 'file': f'images/{name}.png', 'sha256': store.digest(path)}
        self.project = self.library.add_revision(self.project['id'], role, record)
        self.project.update(profile='sdxl_base', prompt='A small teal toy camera, one large round lens.')
        return record

    def recipe(self, task='create_image', role='design', settings=None):
        snapshot = copy.deepcopy(self.project)
        snapshot['settings'].update(settings or {})
        return recipes.image_task_recipe(self.project, snapshot, task, role, 'sdxl-attempt')

    def nodes(self, recipe, kind):
        return [n for n in recipe['graph'].values() if n['class_type'] == kind]

    def test_sdxl_profiles_have_checkpoint_specific_defaults_and_shared_lora_family(self):
        for name, steps, cfg in [('sdxl_base', 30, 7), ('sdxl_juggernaut', 35, 5)]:
            with self.subTest(profile=name):
                info = profiles.capabilities(name)
                self.assertEqual(info['lora']['architecture'], 'sdxl')
                self.assertEqual(info['defaults']['steps'], steps)
                self.assertEqual(info['defaults']['cfg'], cfg)
                self.assertIn('huggingface.co/', info['license']['url'])
        self.assertTrue(profiles.lora_compatible('sdxl_base', 'sdxl_juggernaut'))
        self.assertFalse(profiles.lora_compatible('klein4', 'sdxl_base'))

    def test_dependencies_include_adapter_only_when_the_task_uses_visual_references(self):
        self.assertEqual(recipes.required_models(self.project, 'image'), ['sdxl_base'])
        self.image()
        required = recipes.required_models(self.project, 'image')
        self.assertEqual(required, ['sdxl_base', 'sdxl_ipadapter', 'sdxl_vision'])
        self.project['sources'] = []
        self.assertEqual(recipes.required_models(self.project, 'image', action='three_quarter'),
                         ['sdxl_base', 'sdxl_ipadapter', 'sdxl_vision'])
        self.assertEqual(recipes.required_models(self.project, 'image', action='build_mesh_package'),
                         ['sdxl_base', 'sdxl_ipadapter', 'sdxl_vision'])

    def test_sdxl_settings_and_clip_lora_strength_round_trip_on_an_existing_project(self):
        original = self.library.load(self.project['id'])
        # An existing job genuinely predates these controls.
        for key in list(original['settings']):
            if key.startswith('sdxl_'):
                del original['settings'][key]
        self.library.save(original)
        result = self.library.update_project(original['id'], original['revision'], {
            'profile': 'sdxl_base', 'settings': {'sdxl_negative_prompt': 'extra lens',
            'sdxl_source_mode': 'img2img', 'sdxl_reference_strength': .65,
            'sdxl_img2img_denoise': .55, 'sdxl_edit_denoise': .8,
            'sdxl_sampler': 'dpmpp_2m', 'sdxl_scheduler': 'karras'},
            'loras': [{'name': 'style.safetensors', 'profile': 'sdxl_base', 'strength': .8,
                       'strength_clip': .4, 'enabled': True, 'trigger': 'pixel art'}]})
        self.assertEqual(result['settings']['sdxl_negative_prompt'], 'extra lens')
        self.assertEqual(result['settings']['sdxl_source_mode'], 'img2img')
        self.assertEqual(result['loras'][0]['strength_clip'], .4)
        self.assertEqual(result['settings']['mesh_backend'], 'pixal_single')

    def test_text_generation_uses_sdxl_checkpoint_dual_clip_negative_and_four_channel_latent(self):
        result = self.recipe(settings={'sdxl_negative_prompt': 'extra lens'})
        self.assertEqual(len(self.nodes(result, 'AW_LoadSDXLCheckpoint')), 1)
        self.assertFalse(self.nodes(result, 'CLIPLoader'))
        self.assertFalse(self.nodes(result, 'UNETLoader'))
        encoders = self.nodes(result, 'CLIPTextEncodeSDXL')
        self.assertEqual(len(encoders), 2)
        self.assertTrue(any(n['inputs']['text_g'] == 'extra lens' for n in encoders))
        self.assertEqual(len(self.nodes(result, 'EmptyLatentImage')), 1)
        self.assertFalse(self.nodes(result, 'EmptyFlux2LatentImage'))
        sampler = self.nodes(result, 'KSampler')[0]['inputs']
        self.assertEqual((sampler['sampler_name'], sampler['scheduler'], sampler['denoise']),
                         ('dpmpp_2m', 'karras', 1.0))
        self.assertEqual(result['details']['negative_prompt'], 'extra lens')

    def test_multiple_references_are_padded_and_condition_one_output_without_img2img(self):
        self.image(name='one')
        self.image(name='two')
        result = self.recipe(settings={'sdxl_reference_strength': .6})
        self.assertEqual(len(self.nodes(result, 'ResizeAndPadImage')), 2)
        self.assertEqual(len(self.nodes(result, 'ImageBatch')), 1)
        adapter = self.nodes(result, 'IPAdapterAdvanced')[0]['inputs']
        self.assertEqual(adapter['weight'], .6)
        self.assertEqual(adapter['combine_embeds'], 'average')
        self.assertEqual(self.nodes(result, 'EmptyLatentImage')[0]['inputs']['batch_size'], 1)
        self.assertFalse(self.nodes(result, 'VAEEncode'))
        self.assertEqual(len(result['details']['references']), 2)

    def test_img2img_encodes_the_source_with_explicit_denoise(self):
        self.image()
        result = self.recipe(settings={'sdxl_source_mode': 'img2img', 'sdxl_img2img_denoise': .55})
        self.assertEqual(len(self.nodes(result, 'VAEEncode')), 1)
        self.assertFalse(self.nodes(result, 'EmptyLatentImage'))
        self.assertEqual(self.nodes(result, 'KSampler')[0]['inputs']['denoise'], .55)

    def test_masked_edit_uses_native_inpaint_mask_and_keeps_the_compositing_contract(self):
        source = self.image()
        mask = self.image(name='mask')
        self.project['task_payload'] = {'edit': {'source': source, 'mask': mask,
            'prompt': 'one orange handle', 'id': 'edit1', 'replace_detail': True}}
        result = self.recipe('edit_image', 'source', {'sdxl_edit_denoise': .8})
        self.assertEqual(len(self.nodes(result, 'VAEEncodeForInpaint')), 1)
        self.assertEqual(self.nodes(result, 'KSampler')[0]['inputs']['denoise'], .8)
        self.assertEqual(result['details']['edit']['source']['sha256'], source['sha256'])
        self.assertEqual(result['details']['edit']['mask']['sha256'], mask['sha256'])

    def test_shared_sdxl_lora_patches_model_and_clip_before_text_encoding(self):
        path = Path(self.directory.name) / 'style.safetensors'
        path.write_bytes(b'graph-fixture-only')
        self.project['profile'] = 'sdxl_juggernaut'
        self.project['loras'] = [{'name': path.name, 'profile': 'sdxl_base', 'strength': .8,
                                  'strength_clip': .4, 'enabled': True, 'trigger': 'pixel art'}]
        with patch.object(recipes, 'local_lora', return_value=str(path)):
            result = self.recipe()
        loader = self.nodes(result, 'AW_LoadSDXLLoRA')[0]['inputs']
        self.assertEqual((loader['strength_model'], loader['strength_clip']), (.8, .4))
        self.assertIn('pixel art', result['details']['prompt'])
        self.assertEqual(len(result['details']['loras']), 1)

    def test_optional_sample_lora_is_downloaded_only_when_enabled(self):
        self.assertNotIn('sdxl_pixel_art', recipes.required_models(self.project, 'image'))
        self.project['loras'] = [{'name': 'sdxl-pixel-art-xl.safetensors', 'profile': 'sdxl_base',
                                  'enabled': True, 'strength': .8}]
        self.assertIn('sdxl_pixel_art', recipes.required_models(self.project, 'image'))
        self.project['loras'][0]['enabled'] = False
        self.assertNotIn('sdxl_pixel_art', recipes.required_models(self.project, 'image'))

    def test_prompt_enhancement_uses_sdxl_guidance_and_preserves_user_style(self):
        contract = prompt_contracts.contract('sdxl_juggernaut', 'enhance', True, 'vehicles')
        self.assertEqual(contract['profile'], 'sdxl_juggernaut')
        self.assertTrue(any('RunDiffusion/Juggernaut' in url for url in contract['sources']))
        self.assertIn('SDXL', contract['instruction'])
        prompt = prompt_contracts.image_task('sdxl_base', 'create_image', 'pixel art toy camera', '', None,
                                            category='props', has_images=False)
        self.assertIn('pixel art toy camera', prompt['prompt'])

    def test_single_object_sdxl_prompt_puts_layout_exclusions_only_in_negative_conditioning(self):
        result = self.recipe()
        positive = result['details']['prompt'].lower()
        self.assertNotIn('contact sheet', positive)
        self.assertNotIn('panels', positive)
        self.assertNotIn('do not', positive)
        self.assertIn('single object', positive)
        self.assertIn('collage', result['details']['negative_prompt'])
        self.assertIn('contact sheet', result['details']['negative_prompt'])


if __name__ == '__main__':
    unittest.main()
