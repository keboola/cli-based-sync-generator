import json

STORAGE_STRUCTURE_DIFF_FILE = 'storage_structure_diff.json'

table_relevant_keys = ['id', 'uri', 'isTyped', 'name', 'definition', 'distributionType', 'distributionKey',
                       'indexType',
                       'indexKey', 'bucket', 'primaryKey', 'transactional', 'columns', 'syntheticPrimaryKeyEnabled',
                       'columnMetadata']
bucket_relevant_keys = ['id', 'uri', 'metadata', 'name', 'stage', 'displayName', 'description', 'backend', 'sharing',
                        'sharingParameters']
column_relevant_keys = ['id', 'columnMetadata', 'primaryKey']


class StorageDiff:

    def __init__(self, source_storage_structure_file, dest_storage_structure_file,
                 storage_structure_diff_file=STORAGE_STRUCTURE_DIFF_FILE):
        self._storage_structure_diff_file = storage_structure_diff_file
        self._source_storage_structure_file = source_storage_structure_file
        self._dest_storage_structure_file = dest_storage_structure_file

    def compare(self):
        diff = []
        src_json = self._read_file(self._source_storage_structure_file)
        dest_json = self._read_file(self._dest_storage_structure_file)
        diff.extend(self._compare_buckets(src_json, dest_json))
        diff.extend(self._compare_tables(src_json, dest_json))
        return self._write_file(diff)

    def _write_file(self, data):
        with open(self._storage_structure_diff_file, 'w') as f:
            json.dump(data, f, indent=4)
        return self._storage_structure_diff_file

    @staticmethod
    def _filter_keys(in_dict, relevant_keys):
        return {k: in_dict.get(k, None) for k in relevant_keys if k in in_dict}

    @staticmethod
    def _compare_object(obj1, obj2, ignore_keys=None):
        if ignore_keys is None:
            ignore_keys = []

        keys_to_compare = set(obj1.keys()).union(set(obj2.keys())) - set(ignore_keys)

        for key in keys_to_compare:
            if key in obj1 and key in obj2:
                if obj1[key] != obj2[key]:
                    return False
            else:
                return False

        return True

    @staticmethod
    def _get_bucket_branch(bucket):
        for metadata in bucket['metadata']:
            if metadata['key'] == 'KBC.createdBy.branch.id':
                return metadata['value']

    @staticmethod
    def _read_file(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    # --------------------  BUCKETS --------------------
    @staticmethod
    def _compose_bucket_event(project, bucket, event):
        bucket_uri = bucket['uri']
        uri_parts = bucket_uri.split('/')
        stack = uri_parts[2]
        bucket_id = uri_parts[-1]
        link = f"https://{stack}/admin/projects/{project}/storage/{bucket_id}"

        return {"event": event,
                "bucket": bucket,
                "link": link}

    def _prepare_bucket_structure(self, full_structure):
        tables = full_structure['tables']
        project = full_structure['project_id']
        default_branch = [b['id'] for b in full_structure['dev-branches'] if b['isDefault']][0]

        structure = {}
        for table in tables:
            branch = self._get_bucket_branch(table['bucket'])
            if branch is None or branch == default_branch:
                structure[table['bucket']['id']] = self._filter_keys(table['bucket'], bucket_relevant_keys)
        return structure, project

    def _compare_buckets(self, src_structure, dest_structure):

        events = []

        src_buckets, src_project = self._prepare_bucket_structure(src_structure)
        dest_buckets, dest_project = self._prepare_bucket_structure(dest_structure)

        # Detect added and changed buckets
        for bucket_id, src_bucket in src_buckets.items():
            if bucket_id not in dest_buckets:
                events.append(self._compose_bucket_event(src_project, src_bucket, "ADD_BUCKET"))
                if src_bucket['sharing']:
                    events.append(self._compose_bucket_event(src_project, src_bucket, "SHARE_BUCKET"))
            else:
                dest_bucket = dest_buckets[bucket_id]

                if src_bucket['sharing'] != dest_bucket['sharing']:
                    events.append(self._compose_bucket_event(src_project, src_bucket, "SHARE_BUCKET"))
                if self._compare_object(src_bucket, dest_bucket, ignore_keys=['sharing', 'idBranch']):
                    events.append(self._compose_bucket_event(src_project, src_bucket, "MODIFY_BUCKET"))

        # Detect removed buckets
        for bucket_id, dest_bucket in dest_buckets.items():
            if bucket_id not in src_buckets:
                events.append(self._compose_bucket_event(dest_project, dest_bucket, "DROP_BUCKET"))

        return events

    # --------------------  TABLES --------------------

    @staticmethod
    def _compose_table_event(project, table, event):
        table_uri = table['uri']
        uri_parts = table_uri.split('/')
        stack = uri_parts[2]
        bucket_id = uri_parts[-2]
        table_id = uri_parts[-1]
        link = f"https://{stack}/admin/projects/{project}/storage/{bucket_id}/{table_id}"

        return {"event": event,
                "table": table,
                "link": link}

    def _prepare_table_structure(self, full_structure):
        tables = full_structure['tables']
        project = full_structure['project_id']
        default_branch = [b['id'] for b in full_structure['dev-branches'] if b['isDefault']][0]

        structure = {}
        for table in tables:
            branch = self._get_bucket_branch(table['bucket'])
            if branch is None or branch == default_branch:
                structure[table['id']] = self._filter_keys(table, table_relevant_keys)
        return structure, project

    def _compare_tables(self, src_structure, dest_structure):
        events = []

        src_tables, src_project = self._prepare_table_structure(src_structure)

        dest_tables, dest_project = self._prepare_table_structure(dest_structure)

        # Detect added and changed tables
        for table_id, src_table in src_tables.items():

            if table_id not in dest_tables:
                src_table['bucket'] = self._filter_keys(src_table['bucket'], bucket_relevant_keys)
                events.append(self._compose_table_event(src_project, src_table, "ADD_TABLE"))
            else:
                dest_table = dest_tables[table_id]
                events.extend(self._compare_table_details(src_table, dest_table, src_project, dest_project))

        # Detect removed tables
        for table_id, dest_table in dest_tables.items():
            if table_id not in src_tables:
                events.append(self._compose_table_event(src_project, dest_table, "DROP_TABLE"))

        return events

    @staticmethod
    def _compose_column_event(project, table, event, column=None, primary_key=None, metadata=None):
        table_uri = table['uri']
        uri_parts = table_uri.split('/')
        stack = uri_parts[2]
        bucket_id = uri_parts[-2]
        table_id = uri_parts[-1]
        link = f"https://{stack}/admin/projects/{project}/storage/{bucket_id}/{table_id}"

        event_struct = {"event": event,
                        "table_id": table_id,
                        "link": link}
        if column:
            event_struct["column"] = column
        elif primary_key:
            event_struct["primary_key"] = primary_key
        elif metadata:
            event_struct["metadata"] = metadata

        return event_struct

    def _compare_table_details(self, src_table, dest_table, src_project, dest_project):
        events = []

        # Compare columns
        src_columns = set(self._filter_keys(src_table['columns'], column_relevant_keys))
        dest_columns = set(self._filter_keys(dest_table['columns'], column_relevant_keys))

        added_columns = src_columns - dest_columns
        removed_columns = dest_columns - src_columns

        for column in added_columns:
            events.append(self._compose_column_event(src_project, src_table, "ADD_COLUMN", column=column))
        for column in removed_columns:
            events.append(self._compose_column_event(src_project, src_table, "DROP_COLUMN", column=column))

        # Compare primary keys
        if src_table['primaryKey'] != dest_table['primaryKey']:
            if not dest_table['primaryKey']:
                events.append(self._compose_column_event(src_project, src_table, "ADD_PRIMARY_KEY",
                                                         primary_key=src_table['primaryKey']))
            elif not src_table['primaryKey']:
                events.append(self._compose_column_event(src_project, src_table, "DROP_PRIMARY_KEY"))

        # Compare column metadata
        if src_table['columnMetadata'] != dest_table['columnMetadata']:
            events.append(self._compose_column_event(src_project, src_table, "EDIT_COLUMNS_METADATA",
                                                     metadata={"src_metadata": src_table['columnMetadata'],
                                                               "dest_metadata": dest_table['columnMetadata']}))

        return events
