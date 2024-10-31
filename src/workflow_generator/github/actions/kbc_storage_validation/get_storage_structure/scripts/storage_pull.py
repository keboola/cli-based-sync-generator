import json
import os
import requests
import argparse


class StoragePull:
    def __init__(self, host, project_id, token, destination_file):
        self._base = self._base_uni(host)
        self._project_id = project_id
        self._token = token
        self._head = {'X-StorageApi-Token': self._token}
        self._destination_file = destination_file

    @staticmethod
    def _base_uni(host):
        if not host.startswith('https://'):
            return ''.join(['https://', host])
        return host

    def _get_branches(self):
        branches = requests.get(url=''.join([self._base, '/v2/storage/dev-branches']), headers=self._head)
        return branches.json()

    def _get_buckets(self):
        buckets = requests.get(url=''.join([self._base, '/v2/storage/buckets']), headers=self._head,
                               params={'include': 'metadata'})
        return buckets.json()

    def _get_tables(self, bucket_id):
        tables = requests.get(url=''.join([self._base, f'/v2/storage/buckets/{bucket_id}/tables']), headers=self._head,
                              params={'include': 'columns,metadata,columnMetadata'})
        return tables.json()

    def pull(self):
        # create whole tree if not exists
        if not os.path.exists(os.path.dirname(self._destination_file)):
            os.makedirs(os.path.dirname(self._destination_file))

        buckets = self._get_buckets()
        all_tables = []
        for bucket in buckets:
            bucket_tables = self._get_tables(bucket.get('id'))
            for table in bucket_tables:
                table['bucket'] = bucket
            all_tables.extend(bucket_tables)

        storage_structure = {'project_id': self._project_id, 'dev-branches': self._get_branches(), 'tables': all_tables}

        with open(self._destination_file, 'w') as f:
            json.dump(storage_structure, f, indent=4)

        print(f'Storage structure saved to {self._destination_file}')
        return self._destination_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pull storage structure from KBC')
    parser.add_argument('--host', required=True, help='KBC host')
    parser.add_argument('--project', required=True, help='KBC project id')
    parser.add_argument('--token', required=True, help='KBC token')
    parser.add_argument('--destination-file', required=True, help='Destination file')
    args = parser.parse_args()
    StoragePull(args.host, args.project, args.token, args.destination_file).pull()
