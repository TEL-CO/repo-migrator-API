from fastapi import FastAPI, HTTPException, Body, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from typing import Any, Optional
from git import Repo, GitCommandError
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from functools import wraps

import src.github as GitHub
import src.gitlab as GitLab
import src.azure_wrapper as Azure

import requests
import os
import shutil
import subprocess

app = FastAPI()
origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
Base = declarative_base()

class Repository(Base):
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    gitlab_id = Column(Integer, unique=True)
    name = Column(String, index=True)
    description = Column(String)
    path = Column(String)
    created_at = Column(String)
    default_branch = Column(String)
    web_url = Column(String)
    ssh_url_to_repo = Column(String)
    http_url_to_repo = Column(String)
    last_activity_at = Column(String)
    platform = Column(String)

class RepositoryObject(BaseModel):
    repo_name: str
    source_repo_url: str
    organization: str = None
    project: str = None

#decorator to save repositories to database
def save_repositories_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if 'indexing' parameter is provided and is True
        indexing = kwargs.get('indexing', False)
        if not indexing:
            return func(*args, **kwargs)

        # Proceed with the original functionality if indexing is True
        response = func(*args, **kwargs)
        repositories = response.get('repositories', []) if isinstance(response, dict) else []

        if repositories:
            session = Session()
            for repo in repositories:
                db_repo = Repository(
                    gitlab_id=repo.get('id'),
                    name=repo.get('name'),
                    description=repo.get('description'),
                    path=repo.get('path'),
                    created_at=repo.get('created_at'),
                    default_branch=repo.get('default_branch'),
                    web_url=repo.get('web_url'),
                    ssh_url_to_repo=repo.get('ssh_url_to_repo'),
                    http_url_to_repo=repo.get('http_url_to_repo'),
                    last_activity_at=repo.get('last_activity_at'),
                    platform=kwargs.get('platform', 'unknown')
                )
                session.add(db_repo)
            session.commit()

        return response
    return wrapper

class RepoMigrator:
    def __init__(self):
        self.gitlab_token = os.getenv('GITLAB_TOKEN')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.azure_token = os.getenv('AZURE_TOKEN')
        self.gitlab_group_id = os.getenv('GITLAB_GROUP_ID')
        self.github_organization = os.getenv('GITHUB_ORGANIZATION')
        self.azure_organization = os.getenv('AZURE_ORGANIZATION')
        self.github = GitHub.GitHub(self.github_token)
        self.gitlab = GitLab.GitLab(self.gitlab_token)
        self.azure = Azure.Azure(self.azure_organization, self.azure_token)

    @save_repositories_decorator
    def get_all_repositories(self, platform, per_page, pagination = False, indexing = False):
        if platform.lower() == "gitlab":
            return self.gitlab.get_all_repositories(self.gitlab_group_id, pagination, per_page) 
        elif platform.lower() == "github":
            return self.github.get_all_repositories(self.github_organization, pagination, per_page)
        elif platform.lower() == "azure":
            return self.azure.get_all_repositories()
        else:
            raise ValueError("Unsupported platform")

    def move_repository(self, source_repo_url, target_platform, repo_name, project=''):
        local_dir = f"/tmp/{repo_name}"
        
        # Create a new repository on the target platform
        if target_platform.lower() == "github":
            new_repo_url = self.github.create_repository(repo_name, self.github_token)
        elif target_platform.lower() == "azure":
            new_repo_url = self.azure.create_repository(repo_name, self.azure_token, project)
        elif target_platform.lower() == "gitlab":
            new_repo_url = self.gitlab.create_repository(repo_name, self.gitlab_token)
        else:
            raise ValueError("Unsupported target platform")

        subprocess.run(["git", "config", "--global", "credential.helper", "cache --timeout=300"])
        # Clone the repository from the source
        repo = Repo.clone_from(source_repo_url, local_dir, mirror=True)

        # Change the remote URL to the new repository
        repo.git.remote('set-url', 'origin', new_repo_url)

        # Push all branches and tags
        try:
            repo.git.push('--all')
            repo.git.push('--tags')
        except GitCommandError as e:
            raise Exception(f"Failed to push to the target repository: {e}")

        # Clean up the local repository directory
        if os.path.exists(local_dir):
            shutil.rmtree(local_dir)


# Set up the engine and session
engine = create_engine('sqlite:///repositories.db', echo=True)
Session = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(engine)



@app.get("/repositories/{platform}")
async def get_repositories(platform: str, indexing: bool = Query(False, alias="indexing"), pagination: bool = Query(False, alias="pagination"), per_page: int = Query(20, alias="per_page")):
    try:
        return migrator.get_all_repositories(platform, per_page, pagination)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/move-repository/{source_platform}/{target_platform}")
async def move_repository(source_platform: str, target_platform: str, repo_obj: RepositoryObject = Body(...)):
    try:
        # Call the move_repository method with appropriate parameters
        migrator.move_repository(
            repo_obj.source_repo_url, 
            target_platform, 
            repo_obj.repo_name, 
            repo_obj.project
        )
        return {"message": f"Repository {repo_obj.repo_name} moved from {source_platform} to {target_platform}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_request(path: str, request: Request):
    # Construct the new URL for GitLab
    new_url = f"https://gitlab.com/api/v4/{path}"

    # Forward the request to GitLab
    method = request.method.lower()
    headers = {key: value for key, value in request.headers.items() if key.lower() != 'host'}
    content = await request.body()
    
    # Make the request to GitLab
    response = requests.request(method, new_url, headers=headers, data=content, allow_redirects=False)

    # Return the response received from GitLab
    return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))

@app.get("/search-repositories")
async def search_repositories(query: str):
    try:
        with Session() as session:
            results = session.query(Repository).filter(Repository.name.contains(query)).all()

            search_results = [
                {
                    "name": repo.name,
                    "description": repo.description,
                    "path": repo.path,
                    "created_at": repo.created_at,
                    "default_branch": repo.default_branch,
                    "web_url": repo.web_url,
                    "ssh_url_to_repo": repo.ssh_url_to_repo,
                    "http_url_to_repo": repo.http_url_to_repo,
                    "last_activity_at": repo.last_activity_at,
                    "platform": repo.platform
                }
                for repo in results
            ]
            return {"search_results": search_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

migrator = RepoMigrator()