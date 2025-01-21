import requests
from typing import Optional, Tuple, List, Dict, Any

def validate_token(stack: str, token: str) -> Optional[Tuple[str, str, str, List[Dict[str, Any]]]]:
    """
    Validate Keboola API token and return project details.
    
    Returns:
        Tuple of (project_id, kbc_project_name, project_link, project_branches) or None if validation fails
    """
    header = {'X-StorageApi-Token': token}
    url = f'https://{stack}/v2/storage/tokens/verify'
    
    try:
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            project_id = response.json().get('owner', {}).get('id')
            kbc_project_name = response.json().get('owner', {}).get('name')
            project_link = f'https://{stack}/admin/projects/{project_id}'
            project_branches = get_branches(stack, token)
            return project_id, kbc_project_name, project_link, project_branches
    except Exception:
        return None
    
    return None

def get_branches(stack: str, token: str) -> List[Dict[str, Any]]:
    """Get available branches for a project."""
    headers = {'X-StorageApi-Token': token}
    url = f'https://{stack}/v2/storage/dev-branches/'
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return [
                {
                    'id': branch.get('id'),
                    'name': branch.get('name'),
                    'isDefault': branch.get('isDefault')
                }
                for branch in response.json()
            ]
    except Exception:
        return []
    
    return []
