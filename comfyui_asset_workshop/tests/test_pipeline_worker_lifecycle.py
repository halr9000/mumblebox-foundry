"""A host crash must not leave an isolated worker or its child running."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import psutil

@unittest.skipUnless(os.name=='nt','Windows process ownership contract')
class WorkerOwnershipTests(unittest.TestCase):
    def test_host_exit_reaps_owned_worker_tree(self):
        with tempfile.TemporaryDirectory(prefix='mumblebox-owned-worker-') as temp:
            folder=Path(temp);runtime=Path(__file__).parents[1]/'pipeline_workers/trellis_bridge_runtime.py'
            leaf="import os,time;from pathlib import Path;Path("+repr(str(folder/'leaf.pid'))+").write_text(str(os.getpid()));time.sleep(30)"
            worker="import os,time,subprocess,sys;from pathlib import Path;Path("+repr(str(folder/'worker.pid'))+").write_text(str(os.getpid()));subprocess.Popen([sys.executable,'-c',"+repr(leaf)+"]);time.sleep(30)"
            host="import importlib.util,os,sys;from pathlib import Path;Path("+repr(str(folder/'host.pid'))+").write_text(str(os.getpid()));s=importlib.util.spec_from_file_location('owned_runtime',"+repr(str(runtime))+");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.run_worker([sys.executable,'-c',"+repr(worker)+"],"+repr(str(folder/'worker.log'))+",lambda:None)"
            process=subprocess.Popen([sys.executable,'-c',host],creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                deadline=time.monotonic()+10
                while not (folder/'leaf.pid').exists() and time.monotonic()<deadline:time.sleep(.05)
                self.assertTrue((folder/'leaf.pid').exists(),'Owned test worker did not start')
                host_pid=int((folder/'host.pid').read_text());leaf_pid=int((folder/'leaf.pid').read_text());worker_pid=int((folder/'worker.pid').read_text())
                target=psutil.Process(host_pid)
                self.assertIn(folder.name, ' '.join(target.cmdline()))
                target.kill()
                deadline=time.monotonic()+3
                while any(psutil.pid_exists(pid) for pid in (worker_pid,leaf_pid)) and time.monotonic()<deadline:time.sleep(.05)
                self.assertFalse(psutil.pid_exists(leaf_pid),'Host exit left the isolated child alive')
                self.assertFalse(psutil.pid_exists(worker_pid),'Host exit left the isolated worker alive')
            finally:
                for name in ('leaf.pid','worker.pid','host.pid'):
                    marker=folder/name
                    if marker.exists():
                        try:
                            owned=psutil.Process(int(marker.read_text()))
                            if folder.name in ' '.join(owned.cmdline()):owned.kill();owned.wait(5)
                        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                if process.poll() is None:process.kill()
                process.wait(5)
