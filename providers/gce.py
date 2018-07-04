import os
import sys
import json
import traceback
from apiclient.discovery import build
from dateutil.parser import parse
from .provider import Provider

class GCE(Provider):

    def __init__(self, project_id, zone):
        self.project_id = project_id
        self.zone = zone
        service = build('compute', 'v1')
        self.disks = service.disks()
        self.snapshots = service.snapshots()

    def get_tag_value(self, tags, key):
        return tags.get(key)

    def list_volumes(self):
        print(f'--> Listing volumes from project {self.project_id}, zone {self.zone}')

        volumes = [
            disk for disk in self.disks.list(project=self.project_id, zone=self.zone).execute()['items']
            if disk['name'].startswith('kubernetes-dynamic-pvc-')
        ]

        print(f'--> Found {len(volumes)} volume(s)')

        return volumes

    def create_snapshot(self, volume, dry_run=False):
        tags = json.loads(volume['description'])

        ignore = self.get_tag_value(tags, 'snapshot')
        if ignore in [ 'false', 'False', 'no', '0' ]:
            print(f'--> Ignoring snapshot for volume {volume["name"]}')
            return

        namespace = self.get_tag_value(tags, 'kubernetes.io/created-for/pvc/namespace')
        pvc = self.get_tag_value(tags, 'kubernetes.io/created-for/pvc/name')
        name = f'{namespace}-{pvc}'
        labels = {
            'created-by': 'automated-backup',
            'name': name,
            'pv': self.get_tag_value(tags, 'kubernetes.io/created-for/pv/name'),
            'pvc': pvc,
            'namespace': namespace

        }
        print(f'--> Creating snapshot for volume {volume["name"]} -> ', end='', flush=True)

        if dry_run:
            print('(not created by user request)')
            return {}

        snapshot = self.disks.createSnapshot(
                    project=self.project_id,
                    zone=self.zone,
                    disk=volume['name'],
                    body={'name': name, 'labels': labels}).execute()
        print(f'{snapshot["name"]} [{volume["sizeGb"]}Gb] {labels}')
        return snapshot

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

