import json
import logging
import os

import requests
import argparse


class VaultPull:
    def __init__(self, host, token, branch, destination_file):
        self._base = self._base_uni(host)
        self._token = token
        self._head = {'X-StorageApi-Token': self._token}
        self._branch = self._get_branch(branch)
        self._destination_file = destination_file

    @staticmethod
    def _base_uni(host):
        if not host.startswith('https://'):
            return ''.join(['https://', host])
        return host

    def _get_branch(self, branch):
        # if branch is digit
        if branch.isdigit():
            logging.info(f'Branch {branch} is digit, using it as branch id')
            return branch
        else:
            logging.info(f'Branch {branch} is empty or is not digit, get default branch from KBC')
            branches = requests.get(url=''.join([self._base, '/v2/storage/dev-branches/']), headers=self._head)
            default_branch = [b['id'] for b in branches.json() if b['isDefault']][0]
            logging.info(f'Using default branch ({default_branch})')
            return default_branch

    def _get_vault_keys(self):
        url = self._base.replace('connection', 'vault')
        keys = requests.get(url=''.join([url, '/variables/scoped/branch/', str(self._branch)]), headers=self._head)
        return [k['key'] for k in keys.json()]

    def _save_vault_structure(self, structure):
        # create whole tree if not exists
        if not os.path.exists(os.path.dirname(self._destination_file)):
            os.makedirs(os.path.dirname(self._destination_file))

        with open(self._destination_file, 'w') as f:
            json.dump(structure, f, indent=4)

        print(f'Storage structure saved to {self._destination_file}')
        return self._destination_file

    def pull(self):
        return self._save_vault_structure(self._get_vault_keys())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pull vault structure from KBC')
    parser.add_argument('--host', required=True, help='KBC host')
    parser.add_argument('--token', required=True, help='KBC token')
    parser.add_argument('--branch', required=True, help='KBC branch')
    parser.add_argument('--destination-file', required=True, help='Destination file')
    args = parser.parse_args()
    VaultPull(args.host, args.token, args.branch, args.destination_file).pull()
