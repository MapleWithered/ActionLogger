$folderPath = "C:\temp\action_log\bin"
$distFolderPath = ".\dist\main"
$vendorFolderPath = ".\vendor"

Write-Host "Stopping the service"
Start-Process -FilePath "$folderPath\winsw.exe" -ArgumentList "stop" -Wait
Write-Host "Uninstalling the service"
Start-Process -FilePath "$folderPath\winsw.exe" -ArgumentList "uninstall" -Wait