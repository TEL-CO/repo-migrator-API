from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
import requests
import base64

class Azure:
    def __init__(self, organization, personal_access_token):
        self.organization = organization
        self.base_url = f"https://dev.azure.com/{organization}"
        self.auth_header = {
            'Authorization': 'Basic ' + base64.b64encode(f":{personal_access_token}".encode()).decode(),
            'Content-Type': 'application/json'
        }

    def get_projects(self):
        url = f"{self.base_url}/_apis/projects?api-version=7.1-preview.4"
        response = requests.get(url, headers=self.auth_header)
        response.raise_for_status()
        return response.json()['value']

    def get_all_repositories(self):
        all_repos = []
        projects = self.get_projects()

        for project in projects:
            url = f"{self.base_url}/{project['id']}/_apis/git/repositories?api-version=7.1-preview.1"
            response = requests.get(url, headers=self.auth_header)
            response.raise_for_status()
            repos = response.json()['value']
            all_repos.extend(repos)

        return all_repos

    def create_repository(self, project, token, repo_name):
        url = f"https://dev.azure.com/{self.organization}/{project}/_apis/git/repositories?api-version=6.0"
        headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }
        data = {'name': repo_name}
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()['remoteUrl']