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

    def create_snapshot(self, pv, dry_run=False):
        print(f'--> Creating snapshot for PV {pv.metadata.name}', end='', flush=True)

        ts = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        description = f'{pv.metadata.name}-{ts}'
        aws_volume_id = pv.spec.aws_elastic_block_store.volume_id.split('/')[-1]

        print(f' EBS {aws_volume_id} -> ', end='', flush=True)

        if dry_run:
            print('(not created by user request)')
            return

        ret = {
            'err': None,
            'snapshot': None,
            'pv': pv,
        }
        try:
            snapshot = self.ec2.create_snapshot(VolumeId=aws_volume_id, Description=description)
            ret['snapshot'] = snapshot
            print(f'{snapshot["SnapshotId"]} [{snapshot["VolumeSize"]}Gi] {snapshot["Description"]}')
            self.ec2.create_tags(Resources=[snapshot["SnapshotId"]], Tags=[{'Key':'CreatedBy', 'Value':'AutomatedBackup'}])
        except Exception as ex:
            traceback.print_exc()
            ret['err'] = str(ex)

        return ret

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
