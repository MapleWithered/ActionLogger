# Function to prompt user with a default value
function Get-UserInputWithDefault {
    param (
        [string]$PromptMessage,
        [string]$DefaultValue
    )
    $user_input = Read-Host "$PromptMessage (Default as $DefaultValue)"
    if (-not [string]::IsNullOrWhiteSpace($user_input)) {
        Write-Host "Using: $user_input"
        return $user_input
    } else {
        Write-Host "Using default value: $DefaultValue"
        return $DefaultValue
    }
}

# Ask for Program install path with default
$programInstallPath = Get-UserInputWithDefault "Enter the Program Install Path" "$env:LocalAppData\Programs\ActionLogger"

# Ask for Log output path with default
$logOutputPath = Get-UserInputWithDefault "Enter the Log Output Path" "$env:LocalAppData\ActionLogger\logs"

# Ask if should start on windows startup with default value Y
$startOnStartup = Get-UserInputWithDefault "Start on Windows Startup? [Y/n]" "Y"

# Initialize startup variables
$startupLinkPath = ""
$startupDir = ""

if ($startOnStartup -ieq "Y") {
    # Ask for startup directory if starting on windows startup
    $startupDir = Get-UserInputWithDefault "Enter the Startup Directory" "$env:AppData\Microsoft\Windows\Start Menu\Programs\Startup"
    $startupLinkPath = "$startupDir\ActionLogger.lnk"
}

# Generate uninstaller script with forceful termination of actionlogger.exe
$uninstallerScriptPath = ".\uninstaller.ps1"
$uninstallScriptContent = @"
# Uninstaller script to remove program files and startup link

# Stop actionlogger.exe if running
if (Get-Process -Name actionlogger -ErrorAction SilentlyContinue) {
    Write-Host "Stopping actionlogger"
    Stop-Process -Name actionlogger -Force
    # Sleep for 1 second to ensure the process is stopped
    Start-Sleep -Seconds 1
}

# Remove Program Install Path
Remove-Item -Recurse -Force "$programInstallPath"

# Remove Startup Link if exists
if (Test-Path "$startupLinkPath") {
    Remove-Item -Force "$startupLinkPath"
}
if (Test-Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\ActionLogger.lnk") {
    Remove-Item -Force "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\ActionLogger.lnk"
}

Write-Host "ActionLogger uninstalled successfully."
"@
$uninstallScriptContent | Out-File -FilePath "$uninstallerScriptPath" -Encoding UTF8

# Start installation

# Stop the program
$processName = 'actionlogger'
$process = Get-Process -Name $processName -ErrorAction SilentlyContinue
if ($process) {
    Write-Host "Stopping $processName"
    Stop-Process -Name $processName -Force
}

# Check if the target folder exists
if (Test-Path "$programInstallPath") {
    # Delete the folder and recreate it
    Write-Host "Deleting older binary folder $programInstallPath"
    Remove-Item -Path "$programInstallPath" -Recurse -Force
    Write-Host "Creating new binary folder $programInstallPath"
    New-Item -Path "$programInstallPath" -ItemType Directory | Out-Null
} else {
    # Create the folder and its parent folders
    Write-Host "Creating new binary folder $programInstallPath"
    New-Item -Path "$programInstallPath" -ItemType Directory -Force | Out-Null
}

# Copy uninstaller script to programInstallPath
Write-Host "Copying uninstaller script to $programInstallPath"
Copy-Item -Path "$uninstallerScriptPath" -Destination "$programInstallPath" -Force

# Check if the log output folder exists. If not, create it
if (-not (Test-Path "$logOutputPath")) {
    Write-Host "Creating log output folder $logOutputPath"
    New-Item -Path "$logOutputPath" -ItemType Directory -Force | Out-Null
}

# Copy all files in folder to programInstallPath
$distFolderPath = ".\dist\actionlogger"
Write-Host "Copying all files in $distFolderPath to $programInstallPath"
Copy-Item -Path "$distFolderPath\*" -Destination "$programInstallPath" -Force -Recurse

# Copy vendor files (icon, blacklist rules) from ./vendor/* to the programInstallPath
Write-Host "Copying vendor files to $programInstallPath"
$vendorFolderPath = ".\vendor"
Copy-Item -Path "$vendorFolderPath\*" -Destination "$programInstallPath" -Force -Recurse

# Create shortcut for actionlogger.exe in the startup folder
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($startupLinkPath)
$shortcut.TargetPath = "$programInstallPath\actionlogger.exe"
$shortcut.Save()

# Write path to config.txt
$configFilePath = "$programInstallPath\config.txt"
@"
$logOutputPath
"@ | Out-File -FilePath "$configFilePath" -Encoding UTF8

Write-Host "Setup completed. Configuration and uninstaller script have been created."

# Ask if should create start menu shortcut
$createStartMenuShortcut = Get-UserInputWithDefault "Create start menu shortcut? [Y/n]" "Y"

if ($createStartMenuShortcut -ieq "Y") {
    # Create start menu shortcut under user profile
    $shortcutPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\ActionLogger.lnk"
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "$programInstallPath\actionlogger.exe"
    $shortcut.Save()
}
