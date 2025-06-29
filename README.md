# Bitwarden Secret Manager

## Overview

This project provides a command-line interface (CLI) and a FastAPI application to manage secrets from Bitwarden. It allows you to fetch, create, and manage secrets, and store them locally. The application is designed to be run in a Docker container for easy deployment and portability.

## Features

*   **Manage Bitwarden Secrets:** Interact with your Bitwarden vault to manage secrets.
*   **Local Storage:** Store secrets in a local file for offline access.
*   **Dual Interface:** Access secrets through a CLI or a FastAPI endpoint.
*   **Create New Secrets:** Add new secrets to your Bitwarden vault.
*   **Dockerized:** Packaged as a Docker container for consistent deployment across different environments.
*   **Secure:** Handles Bitwarden authentication securely.

## Architecture

The project consists of:

*   **Python Script:** The core logic for interacting with the Bitwarden API (or CLI).
*   **FastAPI:** An optional web interface to manage secrets.
*   **Docker:** A Dockerfile and `docker-compose.yml` to containerize the application.
*   **Bitwarden:** The secret management service.

## Getting Started

### Prerequisites

*   Docker and Docker Compose
*   Bitwarden account with an organization
*   Access to Bitwarden Secrets Manager
*   Ensure the token created has access to the project for read/create

### Setup Instructions

1.  **Get Bitwarden Credentials:**
    - Log into your Bitwarden account
    - Navigate to your organization settings
    - Create a new access token for Secrets Manager
    - Note your Organization ID and Project ID

2.  **Clone and Configure:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

3.  **Environment Configuration:**
    Copy the example environment file and fill in your credentials:
    ```bash
    cp .env.example .env
    ```
    
    Edit `.env` with your actual values:
    ```
    BW_ACCESS_TOKEN=your-actual-access-token
    BW_API_URL=https://api.bitwarden.com
    BW_IDENTITY_URL=https://identity.bitwarden.com
    ORGANIZATION_ID=your-actual-organization-id
    BW_PROJECT_ID=your-actual-project-id
    ```

### Installation

#### Option 1: Build the Docker image locally

1.  Build the Docker image:
    ```bash
    docker-compose build
    ```

#### Option 2: Use pre-built image from GitHub Packages

1.  Pull the Docker image:
    ```bash
    docker pull ghcr.io/[your-github-username]/bitwarden-secrets:latest
    ```

2.  Update your docker-compose.yml to use the pre-built image:
    ```yaml
    services:
      app:
        image: ghcr.io/[your-github-username]/bitwarden-secrets:latest
        # ... rest of your configuration
    ```

### Configuration

Create a `.env` file in the root of the project with the following content. You will need to create an access token from your Bitwarden account.

```
BW_ACCESS_TOKEN=<your-bitwarden-access-token>
BW_API_URL=https://api.bitwarden.com
BW_IDENTITY_URL=https://identity.bitwarden.com
ORGANIZATION_ID=<your-organization-id>
BW_PROJECT_ID=<your-project-id>
API_SECRET_KEY=<your-api-access-key>
```

## Usage

### Command-Line Interface (CLI)

You can run CLI commands directly in the container:

```bash
# List all available secrets
docker-compose run --rm cli list-secrets

# Get a specific secret
docker-compose run --rm cli get-secret "MY_SECRET_KEY"

# Create a new secret
docker-compose run --rm cli create-secret "NEW_SECRET" "secret_value" --note "Optional note"

# Sync all secrets to local file
docker-compose run --rm cli sync-secrets
```

**Available CLI Commands:**

*   `list-secrets`: List all secrets in your Bitwarden organization
*   `get-secret <secret-name>`: Get a specific secret from Bitwarden
*   `create-secret <secret-name> <secret-value> [--note]`: Create a new secret
*   `sync-secrets`: Sync all secrets to a local JSON file

### FastAPI Application

To start the FastAPI server:

```bash
docker-compose up
```

The API will be available at `http://localhost:8000`.

**API Documentation:**

The API includes built-in documentation through Swagger UI and ReDoc:
* Swagger UI: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`
* OpenAPI schema: `http://localhost:8000/openapi.json`

These interactive documentation interfaces allow you to explore all endpoints, see request/response schemas, and even test API calls directly from your browser.

**API Endpoints:**

*   `GET /`: Root endpoint with API information
*   `GET /health`: Health check endpoint
*   `GET /secrets`: List all secrets
*   `GET /secrets/{secret_name}`: Get a specific secret
*   `POST /secrets`: Create a new secret
*   `POST /sync`: Sync all secrets to local file
*   `GET /local-secrets`: Get secrets from local file

**API Authentication:**

The API is protected with an API key authentication mechanism. You need to include an `X-API-Key` header in all your requests (except the root endpoint).

To configure the API key:
1. Set the `API_SECRET_KEY` environment variable in your `.env` file
2. If not set, a development-only default key will be used (not recommended for production)
3. Include the API key in your requests as shown in the examples below

**Example API Usage:**

```bash
# Get a secret
curl -H "X-API-Key: your-api-key" http://localhost:8000/secrets/MY_SECRET_KEY

# Create a new secret
curl -X POST http://localhost:8000/secrets \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"secrets": [{"key": "NEW_SECRET", "value": "secret_value", "note": "Optional note"}]}'

# List all secrets
curl -H "X-API-Key: your-api-key" http://localhost:8000/secrets

# Sync secrets to local file
curl -X POST -H "X-API-Key: your-api-key" http://localhost:8000/sync
```

### Local Development

If you want to run the application locally without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run CLI
python main.py list-secrets

# Run API server
python api.py
```

## Deployment

This application is designed to be deployed using Docker. You can run it on any server with Docker installed.

1.  Copy the project files to your server.
2.  Create the `.env` file with your Bitwarden credentials.
3.  Run `docker-compose up -d` to start the application in the background.

## Troubleshooting

### Common Issues

1. **Authentication Errors:**
   - Verify your `BW_ACCESS_TOKEN` is correct and has not expired
   - Ensure your `ORGANIZATION_ID` and `BW_PROJECT_ID` are correct
   - Check that your access token has the necessary permissions

2. **Secret Not Found:**
   - Verify the secret exists in your Bitwarden organization
   - Check that the secret is in the correct project
   - Ensure the secret name matches exactly (case-sensitive)

3. **Connection Issues:**
   - Verify `BW_API_URL` and `BW_IDENTITY_URL` are correct
   - Check your network connection
   - Ensure firewall is not blocking API requests

4. **Docker Issues:**
   - Make sure Docker and Docker Compose are installed
   - Check that port 8000 is not already in use
   - Verify the `.env` file is in the correct location

### Logs

To view application logs:

```bash
# View API logs
docker-compose logs app

# View CLI logs
docker-compose run --rm cli list-secrets
```

## Security Considerations

- Never commit your `.env` file to version control
- Store your access token securely
- Regularly rotate your access tokens
- Use HTTPS in production deployments
- Consider using Docker secrets for sensitive environment variables

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## CI/CD Pipeline

This project includes a GitHub Actions workflow to automatically build and publish Docker images to GitHub Packages.

### Automatic Builds

The Docker image is automatically built and pushed to GitHub Packages when:
- Pushing to the main branch
- Creating and pushing a new tag (starting with "v", e.g., v1.0.0)
- Manually triggering the workflow

### Manual Trigger

You can manually trigger a build from the Actions tab in your GitHub repository.

### Image Tags

The Docker image is tagged with:
- The git tag when pushing a tag (e.g., v1.0.0)
- The branch name when pushing to a branch
- The short SHA of the commit
- "latest" when pushing to the main branch

### Using the GitHub Packages Docker Image

To use the pre-built image, you'll need to authenticate with GitHub Packages:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker pull ghcr.io/[your-github-username]/bitwarden-secrets:latest
```

## License

This project is licensed under the MIT License.
