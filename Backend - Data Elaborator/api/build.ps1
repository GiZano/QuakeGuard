param(
    [string]$Version = "latest",
    [switch]$Push = $false
)

$GitHubUsername = "gizano"
$GitHubRepo = "earthquake-data-server"
$ImageName = "ghcr.io/$GitHubUsername/$GitHubRepo"
$GitHubToken = $env:GITHUB_TOKEN

Write-Host "Building: $ImageName`:$Version"

# Build
docker build -t "$ImageName`:$Version" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed"
    exit 1
}
Write-Host "Build OK"

# Test
docker run -d --name test-container "$ImageName`:$Version"
Start-Sleep -Seconds 2
docker logs test-container
docker stop test-container
docker rm test-container
Write-Host "Test OK"

# Push
if ($Push) {
    Write-Host "Pushing to GHCR..."
    
    if (-not $GitHubToken) {
        Write-Host "Token needed"
        $GitHubToken = Read-Host -Prompt "Enter GitHub Token" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($GitHubToken)
        $GitHubToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    }
    
    echo $GitHubToken | docker login ghcr.io -u $GitHubUsername --password-stdin
    
    if ($LASTEXITCODE -eq 0) {
        docker push "$ImageName`:$Version"
        Write-Host "Pushed to GHCR!"
        Write-Host "URL: https://github.com/$GitHubUsername/$GitHubRepo/pkgs/container/$GitHubRepo"
    } else {
        Write-Host "GHCR login failed"
        exit 1
    }
}

Write-Host "Done: $ImageName`:$Version"