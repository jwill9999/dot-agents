import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('storage', Path(__file__).with_name('storage.py'))
storage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(storage)


class RetirementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'retired-runtime'
        self.source.mkdir()
        (self.source / 'images').mkdir()
        (self.source / 'images' / 'fixture.img').write_bytes(b'fixture-content' * 4096)
        (self.source / 'manifest.json').write_text('{"fixture": true}')
        self.archive = self.root / 'recovery.tar.gz'

    def tearDown(self):
        self.temp.cleanup()

    def test_success_requires_complete_verified_archive_and_removes_only_target(self):
        neighbour = self.root / 'keep.txt'
        neighbour.write_text('keep')
        before = storage.snapshot(self.source, hashes=True)
        result = storage.retire(self.source, self.archive, storage.snapshot(self.source), lambda _: None)
        self.assertFalse(self.source.exists())
        self.assertEqual(neighbour.read_text(), 'keep')
        storage.verify_archive(self.archive, before)
        self.assertTrue(Path(result['manifest']).is_file())

    def test_changed_source_retained(self):
        planned = storage.snapshot(self.source)
        (self.source / 'manifest.json').write_text('changed')
        with self.assertRaises(storage.Refused):
            storage.retire(self.source, self.archive, planned, lambda _: None)
        self.assertTrue(self.source.exists())
        self.assertFalse(self.archive.exists())

    def test_parent_runtime_activity_blocks_an_idle_image_collection(self):
        cfg = {'candidates': [{'path': str(self.source), 'reason': 'fixture',
                              'activity_paths': [str(self.root)]}]}
        def check(path):
            if path == self.root:
                raise storage.Refused('runtime owner still active')
        mount = SimpleNamespace(stat=lambda: SimpleNamespace(st_dev=-1))
        with patch.object(storage, 'check_idle', side_effect=check):
            rows, _ = storage.audit(cfg, mount)
        self.assertEqual(rows[0]['status'], 'blocked')
        self.assertIn('runtime owner still active', rows[0]['blockedReason'])

    def test_archive_verification_failure_never_deletes(self):
        with patch.object(storage, 'verify_archive', side_effect=storage.Refused('bad archive')):
            with self.assertRaises(storage.Refused):
                storage.retire(self.source, self.archive, storage.snapshot(self.source), lambda _: None)
        self.assertTrue(self.source.exists())

    def test_open_source_never_archived_or_deleted(self):
        def busy(_):
            raise storage.Refused('busy')
        with self.assertRaises(storage.Refused):
            storage.retire(self.source, self.archive, storage.snapshot(self.source), busy)
        self.assertTrue(self.source.exists())
        self.assertFalse(self.archive.exists())

    def test_becoming_busy_after_backup_retains_source(self):
        calls = []
        def busy_after_backup(_):
            calls.append(True)
            if len(calls) == 2:
                raise storage.Refused('became busy')
        with self.assertRaises(storage.Refused):
            storage.retire(self.source, self.archive, storage.snapshot(self.source), busy_after_backup)
        self.assertTrue(self.source.exists())
        self.assertTrue(self.archive.exists())

    def test_source_mutated_during_archival_retained(self):
        original = storage.verify_archive
        def verify_then_change(archive, rows):
            original(archive, rows)
            (self.source / 'manifest.json').write_text('a later change')
        with patch.object(storage, 'verify_archive', side_effect=verify_then_change):
            with self.assertRaises(storage.Refused):
                storage.retire(self.source, self.archive, storage.snapshot(self.source), lambda _: None)
        self.assertTrue(self.source.exists())

    def test_link_rejected(self):
        (self.source / 'escape').symlink_to(self.root)
        with self.assertRaises(storage.Refused):
            storage.snapshot(self.source)

    def test_parent_link_rejected(self):
        link = self.root / 'alias'
        link.symlink_to(self.source)
        with self.assertRaises(storage.Refused):
            storage.canonical(link / 'images')

    def test_credentials_database_and_repository_protected(self):
        for name in ['auth.json', '.env', 'config.toml', 'profile.sqlite', '.git']:
            with self.subTest(name=name):
                p = self.source / name
                p.write_text('protected fixture')
                with self.assertRaises(storage.Refused):
                    storage.snapshot(self.source)
                p.unlink()

    def test_directory_within_repository_rejected(self):
        (self.root / '.git').mkdir()
        with self.assertRaises(storage.Refused):
            storage.snapshot(self.source)

    def test_config_change_invalidates_plan_digest(self):
        cfg = {'candidates': [{'path': str(self.source), 'reason': 'completed fixture'}],
               'archive_root': '/first-archive'}
        mount = self.root
        with patch.object(storage, 'check_idle'):
            _, first = storage.audit(cfg, mount)
            cfg['archive_root'] = '/another-archive'
            _, second = storage.audit(cfg, mount)
        self.assertNotEqual(first, second)

    def test_missing_activity_tool_refuses(self):
        with patch.object(storage.shutil, 'which', return_value=None):
            with self.assertRaises(storage.Refused):
                storage.check_idle(self.source)

    def test_inventory_does_not_follow_links_or_delete(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'keep').write_text('do not follow')
        (self.source / 'outside-link').symlink_to(outside)
        report = storage.inventory([str(self.source)])
        self.assertEqual(sum(row['files'] for row in report['roots'][0]['groups'].values()), 2)
        self.assertTrue((outside / 'keep').is_file())
        self.assertTrue(self.source.is_dir())

    def test_protected_instruction_link_does_not_break_configuration(self):
        link = self.root / 'shared-instructions'
        link.symlink_to(self.root / 'instructions.txt')
        cfg = {'allowed_roots': [str(self.root)], 'protected_paths': [str(link)],
               'archive_root': str(self.root / 'external' / 'archives'),
               'archive_mount': str(self.root / 'external'),
               'candidates': [{'path': str(self.source), 'reason': 'completed fixture'}]}
        path = self.root / 'config.json'
        path.write_text(json.dumps(cfg))
        with patch.object(Path, 'is_mount', return_value=True):
            self.assertEqual(storage.load_config(path)[0], cfg)

    def test_global_handle_blocks_even_without_directory_scan(self):
        result = SimpleNamespace(returncode=0, stderr='',
                                 stdout='n' + str(self.source / 'images/fixture.img') + '\n')
        with patch.object(storage.shutil, 'which', return_value='/tool/lsof'):
            with patch.object(storage.subprocess, 'run', return_value=result) as run:
                with self.assertRaises(storage.Refused):
                    storage.check_idle(self.source)
                self.assertEqual(run.call_count, 1)

    def test_individual_report_retired_without_touching_neighbours(self):
        report = self.root / 'obsolete-report.json'
        report.write_text('{"result":"resolved fixture"}')
        before = storage.snapshot(report, hashes=True)
        storage.retire(report, self.archive, storage.snapshot(report), lambda _: None)
        self.assertFalse(report.exists())
        self.assertTrue(self.source.exists())
        storage.verify_archive(self.archive, before)

    def test_individual_secret_candidate_refused(self):
        secret = self.root / 'auth.json'
        secret.write_text('fixture')
        with self.assertRaises(storage.Refused):
            storage.snapshot(secret)

    def test_file_changed_during_backup_is_retained(self):
        report = self.root / 'report.md'
        report.write_text('initial fixture')
        original = storage.verify_archive
        def verify_then_change(archive, rows):
            original(archive, rows)
            report.write_text('new content')
        with patch.object(storage, 'verify_archive', side_effect=verify_then_change):
            with self.assertRaises(storage.Refused):
                storage.retire(report, self.archive, storage.snapshot(report), lambda _: None)
        self.assertEqual(report.read_text(), 'new content')

    def test_only_exact_reviewed_fixture_database_can_be_retired(self):
        fixture = self.source / 'fixture.sqlite'
        fixture.write_bytes(b'disposable CI fixture')
        exceptions = {'fixture.sqlite': storage.digest(fixture)}
        planned = storage.snapshot(self.source, fixture_databases=exceptions)
        storage.retire(self.source, self.archive, planned, lambda _: None,
                       fixture_databases=exceptions)
        self.assertFalse(self.source.exists())

    def test_fixture_exception_cannot_bypass_secret_protection(self):
        with self.assertRaises(storage.Refused):
            storage.snapshot(self.source, fixture_databases={'auth.json': 'a' * 64})

    def test_changed_fixture_database_is_blocked(self):
        fixture = self.source / 'fixture.sqlite'
        fixture.write_bytes(b'changed')
        with self.assertRaises(storage.Refused):
            storage.snapshot(self.source, fixture_databases={'fixture.sqlite': 'a' * 64})


if __name__ == '__main__':
    unittest.main(verbosity=2)
