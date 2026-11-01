import json
import sys
import tempfile
import unittest
from pathlib import Path
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from foundry.library import Library
from foundry.preferences import Preferences
from foundry.routes import register
from foundry.receipts import sync

class RouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.outputs = self.root / "outputs"; self.outputs.mkdir()
        self.library = Library(self.root / "state", self.outputs)
        self.prefs = Preferences(self.root / "state" / "preferences.json")
        routes = web.RouteTableDef()
        register(routes, self.library, self.prefs)
        app = web.Application(); app.add_routes(routes)
        self.client = TestClient(TestServer(app)); await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        self.temp.cleanup()

    async def test_cross_origin_mutation_is_rejected(self):
        response = await self.client.patch("/mumblebox-foundry/v1/preferences", json={"theme":"dark"},
                                           headers={"Origin":"https://unrelated.example"})
        self.assertEqual(response.status, 403)
        self.assertIsNone(self.prefs.read()["theme"])

    async def test_preferences_persist_without_accepting_secret_fields(self):
        url = "/mumblebox-foundry/v1/preferences"
        response = await self.client.patch(url, json={"theme":"light"})
        self.assertEqual(response.status, 200)
        response = await self.client.patch(url, json={"token":"do-not-save"})
        self.assertEqual(response.status, 400)
        self.assertNotIn("do-not-save", self.prefs.path.read_text())

    async def test_bootstrap_and_gallery_read_do_not_create_exports(self):
        response = await self.client.get("/mumblebox-foundry/v1/bootstrap")
        data = await response.json()
        self.assertEqual(response.status, 200)
        self.assertFalse(data["workflow"]["wizard"])
        self.assertIsNone(data["donate"])
        response = await self.client.get("/mumblebox-foundry/v1/library?kind=image")
        self.assertEqual((await response.json())["items"], [])
        self.assertEqual(list(self.outputs.iterdir()), [])

    async def test_unlisted_import_and_large_requests_fail(self):
        response = await self.client.post("/mumblebox-foundry/v1/library/import-package",
                                           json={"candidate_id":"C:/private/file.zip"})
        self.assertEqual(response.status, 400)
        response = await self.client.post("/mumblebox-foundry/v1/library/sync", data="x"*17000)
        self.assertEqual(response.status, 400)

    async def test_sync_is_bounded_and_quarantines_invalid_receipts(self):
        outbox = self.library.root / "outbox"; outbox.mkdir()
        for i in range(35):
            (outbox / (str(i)+".json")).write_text(json.dumps({"schema":"unknown"}))
        result = sync(self.library)
        self.assertEqual(result, {"imported":0,"failed":32,"more":True,"previews":0})
        self.assertEqual(len(list(outbox.glob("*.json"))),3)
        self.assertEqual(len(list(outbox.glob("*.failed"))),32)

if __name__ == "__main__": unittest.main()
