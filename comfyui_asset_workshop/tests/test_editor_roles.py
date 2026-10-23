"""Edit previews cannot change the image or source set until explicitly kept."""
import importlib
import ast
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest

from PIL import Image

package = types.ModuleType('_aw_editor_roles')
package.__path__ = [str(Path(__file__).parents[1])]
sys.modules[package.__name__] = package
store = importlib.import_module('_aw_editor_roles.store')
edits = importlib.import_module('_aw_editor_roles.image_edits')


class EditorRoleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.library = store.AssetStore(temporary.name)
        self.project = self.library.create_project()
        self.sequence = 0

    def image(self, role):
        self.sequence += 1
        relative = f'originals/source{self.sequence}.png'
        path = self.library.path(self.project['id'], relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGBA', (8, 8), 'red').save(path)
        record = {'id': f'image{self.sequence}', 'file': relative,
                  'sha256': store.digest(path)}
        self.project = self.library.add_revision(self.project['id'], role, record)
        return record

    def preview(self, role, record):
        selection = Image.new('L', (8, 8))
        selection.paste(255, (2, 2, 6, 6))
        buffer = io.BytesIO()
        selection.save(buffer, format='PNG')
        edit = edits.create(self.library, self.project['id'], role, record['id'],
                            'Change the selected area to blue', buffer.getvalue())
        self.library.complete_job = lambda *args: None
        _, candidate = edits.save_candidate(self.library, self.project['id'], role,
            'fixture-attempt', Image.new('RGBA', (8, 8), 'blue'), {'edit': edit, 'seed': 42})
        return candidate

    def test_all_roles_keep_full_resolution_and_original_pixels_outside_selection(self):
        for role in store.IMAGE_ROLES:
            with self.subTest(role=role):
                original = self.image(role)
                candidate = self.preview(role, original)
                updated = edits.accept(self.library, self.project['id'], role, candidate['id'])
                selected = self.library.revision(updated, role)
                self.assertEqual(selected['id'], candidate['id'])
                self.assertIsNone(updated['images'][role]['approved'], 'Keeping an edit is not final review')
                with Image.open(self.library.path(updated['id'], selected['file'])) as image:
                    self.assertEqual(image.size, (8, 8))
                    self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 255))
                    self.assertEqual(image.getpixel((3, 3)), (0, 0, 255, 255))
                self.assertEqual(store.digest(self.library.path(updated['id'], original['file'])), original['sha256'])

    def test_preview_and_discard_do_not_change_current_or_approval_or_source_set(self):
        original = self.image('source')
        approved = self.library.approve_image(self.project['id'], 'source', original['id'],
            original['sha256'], 'approved', 'user', '', self.project['revision'])
        self.preview('source', original)
        after = self.library.load(self.project['id'])
        self.assertEqual(after['images']['source']['current'], original['id'])
        self.assertEqual(after['images']['source']['approved'], original['id'])
        self.assertEqual(after['sources'], approved['sources'])

    def test_edit_either_source_preserves_other_source_and_already_generated_design(self):
        first, second = self.image('source'), self.image('source')
        design = self.image('design')
        self.project = self.library.select_image(self.project['id'], self.project['revision'],
            'source', first['id'])
        candidate = self.preview('source', first)
        updated = edits.accept(self.library, self.project['id'], 'source', candidate['id'])
        selected = {r['id'] for r in updated['sources'] if r['enabled']}
        self.assertEqual(selected, {second['id'], candidate['id']})
        self.assertEqual(updated['images']['design']['current'], design['id'])
        self.assertIn(first['id'], {r['id'] for r in updated['images']['source']['revisions']})

    def test_stale_edit_cannot_replace_new_image(self):
        original = self.image('mesh_input')
        candidate = self.preview('mesh_input', original)
        latest = self.image('mesh_input')
        with self.assertRaisesRegex(ValueError, 'original changed'):
            edits.accept(self.library, self.project['id'], 'mesh_input', candidate['id'])
        self.assertEqual(self.library.load(self.project['id'])['images']['mesh_input']['current'], latest['id'])

    def test_direct_adoption_needs_no_generation_but_requires_fresh_review(self):
        source = self.image('source')
        self.project = self.library.adopt_image(self.project['id'], self.project['revision'],
            'source', source['id'], 'mesh_input')
        primary = self.library.revision(self.project, 'mesh_input')
        self.assertEqual(primary['sha256'], source['sha256'])
        self.assertEqual(primary['adopted_from']['revision_id'], source['id'])
        self.assertEqual(self.project['jobs'], [])
        with self.assertRaises(store.ApprovalRequired):
            self.library.mesh_input(self.project['id'])

    def test_reference_edit_retires_package_but_primary_edit_also_retires_mesh(self):
        primary, reference = self.image('mesh_input'), self.image('reference_back')
        self.project['artifacts'] = [{'id': 'mesh1', 'kind': 'mesh', 'stale': False},
                                     {'id': 'package1', 'kind': 'package', 'stale': False}]
        self.library.save(self.project)
        preview = self.preview('reference_back', reference)
        updated = edits.accept(self.library, self.project['id'], 'reference_back', preview['id'])
        self.assertFalse(updated['artifacts'][0]['stale'])
        self.assertTrue(updated['artifacts'][1]['stale'])
        preview = self.preview('mesh_input', primary)
        updated = edits.accept(self.library, self.project['id'], 'mesh_input', preview['id'])
        self.assertTrue(all(a['stale'] for a in updated['artifacts']))

    def test_clear_one_source_keeps_other_inputs_and_saved_files(self):
        first, second = self.image('source'), self.image('source')
        updated = self.library.clear_images(self.project['id'], self.project['revision'], 'source', first['id'])
        self.assertEqual([r['id'] for r in updated['sources'] if r['enabled']], [second['id']])
        self.assertTrue(next(r for r in updated['sources'] if r['id'] == first['id'])['cleared'])
        self.assertFalse(next(r for r in updated['sources'] if r['id'] == second['id']).get('cleared', False))
        self.assertTrue(self.library.path(updated['id'], first['file']).exists())

    def test_cleared_source_can_be_explicitly_restored(self):
        first = self.image('source')
        self.project = self.library.clear_images(self.project['id'], self.project['revision'], 'source', first['id'])
        self.assertTrue(self.project['sources'][0]['cleared'])
        updated = self.library.update_project(self.project['id'], self.project['revision'], {'source_selection': [first['id']]})
        self.assertFalse(updated['sources'][0].get('cleared', False))
        self.assertTrue(updated['sources'][0]['enabled'])

    def test_clear_all_removes_current_pixels_and_approval_but_retains_history(self):
        for role in store.IMAGE_ROLES:
            self.image(role)
        updated = self.library.clear_images(self.project['id'], self.project['revision'])
        self.assertTrue(all(s['current'] is None and s['approved'] is None for s in updated['images'].values()))
        self.assertTrue(all(s['revisions'] for s in updated['images'].values()))
        self.assertFalse(any(r['enabled'] for r in updated['sources']))

    def test_clear_cannot_change_an_active_job(self):
        self.image('mesh_input')
        self.project['jobs'] = [{'id': 'running1', 'state': 'running'}]
        self.project = self.library.save(self.project)
        with self.assertRaises(store.JobConflict):
            self.library.clear_images(self.project['id'], self.project['revision'])

    def test_auto_description_uses_uploaded_source_in_new_project(self):
        self.image('source')
        tree = ast.parse((Path(__file__).parents[1] / 'description_helper.py').read_text(encoding='utf-8'))
        functions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'generate'], type_ignores=[])
        contracts = importlib.import_module('_aw_editor_roles.prompt_contracts')
        scope = {'store': lambda: self.library, 'prompt_contracts': contracts, 'SYSTEM': '',
                 'image_part': lambda path: {'image_file': path.name},
                 'complete': lambda asset, content, **kwargs: content}
        exec(compile(functions, 'description_helper.generate', 'exec'), scope)
        content = scope['generate'](self.project, 'describe')
        self.assertEqual(sum('image_file' in p for p in content), 1)
        self.assertTrue(any('Uploaded source' in p.get('text', '') for p in content))

    def test_enhancement_does_not_invent_unseen_surfaces(self):
        self.image('source')
        self.project['prompt'] = 'A red camera with one lens'
        self.project['design_notes'] = 'The back has a small green star'
        tree = ast.parse((Path(__file__).parents[1] / 'description_helper.py').read_text(encoding='utf-8'))
        functions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'generate'], type_ignores=[])
        scope = {'store': lambda: self.library, 'prompt_contracts': importlib.import_module('_aw_editor_roles.prompt_contracts'),
                 'SYSTEM': '', 'image_part': lambda path: {'image_file': path.name},
                 'complete': lambda asset, content, **kwargs: content}
        exec(compile(functions, 'description_helper.generate', 'exec'), scope)
        content = scope['generate'](self.project, 'enhance')
        instruction = content[0]['text']
        self.assertIn('Do not invent', instruction)
        self.assertIn('small green star', instruction)
        self.assertNotIn('proposals for unspecified surfaces', instruction)


if __name__ == '__main__':
    unittest.main()
