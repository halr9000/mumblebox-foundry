"""Agent/status reads stay compact without changing the saved provenance."""
import ast
import copy
from pathlib import Path
import unittest


class PublicMetadataTests(unittest.TestCase):
    def test_project_and_artifact_reads_do_not_repeat_full_package_or_recipe(self):
        source = Path(__file__).parents[1] / 'single_image_routes.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        scope = {'copy': copy}
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in ('artifact_public', 'project_public')]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), scope)
        package = {'id': 'package1', 'kind': 'package', 'file': 'packages/package1.zip',
                   'manifest': {'schema': 'mumblebox.agent-package/1', 'reference_images': {'front': {}},
                                'known_discrepancies': [], 'large_private_detail': 'x' * 100000}}
        master = {'id': 'master1', 'kind': 'master', 'recipe': {'profile': 'klein4', 'seed': 1,
                   'models': {'weights': 'x' * 100000}, 'prompt': 'x' * 100000}}
        edited = {'id': 'preview1', 'edit_accepted': False, 'recipe': {
            'edit': {'id': 'edit1', 'source': {'id': 'original1', 'file': 'private-source.png'},
                     'mask': {'file': 'private-mask.png'}}, 'prompt': 'private prompt'}}
        project = {'jobs': [], 'images': {'design': {'revisions': [edited]}}, 'artifacts': [package, master]}
        result = scope['project_public'](project)
        self.assertFalse('manifest' in result['artifacts'][0], 'Full package manifest leaked into status')
        self.assertFalse('models' in result['artifacts'][1]['recipe'], 'Full model provenance leaked into status')
        self.assertFalse('prompt' in result['artifacts'][1]['recipe'], 'Full prompt leaked into status')
        self.assertEqual(result['artifacts'][1]['recipe']['seed'], 1)
        self.assertIn('manifest', package)
        self.assertIn('models', master['recipe'])
        self.assertEqual(scope['artifact_public'](package)['file'], package['file'])
        self.assertEqual(result['images']['design']['revisions'][0]['recipe']['edit'],
                         {'id': 'edit1', 'source': {'id': 'original1'}})
        self.assertIn('mask', edited['recipe']['edit'], 'Public projection must not alter saved provenance')


if __name__ == '__main__':
    unittest.main()
