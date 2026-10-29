import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import relocate
import storage


class RelocationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'original'
        self.source.mkdir()
        (self.source / 'disk.img').write_bytes(b'fixture-only' * 100)
        self.target = self.root / 'external' / 'original'
        self.journal = self.root / 'journal.json'

    def tearDown(self):
        self.temp.cleanup()

    def run_move(self, checker=lambda _: None):
        return relocate.relocate(self.source, self.target, storage.snapshot(self.source), self.journal, checker)

    def test_directory_move_keeps_working_link_and_content(self):
        self.run_move()
        self.assertTrue(self.source.is_symlink())
        self.assertEqual((self.source / 'disk.img').read_bytes(), b'fixture-only' * 100)
        self.assertFalse(list(self.root.glob('.storage-moving-*')))

    def test_file_move_keeps_original_basename_and_content(self):
        self.source = self.source / 'disk.img'
        self.target = self.target / 'disk.img'
        self.run_move()
        self.assertTrue(self.source.is_symlink())
        self.assertEqual(self.source.read_bytes(), b'fixture-only' * 100)

    def test_busy_source_never_moves(self):
        def busy(_):
            raise storage.Refused('busy')
        with self.assertRaises(storage.Refused):
            self.run_move(busy)
        self.assertFalse(self.source.is_symlink())
        self.assertFalse(self.target.exists())

    def test_copy_corruption_preserves_source(self):
        def bad_copy(source, destination):
            destination.mkdir()
            (destination / 'disk.img').write_bytes(b'corrupted')
        with patch.object(relocate.shutil, 'copytree', side_effect=bad_copy):
            with self.assertRaises(storage.Refused):
                self.run_move()
        self.assertFalse(self.source.is_symlink())
        self.assertEqual((self.source / 'disk.img').read_bytes(), b'fixture-only' * 100)

    def test_source_changed_during_copy_is_not_removed(self):
        original = relocate.shutil.copytree
        def copy_then_change(source, target):
            original(source, target)
            (source / 'disk.img').write_bytes(b'new source')
        with patch.object(relocate.shutil, 'copytree', side_effect=copy_then_change):
            with self.assertRaises(storage.Refused):
                self.run_move()
        self.assertFalse(self.source.is_symlink())
        self.assertEqual((self.source / 'disk.img').read_bytes(), b'new source')

    def test_link_failure_restores_original_directory(self):
        with patch.object(Path, 'symlink_to', side_effect=OSError('link denied')):
            with self.assertRaises(OSError):
                self.run_move()
        self.assertFalse(self.source.is_symlink())
        self.assertEqual((self.source / 'disk.img').read_bytes(), b'fixture-only' * 100)
        self.assertTrue(self.target.exists())

    def test_busy_renamed_source_is_not_deleted(self):
        calls = []
        def busy_after_link(_):
            calls.append(True)
            if len(calls) == 3:
                raise storage.Refused('late busy')
        with self.assertRaises(storage.Refused):
            self.run_move(busy_after_link)
        self.assertTrue(self.source.is_symlink())
        self.assertEqual(len(list(self.root.glob('.storage-moving-*/original/disk.img'))), 1)

    def test_existing_destination_is_not_overwritten(self):
        self.target.mkdir(parents=True)
        with self.assertRaises(storage.Refused):
            self.run_move()
        self.assertFalse(self.source.is_symlink())


if __name__ == '__main__':
    unittest.main(verbosity=2)
