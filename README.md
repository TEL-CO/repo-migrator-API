# Repository Migration and Management Service

## Overview

This FastAPI application facilitates the migration and management of repositories across different platforms including GitHub, GitLab, and Azure. It provides an API to retrieve all repositories from a specified platform, migrate repositories between platforms, and search through repositories stored in a local database.

## Features

- **List Repositories**: Fetch repositories from GitHub, GitLab, or Azure.

- **Migrate Repositories**: Move repositories from one platform to another.

- **Search Repositories**: Search through locally stored repositories.

## Getting Started

### Prerequisites

- Python 3.8 or higher

- Git

- FastAPI

- Uvicorn (for running the API server)

### Installation

1. Clone the repository:

git clone <repository-url>

2. Navigate to the project directory:

cd <project-directory>

3. Install the requirements:

pip install -r requirements.txt

### Configuration

Set up environment variables in a .env file based on the .env.example provided.

### Required variables include:

- GITLAB_TOKEN

- GITHUB_TOKEN

- AZURE_TOKEN

- GITLAB_GROUP_ID

- GITHUB_ORGANIZATION

- AZURE_ORGANIZATION

### Running the Application

## Start the FastAPI server using Uvicorn:

uvicorn main:app --reload

The API will be available at http://127.0.0.1:8000.

### API Endpoints

GET /repositories/{platform}: List repositories from a specified platform.

POST /move-repository/{source_platform}/{target_platform}: Migrate a repository from one platform to another.

GET /search-repositories: Search through the local repository database.

### Contributing

## Contributions to this project are welcome! Please follow these steps:

1. Fork the repository.

2. Create a new branch for your feature (git checkout -b feature/AmazingFeature).

3. Commit your changes (git commit -m 'Add some AmazingFeature').

4. Push to the branch (git push origin feature/AmazingFeature).

5. Open a pull request.

License

Distributed under the GPL License. See LICENSE for more information.

Contact
web@tlco.it
