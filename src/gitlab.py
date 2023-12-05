import requests
import re
import json

class GitLab:
    def __init__(self, token):
        self.base_url = "https://gitlab.com/api/v4"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.url = None
        self.pagination = None

    def get_all_repositories(self, group_id, pagination=False, per_page=20, order_by='id', sort='asc'):
        all_repositories = []
        all_links = []
        last_repository_id = 0

        groups_to_process = [group_id] + [subgroup['id'] for subgroup in self.get_subgroups(group_id)]
        for group in groups_to_process:
            last_repository_id = 0
            if pagination is True:  # Fetch only the first page with pagination links
                self.url = (f"{self.base_url}/groups/{group}/projects?per_page={per_page}"
                            f"&order_by={order_by}&sort={sort}&id_after={last_repository_id}")

                response = requests.get(self.url, headers=self.headers)
                if response.status_code == 200:
                    repositories = response.json()
                    all_repositories.extend(repositories)
                    link_header = response.headers.get('link', None)
                    all_links = self.convert_links_to_json_array(link_header)
                else:
                    print(f"Failed to fetch repositories: {response.status_code}")
                return {"repositories": all_repositories, "headers": all_links}

            else:  # Fetch all repositories without pagination
                while True:
                    self.url = (f"{self.base_url}/groups/{group}/projects?per_page={per_page}"
                                f"&order_by={order_by}&sort={sort}&id_after={last_repository_id}")
                    print(self.url)
                    response = requests.get(self.url, headers=self.headers)
                    if response.status_code == 200:
                        repositories = response.json()
                        if not repositories:
                            break  # Exit the loop if no more repositories are returned

                        all_repositories.extend(repositories)
                        last_repository_id = repositories[-1]['id']
                    else:
                        print(f"Failed to fetch repositories: {response.status_code}")
                        break

        return {"repositories": all_repositories}
    
    #@todo make it recursive
    def get_subgroups(self, group_id):
        subgroups = []
        url = f"{self.base_url}/groups/{group_id}/subgroups?per_page=100"  # Adjust per_page as needed
        while url:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                subgroups.extend(response.json())
                url = self.extract_next_page_url(response.headers.get('link', None))
            else:
                print(f"Failed to fetch subgroups: {response.status_code}")
                break
        return subgroups
    
    def extract_next_page_url(self, link_header):
        if link_header:
            links = link_header.split(',')
            for link in links:
                if 'rel="next"' in link:
                    next_page_url = link.split(';')[0].strip('<> ')
                    return next_page_url
        return None

    def replace_domain(self, url, new_domain="localhost:5000"):
        return url.replace("gitlab.com", new_domain)

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

    def proxy_request(self, method, path, headers, data):
        # Construct the new URL for GitLab
        new_url = f"https://gitlab.com/api/v4/{path}"

        # Forward the request to GitLab
        method = method.lower()
        headers = {key: value for key, value in headers.items() if key.lower() != 'host'}

        # Make the request to GitLab
        response = requests.request(method, new_url, headers=headers, data=data, allow_redirects=False)
        return response
    
    def create_repository(self, repo_name, token):
        url = "https://gitlab.com/api/v4/projects"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        data = {'name': repo_name}
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()['http_url_to_repo']
