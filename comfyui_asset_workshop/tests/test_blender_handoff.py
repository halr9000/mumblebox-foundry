import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('blender_handoff_test', Path(__file__).parents[1] / 'blender_handoff.py')
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)


class BlenderHandoffTests(unittest.TestCase):
    def test_launch_uses_separate_arguments_and_preserves_paths_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='asset handoff ') as folder:
            mesh = Path(folder) / 'my mesh.glb'; mesh.write_bytes(b'fixture')
            executable = Path(folder) / 'blender.exe'
            with patch.object(handoff, 'find_blender', return_value=executable), patch.object(handoff.time, 'sleep'), patch.object(handoff.subprocess, 'Popen', return_value=types.SimpleNamespace(pid=123, poll=lambda:None)) as launch:
                self.assertEqual(handoff.open_mesh(mesh)['pid'], 123)
                args, kwargs = launch.call_args
                self.assertEqual(args[0][-3:-1], ['--', str(mesh.resolve())])
                self.assertNotIn('--background', args[0])
                self.assertFalse(kwargs.get('shell', False))

    def test_invalid_mesh_cannot_launch(self):
        with patch.object(handoff.subprocess, 'Popen') as launch:
            with self.assertRaises(ValueError):handoff.open_mesh('missing.glb')
            launch.assert_not_called()

    def test_explicit_missing_executable_has_actionable_error(self):
        with patch.dict(handoff.os.environ, {'MUMBLEBOX_BLENDER': 'missing-blender.exe'}):
            with self.assertRaisesRegex(ValueError, 'MUMBLEBOX_BLENDER'):handoff.find_blender()


if __name__ == '__main__':unittest.main()
