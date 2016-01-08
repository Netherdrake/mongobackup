#!/usr/bin/env python
# encoding: utf-8

"""
MongoDB backup and restore utility script.
"""

import subprocess
import shutil
import time
import shlex
import os
from os.path import join, basename

SLEEP_DURATION = 3600 * 12  # 12 hours sleep
MAX_BACKUPS = 10


def backup():
    # Backup
    now = str(int(round(time.time() * 1000)))
    backup_dir = '/backup'
    backup_name = join(backup_dir, '%s-%s' % (now, os.getenv('BACKUP_NAME', '')))
    cmd = 'mongodump --out=%s ' % backup_name
    args = [('--host=', 'MONGODB_BACKUP_HOST'),
            ('--port=', 'MONGODB_BACKUP_PORT'),
            ('--username=', 'MONGODB_BACKUP_USER'),
            ('--password=', 'MONGODB_BACKUP_PASS'),
            ('--db=', 'MONGODB_BACKUP_DB')]
    for arg in args:
        if os.getenv(arg[1]):
            cmd += '%s%s ' % (arg[0], os.getenv(arg[1]))
    print(cmd)
    subprocess.call(shlex.split(cmd))
    print('')

    # Store to S3
    s3_bucket = os.getenv('S3_BUCKET')
    s3_path = os.getenv('S3_PATH')
    if backup_name and s3_bucket and s3_path:
        backup_tgz = '%s.tgz' % backup_name
        commands = ['tar czf "%s" "%s"' % (backup_tgz, backup_name),
                    'aws s3 cp "%s" s3://%s/%s/%s' % (backup_tgz, s3_bucket, s3_path, basename(backup_tgz)),
                    'rm -f %s' % backup_tgz]
        for cmd in commands:
            print(cmd)
            subprocess.call(shlex.split(cmd))
            print('')

    # Delete old backups
    dirs = [join(backup_dir, d) for d in os.listdir(backup_dir)]
    dirs = sorted(dirs, key=lambda d: basename(d).split('-')[0])
    if MAX_BACKUPS and len(dirs) > int(MAX_BACKUPS):
        for dir in dirs[:-int(MAX_BACKUPS)]:
            try:
                shutil.rmtree(dir)
            except Exception:
                pass


def restore():
    # Restore
    cmd = "mongorestore "
    args = [('--host=', 'MONGODB_RESTORE_HOST'),
            ('--port=', 'MONGODB_RESTORE_PORT'),
            ('--username=', 'MONGODB_RESTORE_USER'),
            ('--password=', 'MONGODB_RESTORE_PASS'),
            ('--db=', 'MONGODB_RESTORE_DB'),
            ('/backup/', 'FILE_TO_RESTORE')]
    for arg in args:
        if os.getenv(arg[1]):
            cmd += '%s%s ' % (arg[0], os.getenv(arg[1]))
    print(cmd)
    subprocess.call(shlex.split(cmd))
    print()


def backup_and_restore():
    backup()
    restore()


if __name__ == "__main__":
    try:
        while True:
            backup()
            time.sleep(SLEEP_DURATION)
    except KeyboardInterrupt:
        pass
