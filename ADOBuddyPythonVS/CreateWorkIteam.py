import requests
import os
import base64
import subprocess
import json
from azure.devops.connection import Connection
from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
from msrest.authentication import BasicAuthentication
import sys

def authenticate_azure_cli_powershell():
    """Authenticate using Azure CLI via PowerShell and return access token"""
    try:
        print("Checking Azure CLI login status via PowerShell...")
        
        # Check if user is logged in to Azure CLI via PowerShell
        check_login_cmd = ["powershell", "-Command", "az account show --query 'user.name' -o tsv"]
        result = subprocess.run(check_login_cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            print("Not logged in to Azure CLI. Please run 'az login' in PowerShell first.")
            print("Run the following command in PowerShell: az login")
            return None
        
        print(f"Logged in as: {result.stdout.strip()}")
        
        # Get access token for Azure DevOps using PowerShell with semicolon command chaining
        token_cmd = ["powershell", "-Command", "az account get-access-token --resource https://app.vssps.visualstudio.com --query 'accessToken' -o tsv"]
        token_result = subprocess.run(token_cmd, capture_output=True, text=True, shell=True)
        
        if token_result.returncode != 0:
            print(f"Failed to get access token: {token_result.stderr}")
            return None
        
        access_token = token_result.stdout.strip()
        if not access_token:
            print("Empty access token received")
            return None
            
        print("Successfully obtained access token from Azure CLI via PowerShell")
        return access_token
        
    except Exception as e:
        print(f"Error during Azure CLI PowerShell authentication: {e}")
        return None

def create_work_item_with_powershell_auth(organization_url, project, work_item_type, title, description):
    """Create work item using Azure DevOps client with PowerShell Azure CLI authentication"""
    try:
        # Get access token from PowerShell Azure CLI
        access_token = authenticate_azure_cli_powershell()
        if not access_token:
            return None
        
        # Create basic authentication using the token
        credentials = BasicAuthentication('', access_token)
        
        # Create connection to Azure DevOps
        connection = Connection(base_url=organization_url, creds=credentials)
        
        # Get work item tracking client
        wit_client = connection.clients.get_work_item_tracking_client()
        
        # Define work item fields
        patch_document = [
            JsonPatchOperation(
                op="add",
                path="/fields/System.Title",
                value=title
            ),
            JsonPatchOperation(
                op="add", 
                path="/fields/System.Description",
                value=description
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.State",
                value="New"
            )
        ]
        
        # Create the work item
        work_item = wit_client.create_work_item(
            document=patch_document,
            project=project,
            type=work_item_type
        )
        
        return work_item
        
    except Exception as e:
        print(f"Error creating work item with PowerShell Azure CLI authentication: {e}")
        return None

def create_work_item_with_rest_api(organization_url, project, work_item_type, title, description, access_token):
    """Create work item using REST API with Azure CLI token from PowerShell"""
    try:
        url = f"{organization_url}/{project}/_apis/wit/workitems/${work_item_type}?api-version=7.0"
        
        headers = {
            "Content-Type": "application/json-patch+json",
            "Authorization": f"Bearer {access_token}"
        }
        
        # Create JSON patch document for work item creation
        patch_document = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": title
            },
            {
                "op": "add",
                "path": "/fields/System.Description", 
                "value": description
            },
            {
                "op": "add",
                "path": "/fields/System.State",
                "value": "New"
            }
        ]
        
        response = requests.post(url, json=patch_document, headers=headers)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating work item with REST API: {e}")
        return None

def verify_azure_cli_installation():
    """Verify that Azure CLI is installed and accessible via PowerShell"""
    try:
        version_cmd = ["powershell", "-Command", "az --version"]
        result = subprocess.run(version_cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            print("Azure CLI is not installed or not accessible via PowerShell")
            print("Please install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
            return False
        
        print("Azure CLI is installed and accessible")
        return True
        
    except Exception as e:
        print(f"Error checking Azure CLI installation: {e}")
        return False

def main():
    """Main function to authenticate and create work item using PowerShell Azure CLI"""
    
    # Configuration - you can modify these values
    organization_url = "https://dev.azure.com/tr-tax"  # Replace with your organization URL
    project = "TaxProf"  # Replace with your project name
    work_item_type = "Bug"  # Can be Bug, Task, User Story, etc.
    title = "Sample Bug Created via PowerShell Azure CLI Auth"
    description = "This is a test work item created using PowerShell Azure CLI authentication and Azure DevOps API"
    
    print("Starting Azure DevOps work item creation using PowerShell Azure CLI...")
    print(f"Organization: {organization_url}")
    print(f"Project: {project}")
    print(f"Work Item Type: {work_item_type}")
    print("-" * 60)
    
    # Verify Azure CLI is installed
    if not verify_azure_cli_installation():
        return
    
    # Method 1: Try using Azure DevOps Python client with PowerShell Azure CLI authentication
    print("\nMethod 1: Attempting to create work item using Azure DevOps client with PowerShell auth...")
    work_item = create_work_item_with_powershell_auth(
        organization_url, project, work_item_type, title, description
    )
    
    if work_item:
        print("Work item created successfully using Azure DevOps client!")
        print(f"  Work Item ID: {work_item.id}")
        print(f"  Title: {work_item.fields['System.Title']}")
        print(f"  State: {work_item.fields['System.State']}")
        print(f"  URL: {work_item.url}")
        return
    
    # Method 2: Fallback to REST API with PowerShell Azure CLI token
    print("\nMethod 2: Attempting to create work item using REST API with PowerShell Azure CLI token...")
    access_token = authenticate_azure_cli_powershell()
    
    if not access_token:
        print("Failed to authenticate with Azure CLI via PowerShell")
        print("\nTo resolve this issue:")
        print("1. Open PowerShell as Administrator")
        print("2. Run: az login")
        print("3. Complete the authentication process")
        print("4. Run this script again")
        return
    
    print("Successfully authenticated with Azure CLI via PowerShell")
    
    # Create work item using REST API
    work_item_response = create_work_item_with_rest_api(
        organization_url, project, work_item_type, title, description, access_token
    )
    
    if work_item_response:
        print("Work item created successfully using REST API!")
        print(f"  Work Item ID: {work_item_response.get('id')}")
        print(f"  Title: {work_item_response.get('fields', {}).get('System.Title')}")
        print(f"  State: {work_item_response.get('fields', {}).get('System.State')}")
        print(f"  URL: {work_item_response.get('url')}")
    else:
        print("Failed to create work item")

if __name__ == "__main__":
    main()