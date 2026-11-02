import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from foundry.workflows.image_to_3d.progress import stage_plan, snapshot

class ProgressTests(unittest.TestCase):
    def test_print_does_not_count_texture_or_quad_work(self):
        self.assertEqual(stage_plan('finish', {'variants': {'print': {}}}), ['print', 'package', 'cleanup'])

    def test_all_selected_outputs_and_cleanup_are_counted(self):
        plan = stage_plan('rocket', {'variants': dict.fromkeys(['detailed','game_balanced','game_compact','quad_light','print'])})
        self.assertEqual(plan, ['turnaround','geometry','refinement','texture','balanced','compact','quads','print','package','cleanup'])

    def test_zip_is_not_the_end_until_cleanup_finishes(self):
        run = {'operation':'finish','selection':{'variants':{'print':{}}},'stages':{'print':{},'package':{}},'status':'cleaning'}
        self.assertLess(snapshot(run)['fraction'], 1)
        self.assertEqual(snapshot(run)['current'], 'cleanup')
        run['status'] = 'complete'
        self.assertEqual(snapshot(run)['fraction'], 1)
        run['cleanup']={'status':'failed'}
        self.assertLess(snapshot(run)['fraction'],1)

    def test_unrelated_prior_stages_do_not_inflate_finish_progress(self):
        run = {'operation':'finish','selection':{'variants':{'print':{}}},'stages':{'turnaround':{},'geometry':{},'refinement':{}},'status':'running'}
        self.assertEqual(snapshot(run)['fraction'], 0)

if __name__ == '__main__': unittest.main()
