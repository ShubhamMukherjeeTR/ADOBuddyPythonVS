import gradio as gr
import json
import os
import requests
import subprocess
from azure.devops.connection import Connection
from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
from msrest.authentication import BasicAuthentication

def load_team_data():
    """Load team data from TeamNameAndManager.json"""
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(script_dir, "TeamNameAndManager.json")
        
        with open(json_file_path, 'r', encoding='utf-8') as file:
            team_data = json.load(file)
        
        # Create choices for dropdown: display team names, use manager names as values
        choices = []
        for team in team_data:
            team_name = team["Team Name"]
            manager_name = team["Manager Name"]
            choices.append((team_name, manager_name))
        
        return choices
    except FileNotFoundError:
        return [("No teams found", "No manager")]
    except json.JSONDecodeError:
        return [("Invalid JSON", "No manager")]
    except Exception as e:
        return [("Error loading teams", str(e))]

def load_env_config():
    """Load configuration from .env file if it exists"""
    config = {}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file_path = os.path.join(script_dir, ".env")
    
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config

def authenticate_with_pat():
    """Authenticate using Personal Access Token from environment or .env file"""
    try:
        # Try to get PAT from environment variables first
        pat = os.environ.get('ADO_PAT')
        
        # If not found, try to load from .env file
        if not pat:
            config = load_env_config()
            pat = config.get('ADO_PAT')
        
        if pat and pat != 'your-personal-access-token':
            print("Using Personal Access Token authentication")
            return pat, "Success"
        else:
            return None, "No valid PAT found in environment or .env file"
            
    except Exception as e:
        return None, f"Error loading PAT: {e}"

def authenticate_azure_cli_powershell():
    """Authenticate using Azure CLI via PowerShell and return access token"""
    try:
        print("Checking Azure CLI login status via PowerShell...")
        
        # Check if user is logged in to Azure CLI via PowerShell - using semicolon instead of &&
        check_login_cmd = ["powershell", "-Command", "az account show --query 'user.name' -o tsv"]
        result = subprocess.run(check_login_cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            return None, "Not logged in to Azure CLI. Please run 'az login' in PowerShell first."
        
        print(f"Logged in as: {result.stdout.strip()}")
        
        # Get access token for Azure DevOps using the correct resource
        # Try different resource URIs for better compatibility
        resources = [
            "499b84ac-1321-427f-aa17-267ca6975798",  # Azure DevOps
            "https://app.vssps.visualstudio.com",    # Visual Studio Team Services
            "https://management.azure.com/"          # Azure Resource Manager
        ]
        
        for resource in resources:
            print(f"Trying to get token for resource: {resource}")
            token_cmd = ["powershell", "-Command", f"az account get-access-token --resource {resource} --query 'accessToken' -o tsv"]
            token_result = subprocess.run(token_cmd, capture_output=True, text=True, shell=True)
            
            if token_result.returncode == 0:
                access_token = token_result.stdout.strip()
                if access_token and access_token != "":
                    print(f"Successfully obtained access token for resource: {resource}")
                    return access_token, "Success"
        
        return None, "Failed to get access token for any Azure DevOps resource"
        
    except Exception as e:
        return None, f"Error during Azure CLI PowerShell authentication: {e}"

def create_work_item_with_rest_api(organization_url, project, work_item_type, title, description, assignee=None, auth_token=None, use_pat=False):
    """Create work item using REST API with either PAT or Azure CLI token"""
    try:
        url = f"{organization_url}/{project}/_apis/wit/workitems/${work_item_type}?api-version=7.0"
        
        if use_pat:
            # Use Basic authentication with PAT
            import base64
            credentials = base64.b64encode(f":{auth_token}".encode()).decode()
            headers = {
                "Content-Type": "application/json-patch+json",
                "Authorization": f"Basic {credentials}"
            }
        else:
            # Use Bearer token from Azure CLI
            headers = {
                "Content-Type": "application/json-patch+json",
                "Authorization": f"Bearer {auth_token}"
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
        
        # Add assignee if provided
        if assignee:
            patch_document.append({
                "op": "add",
                "path": "/fields/System.AssignedTo",
                "value": assignee
            })
        
        response = requests.post(url, json=patch_document, headers=headers)
        
        if response.status_code == 200:
            return response.json(), "Success"
        else:
            return None, f"HTTP {response.status_code}: {response.text}"
        
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {e}"
    except Exception as e:
        return None, f"Error creating work item with REST API: {e}"

def create_work_item_with_python_client(organization_url, project, work_item_type, title, description, assignee=None, auth_token=None, use_pat=False):
    """Create work item using Azure DevOps Python client"""
    try:
        if use_pat:
            # Use Basic authentication with PAT
            credentials = BasicAuthentication('', auth_token)
        else:
            # Use Bearer token from Azure CLI
            credentials = BasicAuthentication('', auth_token)
        
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
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.AreaPath",
                value="TaxProf\\surePrep\\surePrep-dbe-phoenix-1"
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.Tags",
                value="DBREQ"
            )
        ]

        # Add assignee if provided
        if assignee:
            patch_document.append(
                JsonPatchOperation(
                    op="add",
                    path="/fields/System.AssignedTo",
                    value=assignee
                )
            )
        
        # Create the work item
        work_item = wit_client.create_work_item(
            document=patch_document,
            project=project,
            type=work_item_type
        )
        
        return work_item, "Success"
        
    except Exception as e:
        return None, f"Error creating work item with Python client: {e}"

def create_work_item_with_multiple_auth_methods(organization_url, project, work_item_type, title, description, assignee=None):
    """Try multiple authentication methods to create work item"""
    try:
        # Method 1: Try PAT authentication first (more reliable)
        print("Attempting PAT authentication...")
        pat_token, pat_message = authenticate_with_pat()
        if pat_token:
            print("PAT authentication successful, trying to create work item...")
            
            # Try REST API with PAT
            work_item, message = create_work_item_with_rest_api(
                organization_url, project, work_item_type, title, description, assignee, pat_token, use_pat=True
            )
            if work_item:
                return work_item, "Success with PAT (REST API)"
            
            # Try Python client with PAT
            work_item, message = create_work_item_with_python_client(
                organization_url, project, work_item_type, title, description, assignee, pat_token, use_pat=True
            )
            if work_item:
                return work_item, "Success with PAT (Python client)"
        else:
            print(f"PAT authentication failed: {pat_message}")
        
        # Method 2: Try Azure CLI authentication
        print("Attempting Azure CLI authentication...")
        cli_token, cli_message = authenticate_azure_cli_powershell()
        if cli_token:
            print("Azure CLI authentication successful, trying to create work item...")
            
            # Try REST API with Azure CLI token
            work_item, message = create_work_item_with_rest_api(
                organization_url, project, work_item_type, title, description, assignee, cli_token, use_pat=False
            )
            if work_item:
                return work_item, "Success with Azure CLI (REST API)"
            
            # Try Python client with Azure CLI token
            work_item, message = create_work_item_with_python_client(
                organization_url, project, work_item_type, title, description, assignee, cli_token, use_pat=False
            )
            if work_item:
                return work_item, "Success with Azure CLI (Python client)"
        else:
            print(f"Azure CLI authentication failed: {cli_message}")
        
        # If all methods fail, return comprehensive error message
        error_msg = f"""
Authentication failed with all methods:
1. PAT authentication: {pat_message}
2. Azure CLI authentication: {cli_message}

To fix this issue:
Option 1 (Recommended): Use Personal Access Token
- Go to Azure DevOps → User settings → Personal access tokens
- Create a new token with Work Items (Read & Write) permissions
- Add it to your .env file as: ADO_PAT=your-token-here

Option 2: Fix Azure CLI permissions
- Run 'az login' in PowerShell
- Ensure your account has permissions in the Azure DevOps organization
- Try running: az devops configure --defaults organization={organization_url}
"""
        
        return None, error_msg.strip()
        
    except Exception as e:
        return None, f"Unexpected error in authentication: {e}"

def process_db_script(script_content, selected_manager, create_task=False):
    """Process the database script and optionally create a work item"""
    if not script_content.strip():
        return "Please enter a database script."
    
    # Get team name from the selected manager
    team_data = load_team_data()
    selected_team = "Unknown Team"
    
    for team_name, manager_name in team_data:
        if manager_name == selected_manager:
            selected_team = team_name
            break
    
    result = f"Original Script:\n{script_content}\n\n"
    result += f"Selected Team: {selected_team}\n"
    result += f"Manager: {selected_manager}\n\n"
    
    # Create work item if requested
    if create_task:
        result += "Creating Azure DevOps Task...\n"
        result += "-" * 40 + "\n"
        
        # Configuration for Azure DevOps
        organization_url = "https://dev.azure.com/tr-tax"
        project = "TaxProf"
        work_item_type = "Task"
        title = f"DB Script Task - {selected_team} Team"
        description = script_content
        assignee = selected_manager
        
        work_item, message = create_work_item_with_multiple_auth_methods(
            organization_url, project, work_item_type, title, description, assignee
        )
        
        if work_item:
            result += "✅ Task created successfully!\n"
            if hasattr(work_item, 'id'):
                # Python client response
                result += f"  Work Item ID: {work_item.id}\n"
                result += f"  Title: {work_item.fields['System.Title']}\n"
                result += f"  State: {work_item.fields['System.State']}\n"
                assigned_to = work_item.fields.get('System.AssignedTo', {})
                if isinstance(assigned_to, dict):
                    assigned_display = assigned_to.get('displayName', 'Unassigned')
                else:
                    assigned_display = str(assigned_to) if assigned_to else 'Unassigned'
                result += f"  Assigned To: {assigned_display}\n"
                result += f"  URL: {work_item.url}\n"
            else:
                # REST API response
                result += f"  Work Item ID: {work_item.get('id')}\n"
                result += f"  Title: {work_item.get('fields', {}).get('System.Title')}\n"
                result += f"  State: {work_item.get('fields', {}).get('System.State')}\n"
                assigned_to = work_item.get('fields', {}).get('System.AssignedTo')
                if isinstance(assigned_to, dict):
                    assigned_display = assigned_to.get('displayName', 'Unassigned')
                else:
                    assigned_display = str(assigned_to) if assigned_to else 'Unassigned'
                result += f"  Assigned To: {assigned_display}\n"
                result += f"  URL: {work_item.get('url', 'N/A')}\n"
            result += f"  Authentication method: {message}\n\n"
        else:
            result += f"❌ Failed to create task:\n{message}\n\n"
    
    result += f"Processed Script:\n{script_content}"
    
    return result

def create_db_script_maker_interface():
    """Create the Instant DB Script Maker interface"""
    with gr.Blocks(title="Instant DB Script Maker") as interface:
        gr.Markdown("""
        <div align='center'><h1>Instant DB Script Maker</h1></div>
        """)
        gr.Markdown("""
        <div align='center'>Enter your database script below, select a team, and optionally create an Azure DevOps task.</div>
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                script_input = gr.Textbox(
                    label="Database Script",
                    placeholder="Enter your SQL script here...\n\nExample:\nSELECT * FROM users WHERE id = 1;\nINSERT INTO products (name, quantity) VALUES ('Product1', 1);",
                    lines=15,
                    max_lines=20
                )
                
                # Load team data for dropdown
                team_choices = load_team_data()
                
                team_dropdown = gr.Dropdown(
                    choices=team_choices,
                    label="Select Team",
                    value=team_choices[0][1] if team_choices else None,
                    info="Select a team to associate with the database script"
                )
                
                create_task_checkbox = gr.Checkbox(
                    label="Create Azure DevOps Task",
                    value=False,
                    info="Check this to create a task in Azure DevOps with the script as description"
                )
                
                with gr.Row():
                    process_button = gr.Button("Process Script", variant="primary")
                    clear_button = gr.Button("Clear", variant="secondary")
            
            with gr.Column(scale=2):
                output_display = gr.Textbox(
                    label="Processed Output",
                    lines=15,
                    max_lines=20,
                    interactive=False
                )
        
        # Event handlers
        process_button.click(
            fn=process_db_script,
            inputs=[script_input, team_dropdown, create_task_checkbox],
            outputs=output_display
        )
        
        clear_button.click(
            fn=lambda: ("", "", False),
            outputs=[script_input, output_display, create_task_checkbox]
        )
        
        script_input.submit(
            fn=process_db_script,
            inputs=[script_input, team_dropdown, create_task_checkbox],
            outputs=output_display
        )
    
    return interface

# Function to launch the interface in a new tab
def launch_db_script_maker():
    """Launch the DB Script Maker in a new tab"""
    interface = create_db_script_maker_interface()
    interface.launch(
        server_name="127.0.0.3",
        server_port=7881,  # Different port to avoid conflicts
        share=False,
        show_error=True,
        inbrowser=True
    )

if __name__ == "__main__":
    launch_db_script_maker()
