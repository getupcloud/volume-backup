import os
import boto3
import traceback
from datetime import datetime
from .provider import Provider

class AWS(Provider):

    def __init__(self):
        self.region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION')
        self.iam = boto3.client('iam')
        self.ec2 = boto3.client('ec2')
        self.user = self._get_user()

    def _get_user(self):
        print(f'--> Retrieving user info')
        iam_user = self.iam.get_user()
        return iam_user['User']

    def get_tag_value(self, tags, key):
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']

    def list_volumes(self):
        print(f'--> Listing volumes from region {self.region}')

        filters = [
            {'Name':'tag:Name','Values':['kubernetes-dynamic-pvc-*']},
            {'Name':'status','Values':['available', 'in-use']},
        ]
        volumes = self.ec2.describe_volumes(Filters=filters)['Volumes']

        print(f'--> Found {len(volumes)} volume(s)')

        return volumes

    def create_snapshot(self, volume, dry_run=False):
        ignore = self.get_tag_value(volume['Tags'], 'snapshot')
        if ignore in [ 'false', 'False', 'no', '0' ]:
            print(f'--> Ignoring snapshot for volume {volume["VolumeId"]}')
            return

        pv = self.get_tag_value(volume['Tags'], 'kubernetes.io/created-for/pv/name')
        pvc = self.get_tag_value(volume['Tags'], 'kubernetes.io/created-for/pvc/name')
        namespace = self.get_tag_value(volume['Tags'], 'kubernetes.io/created-for/pvc/namespace')
        ts = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        description = f'backup-{ts}-{namespace}-{pvc}-{pv}'

        print(f'--> Creating snapshot for volume {volume["VolumeId"]} -> ', end='', flush=True)

        if dry_run:
            print('(not created by user request)')
            return {}

        snapshot = self.ec2.create_snapshot(VolumeId=volume['VolumeId'], Description=description)
        print(f'{snapshot["SnapshotId"]} [{snapshot["VolumeSize"]}Gi] {snapshot["Description"]}')
        self.ec2.create_tags(Resources=[snapshot["SnapshotId"]], Tags=[{'Key':'CreatedBy', 'Value':'AutomatedBackup'}])
        return snapshot

    def list_snapshots(self):
        print(f'--> Listing snapshots from region {self.region}')

        snapshots = self.ec2.describe_snapshots(
                        Filters=[{'Name':'tag:CreatedBy','Values':['AutomatedBackup']}],
                        OwnerIds=[self.user['Arn'].split(':')[4]])['Snapshots']

        print(f'--> Found {len(snapshots)} snapshot(s)')
        return snapshots

    def delete_snapshot(self, snapshot, dry_run=False):
        print(f'--> Deleting expired snapshot {snapshot["SnapshotId"]} [{snapshot["VolumeSize"]}Gi] Created {snapshot["StartTime"]} {snapshot["Description"]}')

        if dry_run:
            print('(not deleted by user request)')
            return

        try:
            self.ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
        except:
            traceback.print_exc()

    def expired_snapshot(self, snapshot, clean_before):
        return snapshot['State'] == 'completed' and snapshot['StartTime'] < clean_before
