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
        self.local_secrets_file = "secrets.json"
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
                # Try to list organizations to verify access
                orgs = self.client.organizations().list()
                if hasattr(orgs, 'data'):
                    org_names = [org.name for org in orgs.data.data] if hasattr(orgs.data, 'data') else []
                    logger.info(f"Access to organizations: {', '.join(org_names) if org_names else 'None'}")
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
            
            logger.info(f"Creating secret '{secret_name}' for project '{self.project_id}' and organization '{self.organization_id}'")

            # Convert string IDs to UUID objects as required by the SDK
            org_id = UUID(self.organization_id)
            project_id = UUID(self.project_id)
            
            secret = self.client.secrets().create(
                organization_id=org_id,
                key=secret_name,
                value=secret_value,
                note=note,
                project_ids=[project_id],
            )
            
            logger.info(f"Successfully created secret '{secret_name}'")
            return {
                "id": secret.id,
                "key": secret.key,
                "value": secret.value,
                "note": secret.note
            }
            
        except Exception as e:
            logger.error(f"Error creating secret '{secret_name}': {e}")
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

if __name__ == '__main__':
    cli()
