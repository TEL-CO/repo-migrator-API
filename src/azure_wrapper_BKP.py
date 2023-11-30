from azure.devops.connection import Connection
from azure.devops.v7_1.git.models import GitRepositoryCreateOptions
from azure.devops.v7_1.git.git_client import GitClient  # Corrected path

from msrest.authentication import BasicAuthentication

class Azure:
    def __init__(self, token, organization):
        self.organization = organization
        self.credentials = BasicAuthentication('', token)
        try:
            self.connection = Connection(base_url=f"https://dev.azure.com/{organization}", creds=self.credentials)
            self.git_client = self.connection.clients.get_git_client()
            print("Successfully connected to Azure DevOps")
        except Exception as e:
            print(f"Error connecting to Azure DevOps: {e}")
            raise

    def get_all_repositories(self, pagination=False, per_page=50, page=1):
        repositories = []
        try:
            criteria = self.git_client.get_repositories(self.organization, top=per_page, skip=(page - 1) * per_page)
            repositories = list(criteria)

            if pagination:
                return repositories[:per_page]

            while len(criteria) == per_page:
                page += 1
                criteria = self.git_client.get_repositories(self.organization, top=per_page, skip=(page - 1) * per_page)
                repositories.extend(criteria)

            print("Successfully fetched repositories")
        except Exception as e:
            print(f"Error fetching repositories: {e}")
            raise

        return repositories

    def create_repository(self, repo_name, project):
        try:
            create_options = GitRepositoryCreateOptions(name=repo_name, project=project)
            repo = self.git_client.create_repository(create_options, project)
            print(f"Repository '{repo_name}' created successfully")
            return repo
        except Exception as e:
            print(f"Error creating repository '{repo_name}': {e}")
            raise