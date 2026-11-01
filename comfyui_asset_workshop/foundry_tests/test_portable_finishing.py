import ast
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class PortableFinishingTests(unittest.TestCase):
    def test_finishing_is_shipped_without_developer_paths(self):
        folder=ROOT/'finishing'
        self.assertTrue((folder/'nodes.py').is_file())
        for path in folder.glob('*.py'):
            source=path.read_text(encoding='utf-8')
            ast.parse(source)
            self.assertNotIn('C:\\Dev\\',source,str(path))
            self.assertNotIn('Blender Foundation',source,str(path))

    def test_package_contract_loads_without_experiment_sys_path(self):
        from finishing.package_catalog import parse_selection
        from finishing.quad_nodes import Hi3DExportBundle
        selection=Hi3DExportBundle.selection(True,saved_print='asset.stl')
        self.assertEqual(set(selection.variants),{'print'})

    def test_registry_uses_distributed_resource_file(self):
        from foundry.catalog import catalog
        result=catalog()
        self.assertTrue(result['resource_registry_available'])
        self.assertEqual(result['github'],'https://github.com/mumblebox-gpt')

if __name__=='__main__':unittest.main()
