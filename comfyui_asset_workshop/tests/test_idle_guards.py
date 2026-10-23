"""Library mutations must wait for coordinated jobs even between native prompts."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


def function(name, filename, context):
    tree = ast.parse((Path(__file__).parents[1] / filename).read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), filename, "exec"), context)
    return context[name]


class IdleGuardTests(unittest.TestCase):
    def idle(self, coordinated):
        return function("idle", "routes.py", {
            "queue": lambda: SimpleNamespace(get_tasks_remaining=lambda: 0),
            "description_helper": SimpleNamespace(STATE={}),
            "single_image_jobs_active": lambda: coordinated,
            "JobConflict": RuntimeError,
        })

    def test_library_mutations_rejected_between_native_stages(self):
        with self.assertRaisesRegex(RuntimeError, "Mumblebox job"):
            self.idle(True)()

    def test_idle_library_remains_available(self):
        self.idle(False)()

    def test_active_job_check_uses_coordinator_tasks(self):
        context = {"COORDINATOR": None}
        check = function("has_active_jobs", "single_image_routes.py", context)
        self.assertFalse(check())
        context["COORDINATOR"] = SimpleNamespace(tasks={})
        self.assertFalse(check())
        context["COORDINATOR"].tasks["ownedjob"] = object()
        self.assertTrue(check())
