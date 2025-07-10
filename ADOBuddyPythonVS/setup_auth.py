"""
Setup script for ADOBuddy - Azure DevOps Helper
This script helps configure authentication for Azure DevOps integration.
"""

import os
import sys
import subprocess
import json

def check_azure_cli():
    """Check if Azure CLI is installed and working"""
    try:
        result = subprocess.run(["az", "--version"], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("? Azure CLI is installed and working")
            return True
        else:
            print("? Azure CLI is not working properly")
            return False
    except FileNotFoundError:
        print("? Azure CLI is not installed")
        return False

def check_azure_cli_login():
    """Check if user is logged in to Azure CLI"""
    try:
        result = subprocess.run(["az", "account", "show"], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            account_info = json.loads(result.stdout)
            print(f"? Logged in to Azure CLI as: {account_info.get('user', {}).get('name', 'Unknown')}")
            return True
        else:
            print("? Not logged in to Azure CLI")
            return False
    except Exception as e:
        print(f"? Error checking Azure CLI login: {e}")
        return False

def setup_pat_token():
    """Guide user through PAT token setup"""
    print("\n" + "="*60)
    print("PERSONAL ACCESS TOKEN (PAT) SETUP")
    print("="*60)
    print("\nPersonal Access Token is the most reliable authentication method.")
    print("\nTo create a PAT token:")
    print("1. Go to https://dev.azure.com/tr-tax")
    print("2. Click on your profile picture (top right)")
    print("3. Select 'Personal access tokens'")
    print("4. Click 'New Token'")
    print("5. Give it a name (e.g., 'ADOBuddy Token')")
    print("6. Select 'Custom defined' scope")
    print("7. Check 'Work Items' with 'Read & Write' permissions")
    print("8. Click 'Create'")
    print("9. Copy the token (it won't be shown again!)")
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    token = input("\nEnter your PAT token (or press Enter to skip): ").strip()
    
    if token:
        # Update .env file
        env_content = ""
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_content = f.read()
        
        # Replace or add PAT token
        lines = env_content.split('\n')
        pat_updated = False
        
        for i, line in enumerate(lines):
            if line.startswith('ADO_PAT='):
                lines[i] = f'ADO_PAT={token}'
                pat_updated = True
                break
        
        if not pat_updated:
            lines.append(f'ADO_PAT={token}')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"? PAT token saved to {env_file}")
        print("??  Keep this token secure and don't share it!")
        return True
    else:
        print("??  PAT token setup skipped")
        return False

def test_authentication():
    """Test authentication methods"""
    print("\n" + "="*60)
    print("TESTING AUTHENTICATION")
    print("="*60)
    
    # Test PAT authentication
    try:
        from InstantDBScriptMaker import authenticate_with_pat
        pat_token, pat_message = authenticate_with_pat()
        if pat_token:
            print("? PAT authentication: SUCCESS")
        else:
            print(f"? PAT authentication: {pat_message}")
    except Exception as e:
        print(f"? PAT authentication test failed: {e}")
    
    # Test Azure CLI authentication
    try:
        from InstantDBScriptMaker import authenticate_azure_cli_powershell
        cli_token, cli_message = authenticate_azure_cli_powershell()
        if cli_token:
            print("? Azure CLI authentication: SUCCESS")
        else:
            print(f"? Azure CLI authentication: {cli_message}")
    except Exception as e:
        print(f"? Azure CLI authentication test failed: {e}")

def main():
    """Main setup function"""
    print("="*60)
    print("ADOBuddy Setup - Azure DevOps Authentication")
    print("="*60)
    
    # Check Azure CLI
    azure_cli_ok = check_azure_cli()
    if azure_cli_ok:
        azure_cli_logged_in = check_azure_cli_login()
        if not azure_cli_logged_in:
            print("\nTo login to Azure CLI, run: az login")
    
    # Setup PAT token
    pat_setup = setup_pat_token()
    
    # Test authentication
    test_authentication()
    
    print("\n" + "="*60)
    print("SETUP COMPLETE")
    print("="*60)
    
    if pat_setup:
        print("? You're ready to use ADOBuddy with PAT authentication!")
    elif azure_cli_logged_in:
        print("? You can use ADOBuddy with Azure CLI authentication!")
    else:
        print("??  Please complete either PAT or Azure CLI setup to use ADOBuddy")
    
    print("\nYou can now run the InstantDBScriptMaker.py script.")

if __name__ == "__main__":
    main()