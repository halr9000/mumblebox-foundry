"""Download accounting for the description assistant, without model execution."""
import ast
import hashlib
import io
from pathlib import Path
import tempfile
import types
import unittest
import zipfile

source = Path(__file__).parents[1] / "description_helper.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
functions = ast.Module(body=[node for node in tree.body
                            if isinstance(node, ast.FunctionDef) and node.name == "weights"], type_ignores=[])


class DescriptionDownloadTests(unittest.TestCase):
    def test_runtime_reports_aggregate_files_and_verification(self):
        functions = ast.Module(body=[node for node in tree.body
                                     if isinstance(node, ast.FunctionDef) and node.name == "runtime"], type_ignores=[])
        with tempfile.TemporaryDirectory() as directory:
            progress, opened, verified = {}, [], []
            archives, bodies = [], {}
            for name, entry in (("server.zip", "llama-server.exe"), ("cuda.zip", "cudart.dll")):
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, "w") as bundle:
                    bundle.writestr(entry, b"fixture")
                body = buffer.getvalue()
                bodies[name] = body
                archives.append((name, len(body), hashlib.sha256(body).hexdigest()))

            def cached(path, size, sha):
                if path.suffix == ".part":
                    verified.append(dict(progress))
                return path.is_file() and path.stat().st_size == size and hashlib.sha256(path.read_bytes()).hexdigest() == sha

            def open_url(request, timeout):
                opened.append(dict(progress))
                response = io.BytesIO(bodies[request.url.rsplit("/", 1)[-1]])
                response.status = 200
                return response

            scope = {
                "Path": Path, "os": types.SimpleNamespace(environ={}, name="nt"),
                "platform": types.SimpleNamespace(system=lambda: "Windows", machine=lambda: "AMD64"),
                "RUNTIMES": {("Windows", "AMD64"): archives},
                "folder_paths": types.SimpleNamespace(get_user_directory=lambda: directory),
                "models": types.SimpleNamespace(DOWNLOAD=progress),
                "contained": lambda root, name: root / name, "cached_file": cached,
                "check_cancelled": lambda: None,
                "shutil": types.SimpleNamespace(disk_usage=lambda root: types.SimpleNamespace(free=10**9),
                                                copyfileobj=lambda source, target: target.write(source.read())),
                "urllib": types.SimpleNamespace(request=types.SimpleNamespace(
                    Request=lambda url, headers: types.SimpleNamespace(url=url), urlopen=open_url)),
                "zipfile": zipfile, "digest": lambda path: hashlib.sha256(path.read_bytes()).hexdigest(),
                "atomic_json": lambda *args: None,
            }
            exec(compile(functions, str(source), "exec"), scope)
            result = scope["runtime"]()
            self.assertEqual(result.name, "llama-server.exe")
            self.assertEqual([item["name"] for item in opened], ["server.zip", "cuda.zip"])
            self.assertEqual([item["file_index"] for item in opened], [1, 2])
            self.assertEqual([item["batch_total"] for item in opened], [sum(len(b) for b in bodies.values())] * 2)
            self.assertEqual([item["completed_bytes"] for item in opened], [0, len(bodies["server.zip"])])
            self.assertEqual([item["phase"] for item in verified], ["verifying SHA-256"] * 2)
            self.assertEqual(progress["completed_bytes"], sum(len(b) for b in bodies.values()))

    def test_missing_weights_have_their_own_batch_and_installed_files_are_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            progress = {"batch_total": 999, "completed_bytes": 900, "file_count": 9, "file_index": 8}
            observed = []
            root = Path(directory)

            def download(model):
                observed.append(dict(progress))
                destination = root / "LLM" / "Mumblebox" / model["name"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"x" * model["size"])

            scope = {
                "models": types.SimpleNamespace(MODEL_ROOT=root, DOWNLOAD=progress, download_one=download),
                "folder_paths": types.SimpleNamespace(add_model_folder_path=lambda *args: None),
                "check_cancelled": lambda: None,
                "cached_file": lambda path, size, sha: path.is_file() and path.stat().st_size == size,
                "WEIGHTS": {"q4": ("model.gguf", 3, "a"), "vision": ("vision.gguf", 5, "b")},
                "REPO": "fixture", "REVISION": "fixture",
            }
            exec(compile(functions, str(source), "exec"), scope)
            paths = scope["weights"]("q4")
            self.assertEqual([p.name for p in paths], ["model.gguf", "vision.gguf"])
            self.assertEqual([p["batch_total"] for p in observed], [8, 8])
            self.assertEqual([p["completed_bytes"] for p in observed], [0, 3])
            self.assertEqual([p["file_index"] for p in observed], [1, 2])
            self.assertEqual(progress["completed_bytes"], 8)
            scope["weights"]("q4")
            self.assertEqual(len(observed), 2)
            self.assertEqual(progress["file_count"], 0)
            self.assertEqual(progress["batch_total"], 0)


if __name__ == "__main__":
    unittest.main()
