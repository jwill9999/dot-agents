#!/usr/bin/env python3
"""Explicit test-artefact retirement; defaults to a metadata-only audit."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import time


class Refused(RuntimeError):
    pass


def absolute(path):
    p = Path(path).expanduser()
    if not p.is_absolute() or '..' in p.parts:
        raise Refused('Expected an absolute path without parent traversal')
    return p


def canonical(path):
    p = absolute(path)
    for ancestor in reversed((p, *p.parents)):
        if ancestor.is_symlink():
            raise Refused(f'Symlink path component: {ancestor}')
    return p


def within(path, root):
    return path == root or root in path.parents


def forbidden(name):
    low = name.lower()
    return (low in {'.git', '.hg', '.svn', 'auth.json', 'credentials.json',
                    'secrets.json', 'config.toml'} or low == '.env' or
            low.startswith('.env.') or low.endswith(('.sqlite', '.sqlite3',
            '.sqlite-wal', '.sqlite-shm', '.db', '.db-wal', '.db-shm',
            '.pem', '.key', '.p12')))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def raise_walk_error(error):
    raise error


def snapshot(path, hashes=False, fixture_databases=None):
    canonical(path)
    fixture_databases = fixture_databases or {}
    for name, expected in fixture_databases.items():
        relative = Path(name)
        if (relative.is_absolute() or '..' in relative.parts or
                not name.endswith(('.sqlite', '.sqlite3', '.sqlite-wal', '.sqlite-shm',
                                   '.db', '.db-wal', '.db-shm')) or
                len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected)):
            raise Refused('Fixture database exception needs a relative path and SHA-256')
    if not (path.is_dir() or path.is_file()) or path.stat().st_uid != os.getuid():
        raise Refused('Candidate must be an owned regular file or directory')
    if forbidden(path.name) and path.name not in fixture_databases:
        raise Refused('Protected candidate name')
    if any((parent / '.git').exists() for parent in (path, *path.parents)):
        raise Refused('Candidate is inside a source repository; use its own retirement procedure')
    rows = {}
    entries = ([(path.parent, [], [path.name])] if path.is_file() else
               os.walk(path, followlinks=False, onerror=raise_walk_error))
    for base, dirs, files in entries:
        for name in sorted(dirs + files):
            p = Path(base) / name
            s = p.lstat()
            rel = path.name if path.is_file() else str(p.relative_to(path))
            expected = fixture_databases.get(rel)
            if (forbidden(name) and expected is None) or s.st_uid != os.getuid():
                raise Refused(f'Protected/unowned entry: {p}')
            if not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)):
                raise Refused(f'Link or unsupported entry: {p}')
            if s.st_dev != path.stat().st_dev:
                raise Refused(f'Nested filesystem: {p}')
            if expected is not None and digest(p) != expected:
                raise Refused('Fixture database differs from its reviewed CI artefact')
            row = {'type': 'file' if stat.S_ISREG(s.st_mode) else 'dir',
                   'size': s.st_size if stat.S_ISREG(s.st_mode) else 0,
                   'allocated': s.st_blocks * 512,
                   'mtimeNs': s.st_mtime_ns, 'inode': s.st_ino,
                   'mode': stat.S_IMODE(s.st_mode)}
            if hashes and row['type'] == 'file':
                row['sha256'] = digest(p)
            rows[path.name if path.is_file() else str(p.relative_to(path))] = row
    return rows


def check_idle(path):
    executable = shutil.which('lsof')
    if executable is None:
        raise Refused('lsof is required; activity check unavailable')
    # Also check reported pathname handles: directory/inode scans alone may miss
    # handles retained through shared filesystems or replaced pathname entries.
    all_handles = subprocess.run([executable, '-nP', '-F', 'n'],
                                capture_output=True, text=True, timeout=60)
    if all_handles.returncode != 0 or all_handles.stderr.strip():
        raise Refused('Global open-handle inventory is incomplete')
    for line in all_handles.stdout.splitlines():
        if line.startswith('n'):
            name = line[1:]
            if name == str(path) or name.startswith(str(path) + os.sep):
                raise Refused('Open pathname handle references this target')
    args = [executable, '-nP'] + (['+D'] if path.is_dir() else []) + [str(path)]
    result = subprocess.run(args,
                            capture_output=True, text=True, timeout=60)
    if result.returncode != 1 or result.stdout.strip() or result.stderr.strip():
        raise Refused('Open handles or incomplete activity check')
    result = subprocess.run(['ps', '-axo', 'command='], capture_output=True,
                            text=True, check=True, timeout=15)
    if str(path) in result.stdout:
        raise Refused('A process command references this target')


def load_config(path):
    cfg = json.loads(path.read_text())
    roots = [canonical(p) for p in cfg['allowed_roots']]
    # A protected path may intentionally be a link; targets may never traverse it.
    protected = [absolute(p) for p in cfg['protected_paths']]
    archive = canonical(cfg['archive_root'])
    mount = canonical(cfg['archive_mount'])
    if not mount.is_mount() or not within(archive, mount):
        raise Refused('Expected archive filesystem is not mounted')
    candidates = []
    for item in cfg['candidates']:
        p = canonical(item['path'])
        if not item.get('reason') or not any(p != r and within(p, r) for r in roots):
            raise Refused('Candidate needs a reason and a strictly containing allowed root')
        if any(within(p, q) or within(q, p) for q in protected):
            raise Refused(f'Candidate overlaps a protected path: {p}')
        if any(within(p, q) or within(q, p) for q in candidates):
            raise Refused('Candidates overlap')
        if within(archive, p) or within(p, archive):
            raise Refused('Archive and source overlap')
        candidates.append(p)
    return cfg, archive, mount


def audit(cfg, mount):
    rows = []
    for item in cfg['candidates']:
        p = canonical(item['path'])
        row = {**item, 'status': 'blocked'}
        try:
            if not p.exists():
                row['status'] = 'absent'
                rows.append(row)
                continue
            if p.stat().st_dev == mount.stat().st_dev:
                raise Refused('Recovery archive must use another filesystem')
            files = snapshot(p, fixture_databases=item.get('fixture_databases'))
            check_idle(p)
            for activity_path in item.get('activity_paths', []):
                related = canonical(activity_path)
                if related not in p.parents:
                    raise Refused('Activity guard must be a parent of the candidate')
                check_idle(related)
            row.update(status='eligible', inventory=files,
                       allocatedBytes=sum(v['allocated'] for v in files.values()))
        except (OSError, Refused, subprocess.SubprocessError) as e:
            row['blockedReason'] = str(e)
        rows.append(row)
    token = hashlib.sha256(json.dumps({'config': cfg, 'rows': rows}, sort_keys=True).encode()).hexdigest()
    return rows, token


def inventory(roots):
    """Metadata only; no file contents, links or nested filesystems are followed."""
    output = []
    for value in roots:
        root = canonical(value)
        device = root.stat().st_dev
        groups, seen, errors = {}, set(), 0
        def count_walk_error(_error):
            nonlocal errors
            errors += 1
        for base, dirs, files in os.walk(root, followlinks=False, onerror=count_walk_error):
            retained = []
            for name in dirs:
                try:
                    p = Path(base) / name
                    if not p.is_symlink() and p.stat().st_dev == device:
                        retained.append(name)
                except OSError:
                    errors += 1
            dirs[:] = retained
            for name in files:
                p = Path(base) / name
                try:
                    s = p.lstat()
                    key = (s.st_dev, s.st_ino)
                    if not stat.S_ISREG(s.st_mode) or s.st_dev != device or key in seen:
                        continue
                    seen.add(key)
                    rel = p.relative_to(root)
                    group = rel.parts[0] if len(rel.parts) > 1 else '(root files)'
                    row = groups.setdefault(group, {'allocatedBytes': 0, 'logicalBytes': 0, 'files': 0})
                    row['allocatedBytes'] += s.st_blocks * 512
                    row['logicalBytes'] += s.st_size
                    row['files'] += 1
                except OSError:
                    errors += 1
        output.append({'root': str(root), 'freeBytes': shutil.disk_usage(root).free,
                       'scanErrors': errors, 'groups': dict(sorted(groups.items(),
                       key=lambda item: -item[1]['allocatedBytes']))})
    return {'mode': 'read-only inventory', 'roots': output,
            'sizeCaveat': 'Reported allocation may include shared filesystem extents; it is not guaranteed reclaimable space.'}


def verify_archive(path, rows):
    expected = {k: v for k, v in rows.items() if v['type'] == 'file'}
    seen = set()
    with tarfile.open(path, 'r|gz') as archive:
        for entry in archive:
            if entry.isdir():
                if entry.name not in rows or rows[entry.name]['type'] != 'dir':
                    raise Refused('Unexpected archive directory')
                continue
            if not entry.isfile() or entry.name not in expected or entry.name in seen:
                raise Refused('Unexpected, linked or duplicate archive entry')
            h = hashlib.sha256()
            with archive.extractfile(entry) as f:
                for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
                    h.update(block)
            if entry.size != expected[entry.name]['size'] or h.hexdigest() != expected[entry.name]['sha256']:
                raise Refused('Archive content verification failed')
            seen.add(entry.name)
    if seen != set(expected):
        raise Refused('Archive is incomplete')


def save(path, data):
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('x') as f:
        os.chmod(tmp, 0o600)
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def retire(path, archive, planned, activity_check=check_idle, fixture_databases=None):
    activity_check(path)
    if snapshot(path, fixture_databases=fixture_databases) != planned:
        raise Refused('Source changed since reviewed audit')
    rows = snapshot(path, hashes=True, fixture_databases=fixture_databases)
    with tarfile.open(archive, 'x:gz', compresslevel=1) as out:
        os.chmod(archive, 0o600)
        for name in sorted(rows):
            out.add(path if path.is_file() else path / name, arcname=name, recursive=False)
    with archive.open('rb') as f:
        os.fsync(f.fileno())
    verify_archive(archive, rows)
    activity_check(path)
    if snapshot(path, hashes=True, fixture_databases=fixture_databases) != rows:
        raise Refused('Source changed while archiving; retain it')
    if path.is_dir() and not shutil.rmtree.avoids_symlink_attacks:
        raise Refused('Platform lacks safe directory removal')
    manifest = archive.with_suffix(archive.suffix + '.manifest.json')
    save(manifest, {'source': str(path), 'archive': str(archive), 'files': rows,
                    'archiveSha256': digest(archive), 'verified': True})
    # Only explicitly authorised, inactive targets reach this operation.
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return {'archive': str(archive), 'manifest': str(manifest),
            'allocatedBytes': sum(v['allocated'] for v in rows.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path,
                        default=os.environ.get('TEST_STORAGE_CONFIG') or
                        Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) /
                        'test-storage/config.json')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--inventory', action='store_true')
    parser.add_argument('--plan-digest')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    if not args.config:
        parser.error('--config or TEST_STORAGE_CONFIG is required')
    config_path = canonical(args.config)
    if args.inventory:
        if args.apply:
            raise Refused('--inventory cannot be combined with --apply')
        cfg = json.loads(config_path.read_text())
        print(json.dumps(inventory(cfg.get('inventory_roots', cfg['allowed_roots'])), indent=2))
        return
    maintenance_lock = None
    if args.apply:
        lock_path = config_path.parent / '.maintenance.lock'
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        maintenance_lock = os.fdopen(fd, 'w')
        try:
            fcntl.flock(maintenance_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refused('Another maintenance run owns this configuration directory')
    cfg, archive, mount = load_config(config_path)
    rows, token = audit(cfg, mount)
    summary = {'planDigest': token, 'candidates': [{k: v for k, v in row.items()
                if k != 'inventory'} for row in rows], 'freeBytesByRoot': {
                str(root): shutil.disk_usage(root).free for root in cfg['allowed_roots']}}
    if not args.apply:
        print(json.dumps(summary, indent=2))
        return
    if args.plan_digest != token or not args.receipt:
        raise Refused('Apply requires the unchanged audit digest and a receipt path')
    receipt = canonical(args.receipt)
    if receipt.exists() or not receipt.parent.is_dir():
        raise Refused('Receipt must be new with an existing parent')
    archive.mkdir(mode=0o700, parents=True, exist_ok=True)
    batch = archive / (time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '-' + token[:12])
    batch.mkdir(mode=0o700)
    mount_device = mount.stat().st_dev
    state = {**summary, 'archiveDirectory': str(batch), 'actions': [],
             'scriptSha256': digest(Path(__file__)), 'configSha256': digest(config_path)}
    save(receipt, state)
    for number, row in enumerate(rows):
        if row['status'] != 'eligible':
            continue
        path = Path(row['path'])
        free_before = shutil.disk_usage(path).free
        action = {'path': str(path), 'status': 'started', 'freeBytesBefore': free_before}
        state['actions'].append(action)
        save(receipt, state)
        try:
            if not mount.is_mount() or batch.stat().st_dev != mount_device:
                raise Refused('Archive filesystem changed or unmounted')
            print(json.dumps({'archiving': str(path)}), flush=True)
            action.update(retire(path, batch / f'{number:03d}-{path.name}.tar.gz', row['inventory'],
                                 fixture_databases=row.get('fixture_databases')))
            action.update(status='retired', freeBytesAfter=shutil.disk_usage(path.parent).free)
            action['observedFreeBytesChange'] = action['freeBytesAfter'] - free_before
            save(receipt, state)
            print(json.dumps(action), flush=True)
        except Exception as e:
            action.update(status='failed-review-required', error=str(e))
            save(receipt, state)
            raise
    state['completed'] = True
    save(receipt, state)


if __name__ == '__main__':
    try:
        main()
    except (OSError, Refused, subprocess.SubprocessError) as error:
        raise SystemExit(f'Refused: {error}')
