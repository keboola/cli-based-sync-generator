import json

STORAGE_STRUCTURE_DIFF_FILE = 'storage_structure_diff.json'

table_relevant_keys = ['id', 'isTyped', 'name', 'definition', 'distributionType', 'distributionKey', 'indexType',
                       'indexKey', 'bucket', 'primaryKey', 'transactional', 'columns', 'syntheticPrimaryKeyEnabled',
                       'columnMetadata']
bucket_relevant_keys = ['id', 'name', 'stage', 'displayName', 'description', 'backend', 'sharing', 'sharingParameters']
column_relevant_keys = ['id', 'columnMetadata', 'primaryKey']


class StorageDiff:
    def __init__(self, source_storage_structure_file, dest_storage_structure_file,
                 storage_structure_diff_file=STORAGE_STRUCTURE_DIFF_FILE):
        self.relevant_changes = None
        self._diff = None
        self.storage_structure_diff_file = storage_structure_diff_file
        self.source_storage_structure_file = source_storage_structure_file
        self.dest_storage_structure_file = dest_storage_structure_file

    def compare(self):
        diff = []
        src_json = self._read_file(self.source_storage_structure_file)
        dest_json = self._read_file(self.dest_storage_structure_file)
        diff.extend(self._compare_buckets(src_json, dest_json))
        diff.extend(self._compare_tables(src_json, dest_json))
        return self._write_file(diff)

    @staticmethod
    def _filter_keys(in_dict, relevant_keys):
        return {k: in_dict.get(k, None) for k in relevant_keys if k in in_dict}

    def _compare_buckets(self, src_structure, dest_structure):

        events = []

        src_buckets = {table['bucket']['id']: self._filter_keys(table['bucket'], bucket_relevant_keys) for table in
                       src_structure}
        dest_buckets = {table['bucket']['id']: self._filter_keys(table['bucket'], bucket_relevant_keys) for table in
                        dest_structure}

        # Detect added and changed buckets
        for bucket_id, src_bucket in src_buckets.items():
            if bucket_id not in dest_buckets:
                events.append({"event": "ADD_BUCKET", "bucket": src_bucket})
                if src_bucket['sharing']:
                    events.append({"event": "SHARE_BUCKET", "bucket": src_bucket})
            else:
                dest_bucket = dest_buckets[bucket_id]
                if src_bucket != dest_bucket:
                    # TODO better recognise changing! Especially for sharing
                    events.append({"event": "MODIFY_BUCKET", "bucket": src_bucket})

        # Detect removed buckets
        for bucket_id, dest_bucket in dest_buckets.items():
            if bucket_id not in src_buckets:
                events.append({"event": "DROP_BUCKET", "bucket": dest_bucket})

        return events

    def _compare_tables(self, src_structure, dest_structure):
        events = []

        dev_table_dict = {table['id']: self._filter_keys(table, table_relevant_keys) for table in src_structure}
        prod_table_dict = {table['id']: self._filter_keys(table, table_relevant_keys) for table in dest_structure}

        # Detect added and changed tables
        for table_id, dev_table in dev_table_dict.items():
            if table_id not in prod_table_dict:
                dev_table['bucket'] = self._filter_keys(dev_table['bucket'], bucket_relevant_keys)
                events.append(
                    {"event": "ADD_TABLE", "table": dev_table})
            else:
                prod_table = prod_table_dict[table_id]
                events.extend(self._compare_table_details(dev_table, prod_table))

        # Detect removed tables
        for table_id, prod_table in prod_table_dict.items():
            if table_id not in dev_table_dict:
                events.append({"event": "DROP_TABLE", "table": prod_table})

        return events

    def _compare_table_details(self, dev_table, prod_table):
        events = []

        # Compare columns
        dev_columns = set(self._filter_keys(dev_table['columns'], column_relevant_keys))
        prod_columns = set(self._filter_keys(prod_table['columns'], column_relevant_keys))

        added_columns = dev_columns - prod_columns
        removed_columns = prod_columns - dev_columns

        for column in added_columns:
            events.append({"event": "ADD_COLUMN", "table_id": dev_table['id'], "column": column})
        for column in removed_columns:
            events.append({"event": "DROP_COLUMN", "table_id": dev_table['id'], "column": column})

        # Compare primary keys
        if dev_table['primaryKey'] != prod_table['primaryKey']:
            if not prod_table['primaryKey']:
                events.append(
                    {"event": "ADD_PRIMARY_KEY", "table_id": dev_table['id'], "primary_key": dev_table['primaryKey']})
            elif not dev_table['primaryKey']:
                events.append({"event": "DROP_PRIMARY_KEY", "table_id": dev_table['id']})

        # Compare column metadata
        if dev_table['columnMetadata'] != prod_table['columnMetadata']:
            events.append({"event": "EDIT_COLUMNS_METADATA", "table_id": dev_table['id'],
                           "dev_metadata": dev_table['columnMetadata'], "prod_metadata": prod_table['columnMetadata']})

        return events

    def _write_file(self, data):
        with open(self.storage_structure_diff_file, 'w') as f:
            json.dump(data, f, indent=4)
        return self.storage_structure_diff_file

    @staticmethod
    def _read_file(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
