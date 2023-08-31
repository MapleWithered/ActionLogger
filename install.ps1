$folderPath = "C:\temp\action_log\bin"
$distFolderPath = ".\dist\actionlogger"
$vendorFolderPath = ".\vendor"

# Check if the folder exists
if (Test-Path $folderPath) {
    # Delete the folder and recreate it
    Write-Host "Deleting older binary folder $folderPath"
    Remove-Item -Path $folderPath -Recurse -Force
    Write-Host "Creating new binary folder $folderPath"
    New-Item -Path $folderPath -ItemType Directory | Out-Null
} else {
    # Create the folder and its parent folders
    Write-Host "Creating new binary folder $folderPath"
    New-Item -Path $folderPath -ItemType Directory -Force | Out-Null
}

# Copy all files in folder to action_log\bin folder
Write-Host "Copying all files in $distFolderPath to $folderPath"
Copy-Item -Path "$distFolderPath\*" -Destination $folderPath -Force -Recurse

# Copy favicon.ico to the action_log\bin folder
Write-Host "Copying favicon.ico to $folderPath"
Copy-Item -Path ".\favicon.ico" -Destination "$folderPath\favicon.ico" -Force
