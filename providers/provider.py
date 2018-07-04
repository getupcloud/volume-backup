class Provider:
    def get_tag_value(self, tags, key):
        raise NotImplemented

    def list_volumes(self):
        raise NotImplemented

    def create_snapshot(self, volume, dry_run=False):
        raise NotImplemented

    def list_snapshots(self):
        raise NotImplemented

    def delete_snapshot(self, snapshot, dry_run=False):
        raise NotImplemented

    def expired_snapshot(self, snapshot, clean_before):
        raise NotImplemented
