"""Exercise the real isolated-worker bridge with a tiny CPU module, no weights."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline_workers import activity
from pipeline_workers.trellis_bridge_runtime import run_worker

class WorkerMonitorTests(unittest.TestCase):
    def test_real_child_reports_cpu_offload_and_is_removed_at_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);script=root/'trellis_texture_worker.py'
            telemetry=Path(__file__).resolve().parents[1]/'pipeline_workers'
            script.write_text('import sys,time\nfrom types import SimpleNamespace\n'
                +'sys.path.insert(0,'+repr(str(telemetry))+')\n'
                +'from worker_telemetry import monitor\nimport torch\n'
                +'model=torch.nn.Linear(1,1)\nmonitor(SimpleNamespace(models={"tiny":model}),sys.argv[1])\ntime.sleep(.8)\n'
                +'if torch.cuda.is_available():\n model.cuda()\n time.sleep(.8)\n model.cpu()\n from pathlib import Path\n Path(sys.argv[1]).with_name("cuda-checked").touch()\n time.sleep(.8)\n')
            seen=[]
            run_worker([sys.executable,str(script),str(root/'request.json')],root/'worker.log',
                       lambda:seen.extend(row['state'] for row in activity.snapshot()))
            self.assertIn('offloaded',seen)
            if (root/'cuda-checked').exists(): self.assertIn('loaded',seen)
            self.assertEqual(activity.snapshot(),[])
            print('Observed owned-worker residency:', ', '.join(sorted(set(seen))))

if __name__=='__main__':unittest.main()
