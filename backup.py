#!/usr/bin/env python

import os
import sys
from datetime import datetime, timezone
from dateutils import relativedelta
import argparse
import traceback

DEFAULT_RETENTION_DAYS = os.environ.get('DEFAULT_RETENTION_DAYS', 14)

parser = argparse.ArgumentParser(description='Create EC2 snapshots for kubernetes PVs.')
parser.add_argument('--dont-create-snapshots', dest='create_snapshots', action='store_false', default=True,
                    help='Don\'t clean old snapshots.')
parser.add_argument('--retention-days', dest='retention_days', type=int, default=DEFAULT_RETENTION_DAYS,
                    help='How many days should old snapshots be stored. Older than that will be deleted.')
parser.add_argument('--dont-clean-old-snapshots', dest='clean_old_snapshots', action='store_false', default=True,
                    help='Don\'t clean old snapshots.')
parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False,
                    help='Don\'t save a bit')

args = parser.parse_args()

if args.retention_days < 1:
    args.retention_days = DEFAULT_RETENTION_DAYS
    print(f'Invalid retention days. Reseted to default: {args.retention_days}')

if os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY'):
    print('--> Detected provider AWS')
    from providers.aws import AWS
    provider = AWS()
else:
    print('--> Unable to detected provider')
    sys.exit(0 if args.dry_run else 1)

print('--> Started', datetime.utcnow())

if args.create_snapshots:
    for volume in provider.list_volumes():
        provider.create_snapshot(volume, dry_run=args.dry_run)

if args.clean_old_snapshots:
    clean_before = datetime.utcnow() - relativedelta(days=args.retention_days)
    clean_before = clean_before.replace(tzinfo=timezone.utc)

    print(f'--> Cleaning snapshots older than {args.retention_days} days, before {clean_before}')

    for snapshot in provider.list_snapshots():
        if provider.expired_snapshot(snapshot, clean_before):
            provider.delete_snapshot(snapshot, dry_run=args.dry_run)
