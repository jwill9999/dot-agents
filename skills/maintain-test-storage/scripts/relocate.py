#!/usr/bin/env python3
"""Verified, explicit external relocation with backward-compatible source links."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import time
import uuid

import storage


def content(rows):
    return {name: {k: value for k, value in row.items()
                   if k in {'type', 'size', 'sha256', 'mode'}}
            for name, row in rows.items()}


def relocate(source, target, planned, journal, activity_check=storage.check_idle):
    storage.canonical(target)
    if target.exists() or target.is_symlink():
        raise storage.Refused('Relocation destination already exists')
    activity_check(source)
    if storage.snapshot(source) != planned:
        raise storage.Refused('Source changed since relocation audit')
    before = storage.snapshot(source, hashes=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.parent / ('.copying-' + uuid.uuid4().hex)
    backup_root = source.parent / ('.storage-moving-' + uuid.uuid4().hex)
    backup = backup_root / source.name
    state = {'source': str(source), 'target': str(target), 'staging': str(staging),
             'localBackup': str(backup), 'status': 'copying', 'files': before}
    storage.save(journal, state)
    if source.is_dir():
        shutil.copytree(source, staging)
    else:
        shutil.copy2(source, staging)
    # File snapshots use the basename as key; normalise the temporary copy's name.
    copied = storage.snapshot(staging, hashes=True)
    if source.is_file():
        copied = {source.name: copied[staging.name]}
    if content(copied) != content(before):
        raise storage.Refused('Relocation content verification failed; source retained')
    for name, row in copied.items():
        if row['type'] == 'file':
            with (staging if source.is_file() else staging / name).open('rb') as copied_file:
                os.fsync(copied_file.fileno())
    activity_check(source)
    if storage.snapshot(source, hashes=True) != before:
        raise storage.Refused('Source changed while copying; source retained')
    staging.rename(target)
    state['status'] = 'external-copy-verified'
    storage.save(journal, state)
    backup_root.mkdir(mode=0o700)
    source.rename(backup)
    try:
        source.symlink_to(target, target_is_directory=backup.is_dir())
    except BaseException:
        backup.rename(source)
        backup_root.rmdir()
        state['status'] = 'link-failed-source-restored'
        storage.save(journal, state)
        raise
    state['status'] = 'linked-local-backup-retained'
    storage.save(journal, state)
    activity_check(backup)
    if storage.snapshot(backup, hashes=True) != before:
        raise storage.Refused('Renamed source changed; local backup retained')
    if source.resolve(strict=True) != target or content(storage.snapshot(target, hashes=True)) != content(before):
        raise storage.Refused('Final link/copy verification failed; local backup retained')
    if backup.is_dir():
        if not shutil.rmtree.avoids_symlink_attacks:
            raise storage.Refused('Platform lacks safe directory removal')
        shutil.rmtree(backup)
    else:
        backup.unlink()
    backup_root.rmdir()
    state['status'] = 'relocated'
    storage.save(journal, state)
    return {'target': str(target), 'journal': str(journal), 'status': 'relocated',
            'allocatedBytes': sum(row['allocated'] for row in before.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--plan-digest')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    config_path = storage.canonical(args.config)
    cfg, external, mount = storage.load_config(config_path)
    targets = []
    for item in cfg['candidates']:
        target = storage.canonical(item['destination'])
        if (not storage.within(target, external) or target == external or
                target.exists() or target.is_symlink() or
                any(storage.within(target, other) or storage.within(other, target) for other in targets)):
            raise storage.Refused('Destination must be new, separate and within the external root')
        targets.append(target)
    lock = None
    if args.apply:
        fd = os.open(config_path.parent / '.maintenance.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        lock = os.fdopen(fd, 'w')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    rows, token = storage.audit(cfg, mount)
    state = {'planDigest': token, 'mode': 'relocation',
             'candidates': [{k: v for k, v in row.items() if k != 'inventory'} for row in rows]}
    if not args.apply:
        print(json.dumps(state, indent=2))
        return
    if token != args.plan_digest or not args.receipt or args.receipt.exists():
        raise storage.Refused('Apply needs the unchanged audit digest and a new receipt')
    receipt = storage.canonical(args.receipt)
    batch = external / '.storage-moves' / (time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '-' + token[:12])
    batch.mkdir(mode=0o700, parents=True)
    state.update(actions=[], journals=str(batch), scriptSha256=storage.digest(Path(__file__)),
                 storageScriptSha256=storage.digest(Path(storage.__file__)))
    storage.save(receipt, state)
    device = mount.stat().st_dev
    for number, row in enumerate(rows):
        if row['status'] != 'eligible':
            continue
        if not mount.is_mount() or batch.stat().st_dev != device:
            raise storage.Refused('External filesystem changed or unmounted')
        source = Path(row['path'])
        action = {'path': str(source), 'status': 'started',
                  'freeBytesBefore': shutil.disk_usage(source).free}
        state['actions'].append(action)
        storage.save(receipt, state)
        print(json.dumps({'relocating': str(source)}), flush=True)
        try:
            def check_owned_idle(path):
                storage.check_idle(path)
                for related in row.get('activity_paths', []):
                    storage.check_idle(storage.canonical(related))
            action.update(relocate(source, Path(row['destination']), row['inventory'],
                                   batch / f'{number:03d}.json', check_owned_idle))
            action['freeBytesAfter'] = shutil.disk_usage(source.parent).free
            action['observedFreeBytesChange'] = action['freeBytesAfter'] - action['freeBytesBefore']
            storage.save(receipt, state)
            print(json.dumps(action), flush=True)
        except BaseException:
            action['status'] = 'review-required'
            storage.save(receipt, state)
            raise
    state['completed'] = True
    storage.save(receipt, state)


if __name__ == '__main__':
    main()
