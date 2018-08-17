class Provider:
    def create_snapshot(self, pv, dry_run=False):
        raise NotImplementedError

    def list_snapshots(self):
        raise NotImplementedError

    def delete_snapshot(self, snapshot, dry_run=False):
        raise NotImplementedError

    def expired_snapshot(self, snapshot, clean_before):
        raise NotImplementedError
