import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import hi3d_entry


class StatusWriteTests(unittest.TestCase):
    def test_windows_reader_releases_destination_during_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'status.json'
            target.write_text('{"state":"old"}')
            reader = target.open('r')
            timer = threading.Timer(.15, reader.close)
            timer.start()
            try:
                hi3d_entry.atomic_json(target, {'state': 'new'})
            finally:
                reader.close()
                timer.join()
            self.assertEqual(json.loads(target.read_text()), {'state': 'new'})
            self.assertEqual(list(Path(directory).glob('*.tmp')), [])

    def test_persistent_denial_is_bounded_and_preserves_previous_status(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'status.json'
            target.write_text('{"state":"old"}')
            error = PermissionError('locked')
            error.winerror = 5
            with patch.object(hi3d_entry.os, 'replace', side_effect=error) as replace, patch.object(hi3d_entry.time, 'sleep'):
                with self.assertRaises(PermissionError):
                    hi3d_entry.atomic_json(target, {'state': 'new'})
            self.assertEqual(replace.call_count, 11)
            self.assertEqual(json.loads(target.read_text()), {'state': 'old'})
            self.assertEqual(list(Path(directory).glob('*.tmp')), [])


if __name__ == '__main__':
    unittest.main()
