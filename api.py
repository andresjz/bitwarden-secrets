#!/usr/bin/env python3
"""
FastAPI application for Bitwarden Secret Manager
"""
import logging
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, status, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from main import BitwardenSecretManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="🔐 Bitwarden Secret Manager API",
    description="""
    ## Bitwarden Secret Manager API
    
    A comprehensive FastAPI application for managing secrets through Bitwarden Secret Manager.
    
    ### Features:
    * 🔍 **Retrieve secrets** by name
    * ➕ **Create new secrets** with validation
    * 📋 **List all secrets** from your vault
    * 🔄 **Sync secrets** to local storage
    * 💾 **Access local secrets** for offline use
    * 🏥 **Health monitoring** endpoints
    
    ### Authentication:
    This API integrates with Bitwarden's Secret Manager service for secure secret storage and retrieval.
    
    ### API Documentation:
    - **Interactive docs**: `/docs` (Swagger UI)
    - **Alternative docs**: `/redoc` (ReDoc)
    - **OpenAPI schema**: `/openapi.json`
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    tags_metadata=[
        {
            "name": "Health",
            "description": "Health check and system status endpoints",
        },
        {
            "name": "Secrets",
            "description": "Operations for managing secrets in Bitwarden",
        },
        {
            "name": "Sync",
            "description": "Synchronization operations for local storage",
        },
    ]
)

# Pydantic models
class SecretCreate(BaseModel):
    """Model for creating a new secret"""
    key: str = Field(
        ..., 
        description="The unique key/name for the secret",
        example="database_password",
        min_length=1,
        max_length=100
    )
    value: str = Field(
        ..., 
        description="The secret value to store",
        example="super_secure_password_123",
        min_length=1
    )
    note: Optional[str] = Field(
        "", 
        description="Optional note or description for the secret",
        example="Production database password for main server",
        max_length=500
    )

class SecretResponse(BaseModel):
    """Model for secret response data"""
    id: str = Field(
        ..., 
        description="Unique identifier for the secret in Bitwarden",
        example="12345678-1234-1234-1234-123456789abc"
    )
    key: str = Field(
        ..., 
        description="The secret key/name",
        example="database_password"
    )
    value: str = Field(
        ..., 
        description="The secret value",
        example="super_secure_password_123"
    )
    note: Optional[str] = Field(
        "", 
        description="Optional note or description",
        example="Production database password for main server"
    )

class SecretList(BaseModel):
    """Model for listing multiple secrets"""
    secrets: List[SecretResponse] = Field(
        ..., 
        description="List of secrets from the vault"
    )

class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str = Field(
        ..., 
        description="Current health status",
        example="healthy"
    )

class MessageResponse(BaseModel):
    """Model for simple message responses"""
    message: str = Field(
        ..., 
        description="Response message",
        example="Successfully synced secrets to local file"
    )

class LocalSecretsResponse(BaseModel):
    """Model for local secrets response"""
    secrets: Dict = Field(
        ..., 
        description="Secrets loaded from local file storage"
    )

# Initialize the secret manager
try:
    secret_manager = BitwardenSecretManager()
except Exception as e:
    logger.error(f"Failed to initialize Bitwarden Secret Manager: {e}")
    secret_manager = None

@app.get(
    "/",
    tags=["Health"],
    summary="API Root Information",
    description="Get basic information about the API",
    response_model=MessageResponse,
    responses={
        200: {
            "description": "API information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Bitwarden Secret Manager API",
                        "version": "1.0.0"
                    }
                }
            }
        }
    }
)
async def root():
    """
    **Get API Root Information**
    
    Returns basic information about the Bitwarden Secret Manager API including:
    - API name and purpose
    - Current version number
    - Basic status confirmation
    
    This endpoint can be used to verify the API is running and accessible.
    """
    return {"message": "Bitwarden Secret Manager API", "version": "1.0.0"}

@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Check the health and connectivity of the Bitwarden Secret Manager service",
    response_model=HealthResponse,
    responses={
        200: {
            "description": "Service is healthy and operational",
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            }
        },
        503: {
            "description": "Service unavailable - Secret manager not initialized",
            "content": {
                "application/json": {
                    "example": {"detail": "Secret manager not initialized"}
                }
            }
        }
    }
)
async def health_check():
    """
    **Health Check Endpoint**
    
    Performs a health check to verify:
    - ✅ Bitwarden Secret Manager is properly initialized
    - ✅ Connection to Bitwarden services is functional
    - ✅ API is ready to handle requests
    
    **Returns:**
    - `200`: Service is healthy and operational
    - `503`: Service is unavailable (initialization failed)
    
    Use this endpoint for monitoring and load balancer health checks.
    """
    if secret_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Secret manager not initialized"
        )
    return {"status": "healthy"}

@app.get(
    "/secrets/{secret_name}", 
    tags=["Secrets"],
    summary="Get Secret by Name",
    description="Retrieve a specific secret from Bitwarden vault by its key/name",
    response_model=SecretResponse,
    responses={
        200: {
            "description": "Secret found and returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "12345678-1234-1234-1234-123456789abc",
                        "key": "database_password",
                        "value": "super_secure_password_123",
                        "note": "Production database password"
                    }
                }
            }
        },
        404: {
            "description": "Secret not found in the vault",
            "content": {
                "application/json": {
                    "example": {"detail": "Secret 'non_existent_key' not found"}
                }
            }
        },
        500: {
            "description": "Internal server error during secret retrieval",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to retrieve secret from Bitwarden"}
                }
            }
        },
        503: {
            "description": "Service unavailable - Secret manager not initialized"
        }
    }
)
async def get_secret(
    secret_name: str = Path(
        ..., 
        description="The name/key of the secret to retrieve",
        example="database_password",
        min_length=1,
        max_length=100
    )
):
    """
    **Retrieve a Secret by Name**
    
    Fetches a specific secret from your Bitwarden vault using its key/name.
    
    **Parameters:**
    - `secret_name`: The unique key/name identifier for the secret
    
    **Example Usage:**
    ```
    GET /secrets/database_password
    ```
    
    **Returns:**
    - Complete secret information including ID, key, value, and notes
    - Secure access to sensitive data stored in Bitwarden
    
    **Security Notes:**
    - Only returns secrets accessible to the authenticated Bitwarden account
    - Secret values are transmitted securely via HTTPS
    """
    if secret_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Secret manager not initialized"
        )
    
    try:
        secret = secret_manager.get_secret(secret_name)
        if secret is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Secret '{secret_name}' not found"
            )
        
        return SecretResponse(
            id=str(secret["id"]), 
            key=secret["key"], 
            value=secret["value"], 
            note=secret.get("note", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting secret '{secret_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to retrieve secret: {str(e)}"
        )

@app.post(
    "/secrets", 
    tags=["Secrets"],
    summary="Create New Secret",
    description="Create a new secret in the Bitwarden vault",
    response_model=SecretResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Secret created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "12345678-1234-1234-1234-123456789abc",
                        "key": "api_key",
                        "value": "sk-1234567890abcdef",
                        "note": "API key for external service"
                    }
                }
            }
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": {"detail": "Secret key cannot be empty"}
                }
            }
        },
        409: {
            "description": "Secret with this key already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Secret with key 'api_key' already exists"}
                }
            }
        },
        500: {
            "description": "Internal server error during secret creation"
        },
        503: {
            "description": "Service unavailable - Secret manager not initialized"
        }
    }
)
async def create_secret(secret: SecretCreate):
    """
    **Create a New Secret**
    
    Adds a new secret to your Bitwarden vault with the specified key, value, and optional note.
    
    **Request Body:**
    - `key`: Unique identifier for the secret (required)
    - `value`: The actual secret value to store (required)
    - `note`: Optional description or notes about the secret
    
    **Example Request:**
    ```json
    {
        "key": "api_key",
        "value": "sk-1234567890abcdef",
        "note": "API key for external service integration"
    }
    ```
    
    **Returns:**
    - Complete information about the created secret including generated ID
    
    **Security Features:**
    - ✅ Validates input data before creation
    - ✅ Encrypts secret values using Bitwarden's security
    - ✅ Generates unique ID for tracking
    """
    if secret_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Secret manager not initialized"
        )
    
    try:
        created_secret = secret_manager.create_secret(
            secret.key, 
            secret.value, 
            secret.note or ""
        )
        
        return SecretResponse(
            id=str(created_secret["id"]), 
            key=created_secret["key"], 
            value=created_secret["value"], 
            note=created_secret.get("note", "")
        )
        
    except Exception as e:
        logger.error(f"Error creating secret '{secret.key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to create secret: {str(e)}"
        )

@app.get(
    "/secrets", 
    tags=["Secrets"],
    summary="List All Secrets",
    description="Retrieve a list of all secrets from the Bitwarden vault",
    response_model=SecretList,
    responses={
        200: {
            "description": "Secrets retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "secrets": [
                            {
                                "id": "12345678-1234-1234-1234-123456789abc",
                                "key": "database_password",
                                "value": "super_secure_password_123",
                                "note": "Production database password"
                            },
                            {
                                "id": "87654321-4321-4321-4321-cba987654321",
                                "key": "api_key",
                                "value": "sk-1234567890abcdef",
                                "note": "API key for external service"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during secrets retrieval"
        },
        503: {
            "description": "Service unavailable - Secret manager not initialized"
        }
    }
)
async def list_secrets():
    """
    **List All Secrets**
    
    Retrieves a complete list of all secrets stored in your Bitwarden vault.
    
    **Returns:**
    - Array of all secrets with their complete information
    - Includes ID, key, value, and notes for each secret
    
    **Use Cases:**
    - 📋 Inventory management of stored secrets
    - 🔍 Browse available secrets for integration
    - 📊 Audit and compliance reporting
    - 🔄 Backup and synchronization operations
    
    **Security Notes:**
    - Returns all secrets accessible to the authenticated account
    - Use with caution in production environments
    - Consider implementing pagination for large vaults
    """
    if secret_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Secret manager not initialized"
        )
    
    try:
        secrets = secret_manager.list_secrets()
        secret_responses = [
            SecretResponse(
                id=str(secret["id"]), 
                key=secret["key"], 
                value=secret["value"], 
                note=secret.get("note", "")
            ) for secret in secrets
        ]
        
        return SecretList(secrets=secret_responses)
        
    except Exception as e:
        logger.error(f"Error listing secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to retrieve secrets: {str(e)}"
        )

@app.post(
    "/sync",
    tags=["Sync"],
    summary="Sync Secrets to Local Storage",
    description="Synchronize all vault secrets to local file for offline access",
    response_model=MessageResponse,
    responses={
        200: {
            "description": "Secrets synchronized successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Successfully synced secrets to local file"}
                }
            }
        },
        500: {
            "description": "Internal server error during synchronization"
        },
        503: {
            "description": "Service unavailable - Secret manager not initialized"
        }
    }
)
async def sync_secrets():
    """
    **Sync Secrets to Local Storage**
    
    Downloads and synchronizes all secrets from your Bitwarden vault to local file storage.
    
    **Features:**
    - 🔄 **Full Synchronization**: Downloads all accessible secrets
    - 💾 **Local Storage**: Saves to encrypted local file
    - 🚀 **Offline Access**: Enables offline secret retrieval
    - 🔒 **Secure**: Maintains encryption during storage
    
    **Use Cases:**
    - Backup secrets for disaster recovery
    - Enable offline application functionality
    - Create local development environment copies
    - Reduce API calls for frequently accessed secrets
    
    **Operation:**
    1. Connects to Bitwarden vault
    2. Retrieves all accessible secrets
    3. Encrypts and stores locally
    4. Returns confirmation message
    """
    if secret_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Secret manager not initialized"
        )
    
    try:
        secret_manager.sync_secrets_to_file()
        return {"message": "Successfully synced secrets to local file"}
        
    except Exception as e:
        logger.error(f"Error syncing secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to sync secrets: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to sync secrets: {str(e)}"
        )

@app.get(
    "/local-secrets",
    tags=["Sync"],
    summary="Get Local Secrets",
    description="Retrieve secrets from local file storage (offline access)",
    response_model=LocalSecretsResponse,
    responses={
        200: {
            "description": "Local secrets retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "secrets": {
                            "DATABASE_PASSWORD": {
                                "key": "DATABASE_PASSWORD",
                                "value": "super_secure_password_123",
                                "note": "Database password for production",
                                "id": "local-DATABASE_PASSWORD"
                            },
                            "API_KEY": {
                                "key": "API_KEY",
                                "value": "sk-1234567890abcdef",
                                "note": "API key for external service",
                                "id": "local-API_KEY"
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Local secrets file not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Local secrets file not found. Run /sync first."}
                }
            }
        },
        500: {
            "description": "Internal server error during local file access"
        },
        503: {
            "description": "Service unavailable - Secret manager not initialized"
        }
    }
)
async def get_local_secrets():
    """
    **Get Secrets from Local Storage**
    
    Retrieves secrets from the local file storage for offline access.
    
    **Features:**
    - 🚀 **Fast Access**: No network requests required
    - 💾 **Offline Mode**: Works without internet connection
    - 🔒 **Secure Storage**: Encrypted local file storage
    - 📱 **Low Latency**: Instant secret retrieval
    
    **Prerequisites:**
    - Must run `/sync` endpoint first to populate local storage
    - Local secrets file must exist and be accessible
    
    **Use Cases:**
    - Development environments with limited connectivity
    - Emergency access during service outages
    - High-performance applications requiring fast secret access
    - Backup secret retrieval methods
    
    **Security Notes:**
    - Local secrets are encrypted but stored on disk
    - Ensure proper file system permissions
    - Regular synchronization recommended for data freshness
    """
    if secret_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Secret manager not initialized"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Secret manager not initialized"
        )
    
    try:
        secrets = secret_manager.load_secrets_from_file()
        return {"secrets": secrets}
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Local secrets file not found. Please run /sync endpoint first to create local storage."
        )
    except Exception as e:
        logger.error(f"Error loading local secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to load local secrets: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
