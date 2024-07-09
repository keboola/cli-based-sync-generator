import logging
import os
import json
import argparse

secure_keys = []


def check_json_keys_and_values(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"Invalid JSON or encoding: {json_file}")
        return

    def find_keys(obj, path=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f'{path}.{k}' if path else k
                if k.startswith('#'):
                    if isinstance(v, str):
                        is_vault_value: bool = True
                        if (v.startswith('KBC::ComponentSecure::')
                                or v.startswith('KBC::ProjectSecure::')
                                or v.startswith('KBC::ConfigSecure::')):
                            is_vault_value = False
                        # other value types is not possible because it is checked by CLI
                        secure_keys.append(
                            {'is_vault_value': is_vault_value, 'file': json_file, 'key': new_key, 'value': v})
                find_keys(v, new_key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_keys(item, f'{path}[{i}]')

    find_keys(data)


def write_encrypted(secure_encrypted):
    for key in secure_encrypted:
        print(f"{key['file']} -> {key['key']}")
    print("The configurations above contain a secure value not in the vault!")
    exit(-1)


def main(target_dir):
    logging.info(f"Checking JSON keys and values in {target_dir}")
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.json'):
                check_json_keys_and_values(os.path.join(root, file))
    if secure_keys:
        write_encrypted([key for key in secure_keys if not key['is_vault_value']])
    else:
        print("No secure values found in the configurations - validation is ok")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check JSON keys and values in a directory.')
    parser.add_argument('target_dir', help='The target directory to search for JSON files')

    args = parser.parse_args()

    main(args.target_dir)
