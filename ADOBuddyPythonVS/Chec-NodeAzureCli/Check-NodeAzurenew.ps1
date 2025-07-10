try {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Node.js & Azure CLI Setup Checker   " -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
      Write-Host "Checking if Node.js is installed..." -ForegroundColor Yellow
    $node = Get-Command node
    if ($null -eq $node)
    {
        Write-Host "Node.js is not installed." -ForegroundColor Red        
        Write-Host "Opening Company Portal to install Node.js..." -ForegroundColor Blue
        $nodePortalLink = "companyportal:ApplicationId=b7c680c3-72b6-49a9-bd03-eae6ec267ddb"
        Write-Host "Opening Company Portal..." -ForegroundColor Blue
        Start-Process $nodePortalLink
    } 
    else 
    {   
        $nodeVersion = node --version
        Write-Host "Node.js version found: $nodeVersion" -ForegroundColor Green
        $versionNumber = $nodeVersion -replace "[vV]", "" | ForEach-Object { $_.Split(".")[0] }        
        if ([int]$versionNumber -lt 22) 
        {
            Write-Host "Node.js version is below 22. Update required." -ForegroundColor Yellow
            Write-Host "Opening Company Portal to update Node.js..." -ForegroundColor Blue
            $nodeUpdateLink = "companyportal:ApplicationId=b7c680c3-72b6-49a9-bd03-eae6ec267ddb"
            Write-Host "Opening Company Portal..." -ForegroundColor Blue
            Start-Process $nodeUpdateLink        
        } 
        else 
        {
            Write-Host "Checking if Azure CLI is installed..." -ForegroundColor Yellow
            $az = Get-Command az            
            if ($null -eq $az) 
            {
                Write-Host "Azure CLI is not installed." -ForegroundColor Red
                Write-Host "Opening Company Portal to install Azure CLI..." -ForegroundColor Blue
                $azurePortalLink = "companyportal:ApplicationId=47cc165b-a1eb-4183-8c60-9f2c415102d9"
                Write-Host "Opening Company Portal..." -ForegroundColor Blue               
                Start-Process $azurePortalLink
            } 
            else 
            {
                Write-Host "Checking Azure CLI login status..." -ForegroundColor Yellow
                az account show 2>$null | Out-Null                  
                if ($LASTEXITCODE -eq 0) 
                {
                    Write-Host "Azure CLI is logged in." -ForegroundColor Green
                    Write-Host "Current Azure account details:" -ForegroundColor Cyan
                    az account show --output table
                    $userEmail = az account show --query "user.name" --output tsv
                    Write-Host "Logged in user email: $userEmail" -ForegroundColor Green
                } 
                else
                {
                    Write-Host "Azure CLI is not logged in." -ForegroundColor Red
                    Write-Host "Running 'az login' to sign in..." -ForegroundColor Blue
                    az login
                }
            }
        }
    }
} 
finally 
{
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "    Setup Check Complete!             " -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}
