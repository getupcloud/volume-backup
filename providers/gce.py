import os
import sys
import json
import traceback
from googleapiclient.discovery import build
from datetime import datetime
from dateutil.parser import parse
from .provider import Provider

class GCE(Provider):

    def __init__(self, project_id, zone):
        self.project_id = project_id
        self.zone = zone
        service = build('compute', 'v1')
        self.disks = service.disks() # pylint: disable=E1101
        self.snapshots = service.snapshots() # pylint: disable=E1101

    def create_snapshot(self, pv, dry_run=False):
        print(f'--> Creating snapshot for PV {pv.metadata.name}', end='', flush=True)

        ts = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        name = f'{pv.metadata.name}-{ts}'
        gce_pd_name = pv.spec.gce_persistent_disk.pd_name

        print(f' PD {gce_pd_name} -> ', end='', flush=True)

        labels = {
            'created-by': 'automated-backup',
            'name': name,
            'pv': pv.metadata.name,
        }

        if dry_run:
            print('(not created by user request)')
            return

        ret = {
            'err': None,
            'snapshot': None,
            'pv': pv,
        }

        try:
            snapshot = self.disks.createSnapshot(
                project=self.project_id,
                zone=self.zone,
                disk=gce_pd_name,
                body={'name': name, 'labels': labels}).execute()
            ret['snapshot'] = snapshot
            print(f'{snapshot["name"]} [{pv.spec.capacity.storage}] {labels}')
        except Exception as ex:
            traceback.print_exc()
            ret['err'] = str(ex)

        return ret

    def list_snapshots(self):
        print(f'--> Listing snapshots from project {self.project_id}, zone {self.zone}')

        snapshots = []
        request = self.snapshots.list(project=self.project_id, filter='labels.created-by = "automated-backup"')
        while request is not None:
            response = request.execute()
            snapshots.extend(response['items'])
            request = self.snapshots.list_next(previous_request=request, previous_response=response)

        print(f'--> Found {len(snapshots)} snapshot(s)')
        return snapshots

    def delete_snapshot(self, snapshot, dry_run=False):
        print(f'--> Deleting expired snapshot {snapshot["name"]} [{snapshot["storageBytes"]} bytes] Created {snapshot["creationTimestamp"]} {snapshot["labels"]}')

        if dry_run:
            print('(not deleted by user request)')
            return

        try:
            self.snapshots.delete(project=self.project_id, snapshot=snapshot['name']).execute()
        except:
            traceback.print_exc()

    def expired_snapshot(self, snapshot, clean_before):
        return snapshot['status'] == 'READY' and parse(snapshot['creationTimestamp']) < clean_before

