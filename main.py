#!/usr/bin/env python3
"""
Bitwarden Secret Manager
A CLI and API tool for managing secrets in Bitwarden
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import click
from bitwarden_sdk import BitwardenClient, DeviceType, client_settings_from_dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BitwardenSecretManager:
    """Main class for managing Bitwarden secrets"""
    
    def __init__(self):
        self.client = None
        self.local_secrets_file = "data/secrets.json"
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Bitwarden client with environment variables"""
        identity_url = os.getenv("BW_IDENTITY_URL", "https://identity.bitwarden.com")
        api_url = os.getenv("BW_API_URL", "https://api.bitwarden.com")
        access_token = os.getenv("BW_ACCESS_TOKEN")
        
        if not access_token:
            raise ValueError("BW_ACCESS_TOKEN environment variable is required")
        
        self.organization_id = os.getenv("ORGANIZATION_ID")
        self.project_id = os.getenv("BW_PROJECT_ID")
        
        if not self.organization_id:
            raise ValueError("ORGANIZATION_ID environment variable is required")
        
        if not self.project_id:
            raise ValueError("BW_PROJECT_ID environment variable is required")
            
        # Ensure organization_id and project_id are valid UUIDs
        from uuid import UUID
        try:
            self.organization_id = str(UUID(self.organization_id))
            self.project_id = str(UUID(self.project_id))
            logger.info(f"Validated Organization ID: {self.organization_id}")
            logger.info(f"Validated Project ID: {self.project_id}")
        except ValueError as e:
            logger.error(f"Invalid UUID format: {e}")
            raise ValueError(f"Organization ID and Project ID must be valid UUIDs: {e}")
        
        try:
            # Set up the Bitwarden client
            client_settings = client_settings_from_dict({
                "apiUrl": api_url,
                "deviceType": DeviceType.SDK,
                "identityUrl": identity_url,
                "userAgent": "Bitwarden-Secret-Manager-Python",
            })
            
            logger.info(f"Using API URL: {api_url}")
            logger.info(f"Using Identity URL: {identity_url}")
            
            self.client = BitwardenClient(client_settings)
            
            # Log in with the access token
            auth_response = self.client.auth().login_access_token(access_token)
            logger.info("Successfully authenticated with Bitwarden")
            
            # Verify organization access
            try:
                # Try to list projects to verify access
                projects = self.client.projects().list(self.organization_id)

                if hasattr(projects, 'data'):
                    project_names = [project.name for project in projects.data.data] if hasattr(projects.data, 'data') else []
                    logger.info(f"Access to projects: {', '.join(project_names) if project_names else 'None'}")
            except Exception as org_e:
                logger.warning(f"Could not verify organization access: {org_e}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Bitwarden client: {e}")
            raise
    
    def get_secret(self, secret_name: str) -> Optional[Dict]:
        """Get a secret from Bitwarden by name"""
        try:
            secrets = self.client.secrets().list(self.organization_id)
            
            for secret in secrets.data.data:
                if secret.key == secret_name:
                    secret_detail = self.client.secrets().get(secret.id)
                    return {
                        "id": secret_detail.data.id,
                        "key": secret_detail.data.key,
                        "value": secret_detail.data.value,
                        "note": secret_detail.data.note
                    }
            
            logger.warning(f"Secret '{secret_name}' not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting secret '{secret_name}': {e}")
            raise
    
    def create_secret(self, secret_name: str, secret_value: str, note: str = "") -> Dict:
        """Create a new secret in Bitwarden"""
        try:
            # Import UUID class
            from uuid import UUID
           
            # Convert string IDs to UUID objects as required by the SDK
            org_id = UUID(self.organization_id)
            project_id = UUID(self.project_id)
            
            response = self.client.secrets().create(
                organization_id=org_id,
                key=secret_name,
                value=secret_value,
                note=note,
                project_ids=[project_id],
            )
            
            # Extract the secret from the response
            secret = response.data
            
            logger.info(f"Successfully created secret '{secret_name}' with ID {secret.id}")
            return {
                "id": secret.id,
                "key": secret.key,
                "value": secret.value,
                "note": secret.note
            }
            
        except Exception as e:
            logger.error(f"Error creating secret '{secret_name}': {e}  Ensure the token has access to the project to create secrets.")
            raise
    
    def list_secrets(self) -> List[Dict]:
        """List all secrets in the organization"""
        try:
            secrets = self.client.secrets().list(self.organization_id)
            
            secret_list = []
            for secret in secrets.data.data:
                secret_detail = self.client.secrets().get(secret.id)
                secret_list.append({
                    "id": secret_detail.data.id,
                    "key": secret_detail.data.key,
                    "value": secret_detail.data.value,
                    "note": secret_detail.data.note
                })
            
            return secret_list
            
        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            raise
    
    def sync_secrets_to_file(self) -> None:
        """Sync all secrets to a local JSON file"""
        try:
            secrets = self.list_secrets()
            
            with open(self.local_secrets_file, 'w') as f:
                json.dump(secrets, f, indent=2, default=str)
            
            logger.info(f"Successfully synced {len(secrets)} secrets to {self.local_secrets_file}")
            
        except Exception as e:
            logger.error(f"Error syncing secrets to file: {e}")
            raise
    
    def load_secrets_from_file(self) -> Dict:
        """Load secrets from local file"""
        try:
            if not os.path.exists(self.local_secrets_file):
                logger.warning(f"Local secrets file {self.local_secrets_file} not found")
                return {}
            
            with open(self.local_secrets_file, 'r') as f:
                secrets = json.load(f)
            
            # Convert list to dict for easier lookup
            secrets_dict = {secret['key']: secret for secret in secrets}
            return secrets_dict
            
        except Exception as e:
            logger.error(f"Error loading secrets from file: {e}")
            raise

# Utility functions for converting between JSON and ENV formats
def json_to_env(json_file: str, env_file: str) -> None:
    """Convert from JSON format to .env format"""
    try:
        # Read the JSON file
        with open(json_file, 'r') as f:
            secrets = json.load(f)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(env_file), exist_ok=True)
        
        # Write to .env file
        with open(env_file, 'w') as f:
            for secret in secrets:
                # Write KEY=value
                f.write(f"{secret['key']}={secret['value']}\n")
                
                # If ID exists, write it as a comment
                if 'id' in secret and secret['id']:
                    f.write(f"# ID: {secret['id']}\n")
                
                # If note exists, write it as a comment
                if 'note' in secret and secret['note']:
                    for note_line in secret['note'].split('\n'):
                        f.write(f"# Note: {note_line}\n")
                
                # Add a blank line between entries for readability
                f.write("\n")
        
        logger.info(f"Successfully converted {len(secrets)} secrets from {json_file} to {env_file}")
    
    except Exception as e:
        logger.error(f"Error converting from JSON to ENV: {e}")
        raise

def env_to_json(env_file: str, json_file: str) -> None:
    """Convert from .env format to JSON format"""
    try:
        if not os.path.exists(env_file):
            logger.error(f"ENV file {env_file} not found")
            return
        
        secrets = []
        current_secret = None
        
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Process each line
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Process key=value lines
            if "=" in line and not line.startswith('#'):
                # If we have a current secret, add it to the list
                if current_secret:
                    secrets.append(current_secret)
                
                # Start a new secret
                key, value = line.split('=', 1)
                current_secret = {
                    "id": "",
                    "key": key.strip(),
                    "value": value.strip(),
                    "note": ""
                }
            
            # Process comment lines
            elif line.startswith('#'):
                if current_secret:
                    # Extract ID from comment
                    if line.startswith('# ID:'):
                        current_secret['id'] = line[6:].strip()
                    
                    # Extract Note from comment
                    if line.startswith('# Note:'):
                        if current_secret['note']:
                            current_secret['note'] += '\n' + line[7:].strip()
                        else:
                            current_secret['note'] = line[7:].strip()
        
        # Add the last secret if there is one
        if current_secret:
            secrets.append(current_secret)
        
        # Generate IDs for any secrets that don't have one
        for secret in secrets:
            if not secret['id']:
                secret['id'] = f"local-{uuid4()}"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(json_file), exist_ok=True)
        
        # Write to JSON file
        with open(json_file, 'w') as f:
            json.dump(secrets, f, indent=2)
        
        logger.info(f"Successfully converted {len(secrets)} secrets from {env_file} to {json_file}")
    
    except Exception as e:
        logger.error(f"Error converting from ENV to JSON: {e}")
        raise

def env_to_json_formatted(env_file: str, json_file: str, project: str, env: str) -> None:
    """
    Convert from .env format to JSON format with formatted keys
    
    This specialized function converts environment variables to Bitwarden secrets 
    using a formatted key pattern like PROJECT/ENV/VAR_NAME
    """
    try:
        if not os.path.exists(env_file):
            logger.error(f"ENV file {env_file} not found")
            return
        
        # Normalize project and env names to uppercase
        project = project.upper()
        env = env.upper()
        
        secrets = []
        notes_dict = {}
        current_notes = []
        
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # First pass: collect all comments as potential notes for the next variable
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines or // lines (file path comments)
            if not line or line.startswith('//'):
                continue
            
            # If it's a comment, add it to current notes
            if line.startswith('#'):
                current_notes.append(line[1:].strip())
            # If it's a variable definition
            elif "=" in line and not line.startswith('#'):
                key = line.split('=', 1)[0].strip()
                # Associate notes with this key
                if current_notes:
                    notes_dict[key] = "\n".join(current_notes)
                    current_notes = []  # Reset for next variable
        
        # Second pass: process actual variables
        current_notes = []
        for line in lines:
            line = line.strip()
            
            # Skip empty lines or // lines
            if not line or line.startswith('//'):
                continue
            
            # Skip comment lines in this pass
            if line.startswith('#'):
                continue
            
            # Process key=value lines
            if "=" in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Format the key as PROJECT/ENV/KEY
                formatted_key = f"{project}/{env}/{key}"
                
                # Create the secret entry
                secret = {
                    # "id": f"local-{uuid4()}",
                    "key": formatted_key,
                    "value": value,
                    "note": "Created with Code PROJECT: {}\nENV: {}\n{}".format(project, env, notes_dict.get(key, ""))    
                }
                
                secrets.append(secret)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(json_file), exist_ok=True)
        
        # Write to JSON file
        with open(json_file, 'w') as f:
            json.dump(secrets, f, indent=2)
        
        logger.info(f"Successfully converted {len(secrets)} secrets from {env_file} to {json_file} with formatted keys")
    
    except Exception as e:
        logger.error(f"Error converting from ENV to JSON with formatted keys: {e}")
        raise
# CLI Commands
@click.group()
def cli():
    """Bitwarden Secret Manager CLI"""
    pass

@cli.command()
@click.argument('secret_name')
def get_secret(secret_name):
    """Get a secret from Bitwarden"""
    try:
        manager = BitwardenSecretManager()
        secret = manager.get_secret(secret_name)
        
        if secret:
            click.echo(f"Secret: {secret['key']}")
            click.echo(f"Value: {secret['value']}")
            if secret['note']:
                click.echo(f"Note: {secret['note']}")
        else:
            click.echo(f"Secret '{secret_name}' not found")
            
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
@click.argument('secret_name')
@click.argument('secret_value')
@click.option('--note', default='', help='Optional note for the secret')
def create_secret(secret_name, secret_value, note):
    """Create a new secret in Bitwarden"""
    try:
        manager = BitwardenSecretManager()
        secret = manager.create_secret(secret_name, secret_value, note)
        
        click.echo(f"Successfully created secret: {secret['key']}")
        
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
def sync_secrets():
    """Sync all secrets to a local file"""
    try:
        manager = BitwardenSecretManager()
        manager.sync_secrets_to_file()
        
        click.echo("Successfully synced secrets to local file")
        
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
def list_secrets():
    """List all secrets"""
    try:
        manager = BitwardenSecretManager()
        secrets = manager.list_secrets()
        
        if secrets:
            click.echo("Available secrets:")
            for secret in secrets:
                click.echo(f"- {secret['key']}")
                if secret['note']:
                    click.echo(f"  Note: {secret['note']}")
        else:
            click.echo("No secrets found")
            
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
@click.option('--json-file', default='data/secrets.json', help='Path to the JSON file')
@click.option('--env-file', default='data/secrets.env', help='Path to the ENV file')
def convert_to_env(json_file, env_file):
    """Convert secrets from JSON to .env format"""
    try:
        json_to_env(json_file, env_file)
        click.echo(f"Successfully converted secrets from {json_file} to {env_file}")
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
@click.option('--env-file', default='data/secrets.env', help='Path to the ENV file')
@click.option('--json-file', default='data/secrets.json', help='Path to the JSON file')
def convert_to_json(env_file, json_file):
    """Convert secrets from .env to JSON format"""
    try:
        env_to_json(env_file, json_file)
        click.echo(f"Successfully converted secrets from {env_file} to {json_file}")
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
@click.option('--env-file', default='data/secrets.env', help='Path to the ENV file')
@click.option('--json-file', default='data/secrets.json', help='Path to the JSON file')
@click.option('--project', default='MYPROJECT', help='Project name for formatting')
@click.option('--env', default='DEV', help='Environment name for formatting')
def convert_to_json_formatted(env_file, json_file, project, env):
    """Convert secrets from .env to JSON format with formatted keys"""
    try:
        env_to_json_formatted(env_file, json_file, project, env)
        click.echo(f"Successfully converted secrets from {env_file} to {json_file} with formatted keys")
    except Exception as e:
        click.echo(f"Error: {e}")

if __name__ == '__main__':
    cli()
