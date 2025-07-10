# ADOBuddy Authentication Fix

## Problem
If you're getting the error `TF400813: The user 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa' is not authorized to access this resource`, this means the authentication method is not properly configured for your Azure DevOps organization.

## Solution

### Option 1: Personal Access Token (PAT) - Recommended

1. **Create a PAT Token:**
   - Go to [Azure DevOps](https://dev.azure.com/tr-tax)
   - Click your profile picture (top right) ? "Personal access tokens"
   - Click "New Token"
   - Name: `ADOBuddy Token`
   - Scope: Select "Custom defined"
   - Check "Work Items" with "Read & Write" permissions
   - Click "Create" and copy the token immediately

2. **Configure the token:**
   - Open the `.env` file in your project directory
   - Replace `your-personal-access-token` with your actual token:
     ```
     ADO_PAT=your-actual-token-here
     ```

3. **Quick Setup:**
   ```bash
   python setup_auth.py
   ```

### Option 2: Azure CLI Authentication

1. **Install Azure CLI** (if not already installed):
   - Download from [Microsoft Docs](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

2. **Login to Azure CLI:**
   ```powershell
   az login
   ```

3. **Set default organization:**
   ```powershell
   az devops configure --defaults organization=https://dev.azure.com/tr-tax
   ```

4. **Verify permissions:**
   - Ensure your Azure account has permissions in the `tr-tax` organization
   - You should be added as a member with appropriate work item permissions

## What's Fixed

The updated `InstantDBScriptMaker.py` now includes:

1. **Multiple Authentication Methods:** 
   - PAT authentication (most reliable)
   - Azure CLI authentication (fallback)
   - Better error handling

2. **Improved Token Handling:**
   - Better Azure CLI token scoping
   - Proper authentication headers
   - Fallback between REST API and Python client

3. **Enhanced Error Messages:**
   - Clear instructions on how to fix authentication issues
   - Step-by-step troubleshooting guide

## Testing Authentication

Run the setup script to test your authentication:

```bash
python setup_auth.py
```

This will:
- Check if Azure CLI is installed and logged in
- Help you set up PAT authentication
- Test both authentication methods
- Provide clear feedback on what's working

## Troubleshooting

### Common Issues:

1. **"No valid PAT found"**
   - Make sure you've created a `.env` file with your PAT token
   - Ensure the token has Work Items (Read & Write) permissions

2. **"Not logged in to Azure CLI"**
   - Run `az login` in PowerShell
   - Complete the browser authentication flow

3. **"Failed to get access token"**
   - Your Azure account might not have permissions in the organization
   - Contact your Azure DevOps administrator

4. **"TF400813: The user is not authorized"**
   - This usually means insufficient permissions
   - Use PAT authentication instead of Azure CLI
   - Ensure your PAT token has the right scopes

### Getting Help

If you're still having issues:
1. Run `python setup_auth.py` to diagnose the problem
2. Check the error messages in the output
3. Verify your permissions in Azure DevOps
4. Consider using PAT authentication as it's more reliable

## Security Notes

- Keep your PAT token secure and don't share it
- PAT tokens expire - you'll need to regenerate them periodically
- The `.env` file is included in `.gitignore` to prevent accidental commits
- Never commit your PAT token to version control