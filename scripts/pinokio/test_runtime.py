import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
import runtime
from bootstrap import Layout


class RuntimeTests(unittest.TestCase):
    def test_restart_keeps_the_same_addresses(self):
        with tempfile.TemporaryDirectory() as directory:
            layout=Layout(directory)
            first=runtime.installation_ports(layout)
            self.assertEqual(runtime.installation_ports(layout),first)
            with socket.socket() as existing:
                existing.bind(('127.0.0.1',first[0]));existing.listen()
                with self.assertRaisesRegex(RuntimeError,'already in use'):
                    runtime.installation_ports(layout)
            self.assertEqual(runtime.installation_ports(layout),first)

    def test_ports_do_not_reuse_an_existing_listener(self):
        with socket.socket() as existing:
            existing.bind(('127.0.0.1',0));existing.listen()
            ports=runtime.available_ports(2)
            self.assertEqual(len(set(ports)),2)
            self.assertNotIn(existing.getsockname()[1],ports)

    def test_commands_use_this_install_and_separate_persistent_paths(self):
        layout=Layout(Path(tempfile.gettempdir())/'foundry-runtime-test')
        commands=runtime.service_commands(layout,43001,43002)
        self.assertEqual(commands['comfy'][0],str(layout.host_python))
        self.assertIn(str(layout.data/'user'),commands['comfy'])
        self.assertIn('--models-directory',commands['comfy'])
        self.assertIn('43002',commands['hi3d'])
        self.assertNotIn('--open',commands['hi3d'])

    def test_lock_blocks_second_owner_and_releases_after_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'operation.lock'
            with runtime.InstallationLock(path):
                with self.assertRaises(RuntimeError):
                    with runtime.InstallationLock(path):pass
            with runtime.InstallationLock(path):pass

    @unittest.skipUnless(sys.platform=='win32','Windows lifecycle proof')
    def test_closing_job_stops_only_owned_child(self):
        job=runtime.ChildJob()
        child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)'],creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            job.add(child);job.close()
            self.assertIsNotNone(child.wait(timeout=10))
        finally:
            if child.poll() is None:child.kill();child.wait()
            job.close()

    def test_mcp_configuration_tracks_runtime_and_limits_local_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            layout=Layout(directory)
            runtime.write_mcp_configuration(layout)
            conf=json.loads((layout.state/'mcp.json').read_text())['mcpServers']['mumblebox-foundry']
            self.assertEqual(conf['command'],str(layout.mcp_python))
            self.assertIn(str(layout.root/'scripts'/'pinokio'/'connect_agent.py'),conf['args'])
            self.assertNotIn('8188',' '.join(conf['args']))


if __name__=='__main__':unittest.main()
