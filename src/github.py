import requests
import re
import json

class GitHub:
    def __init__(self, token):
        self.base_url = "https://api.github.com"
        self.token = token
        self.headers = {"Authorization": f"token {token}"}
        self.url = None  # URL will be set in get_all_repositories


    def get_all_repositories(self, organization, pagination=False, per_page=20, page=1):
        all_repositories = []
        all_links = []
        self.url = f"{self.base_url}/orgs/{organization}/repos?per_page={per_page}&page={page}"
        
        if pagination:  # Fetch only the first page with pagination links
            response = requests.get(self.url, headers=self.headers)
            print(response.headers)
            if response.status_code == 200:
                all_repositories = response.json()
                link_header = response.headers.get('link', None)
                all_links = self.convert_links_to_json_array(link_header)
            else:
                print(f"Failed to fetch repositories: {response.status_code}")
            return {"repositories": all_repositories, "headers": all_links}

        else:  # Fetch all repositories without pagination
            while self.url:
                response = requests.get(self.url, headers=self.headers)
                print(response.headers)
                if response.status_code == 200:
                    repositories = response.json()
                    if not repositories:
                        break  # Exit the loop if no more repositories are returned

                    all_repositories.extend(repositories)
                    next_page_url = self.extract_next_page_url(response.headers.get('link', None))
                    self.url = next_page_url
                else:
                    print(f"Failed to fetch repositories: {response.status_code}")
                    break
            return {"repositories": all_repositories}

    def extract_next_page_url(self, link_header):
        if link_header:
            links = link_header.split(',')
            for link in links:
                if 'rel="next"' in link:
                    next_page_url = link.split(';')[0].strip('<> ')
                    return next_page_url
        return None

    def create_repository(self, repo_name, token, organization="TEL-CO"):
        url = f"https://api.github.com/orgs/{organization}/repos" if organization else "https://api.github.com/user/repos"
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        data = {
            'name': repo_name,
            'private': True  # Set to True if you want to create a private repository
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()['clone_url']
        
    def convert_links_to_json_array(self, link_header):
        # Pattern to find URLs and their relational tags
        # link_header = self.rewrite_urls_to_localhost(link_header)
        url_pattern = re.compile(r'<(https?://[^>]+)>; rel="([^"]+)"')

        # Find all URLs and their relational tags
        urls = url_pattern.findall(link_header)

        # Construct a list of dictionaries
        json_array = [{"url": self.replace_domain(url), "rel": rel} for url, rel in urls]

        # Convert the list into a JSON formatted string
        json_str = json.dumps(json_array, indent=4)
        return json_array
