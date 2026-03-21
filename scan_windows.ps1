param (
    [string]$OutputDir = "$PSScriptRoot\scans\Manual_Run"
)

if (-not (Test-Path $OutputDir)) {
    New-Item -Path $OutputDir -ItemType Directory -Force | Out-Null
}

Write-Output ">> [INIT] Starting local telemetry collection pipeline..."
Write-Output ">> [INIT] Target payload directory: $OutputDir"

# ------------------------------------------------------------------------
# 1. WINDOWS DEFENDER EXCLUSIONS
# ------------------------------------------------------------------------
Write-Output ">> [1/8] Verifying Windows Defender exclusions and security policies..."
try {
    Get-MpPreference | 
        Select-Object ExclusionPath, ExclusionExtension, ExclusionProcess | 
        ConvertTo-Json -Depth 2 | 
        Set-Content "$OutputDir\defender_exclusions.json" -Encoding UTF8
} catch {
    Set-Content "$OutputDir\defender_exclusions.json" -Value '{ "error": "Insufficient privileges to query Defender policies." }' -Encoding UTF8
}

# ------------------------------------------------------------------------
# 2. STARTUP PROGRAMS
# ------------------------------------------------------------------------
Write-Output ">> [2/8] Extracting startup persistence hooks..."
Get-CimInstance Win32_StartupCommand | 
    ForEach-Object {
        $rawCmd = $_.Command
        $cleanPath = $rawCmd
        $hash = "N/A"

        if ($rawCmd -match '^"([^"]+)"') {
            $cleanPath = $matches[1]
        } elseif ($rawCmd -match " ") {
            if (-not (Test-Path $rawCmd -ErrorAction SilentlyContinue)) {
                $cleanPath = ($rawCmd -split " ")[0]
            }
        }

        if ($cleanPath -and (Test-Path $cleanPath -PathType Leaf)) {
            try { $hash = (Get-FileHash $cleanPath -Algorithm SHA256 -ErrorAction Stop).Hash } 
            catch { $hash = "ACCESS_ERROR" }
        } else {
            $hash = "FILE_NOT_FOUND_OR_COMPLEX_PATH"
        }

        [PSCustomObject]@{
            Name        = $_.Name
            User        = $_.User
            Location    = $_.Location
            Command     = $rawCmd
            Hash_SHA256 = $hash
        }
    } | ConvertTo-Json -Depth 2 | Set-Content "$OutputDir\startup.json" -Encoding UTF8

# ------------------------------------------------------------------------
# 3. ACTIVE PROCESSES
# ------------------------------------------------------------------------
Write-Output ">> [3/8] Performing cryptographic validation on active processes (This may take a moment)..."

$MicrosoftRegex = "^(Microsoft Corporation|Microsoft Windows|Microsoft Ostc|GitHub|Skype)"
$BigTechRegex   = "^(Google|NVIDIA|Intel|AMD|Advanced Micro Devices|ASUSTeK|Adobe|Mozilla|Conexant|Realtek|HP Inc\.|Hewlett-Packard|Dell|Lenovo|Logitech|Synaptics|Oracle|Apple|Cisco|Amazon|Dropbox|Zoom|Slack|Spotify|Valve|Epic Games|Samsung|Qualcomm|Broadcom|VMware|Citrix|TeamViewer|Western Digital|Seagate|McAfee|Symantec|Norton|Bitdefender|Kaspersky|Avast|AVG|Malwarebytes|Fortinet|Palo Alto|CrowdStrike|Trend Micro|Sophos|ESET|Brave Software)"

Get-CimInstance Win32_Process | Select-Object Name, ProcessId, ExecutablePath, CommandLine | Sort-Object Name |
    ForEach-Object {
        $hash = "N/A"
        $signer = "UNVERIFIED"
        $sigStatus = "N/A"
        $llmFlag = "[ANALYZE_HASH]" 
        
        $rawPath = $_.ExecutablePath
        $fullCommand = $_.CommandLine 

        $cleanPath = $rawPath
        if ($cleanPath) {
            $cleanPath = $cleanPath.Trim('"')
            if ($cleanPath -match "^\\\\\?\\") { $cleanPath = $cleanPath.Substring(4) }
        }

        if ($cleanPath -and (Test-Path $cleanPath -PathType Leaf)) {
            try { $hash = (Get-FileHash $cleanPath -Algorithm SHA256 -ErrorAction Stop).Hash } 
            catch { $hash = "HASH_ERROR" }
            
            $sig = Get-AuthenticodeSignature $cleanPath -ErrorAction SilentlyContinue
            $sigStatus = $sig.Status
            
            $rawSubject = $sig.SignerCertificate.Subject
            if ($rawSubject -match "CN=([^,]+)") { $cleanSigner = $matches[1] } else { $cleanSigner = $rawSubject }

            if ($sigStatus -eq 'Valid') {
                $signer = $cleanSigner
                if ($signer -match $MicrosoftRegex -or $signer -match $BigTechRegex) { 
                    return 
                } 
                $llmFlag = "[THIRD_PARTY_SIGNATURE]"

            } elseif ($sigStatus -eq 'HashMismatch') {
                $llmFlag = "[DANGER_ALTERED_SIGNATURE]"
                if ([string]::IsNullOrWhiteSpace($cleanSigner)) { 
                    $signer = "Broken Signature (Unknown Origin)" 
                } else { 
                    $signer = "CLAIMS TO BE: $cleanSigner (INVALID SIGNATURE)" 
                }

            } else {
                $signer = "NOT_SIGNED ($sigStatus)"
                if ($cleanPath -match "^C:\\Windows\\(System32|SysWOW64)\\" -and $sigStatus -eq "NotSigned") {
                    $llmFlag = "[SYSTEM_CATALOG_CHECK]"
                } else { 
                    $llmFlag = "[UNSIGNED_ALERT]" 
                }
            }
        } elseif (-not $cleanPath) {
            $llmFlag = "[INFO_KERNEL]"
            $signer = "Kernel/System"
            return
        } else {
            $llmFlag = "[PATH_ERROR]"
            return
        }
        
        $finalObject = [ordered]@{
            SIGNATURE_FLAG = $llmFlag
            Name           = $_.Name
            PID            = $_.ProcessId
            Signer_Info    = $signer
            Command_Line   = $fullCommand
            Hash_SHA256    = $hash
        }

        if ([string]::IsNullOrWhiteSpace($fullCommand) -or ($rawPath -and -not $fullCommand.ToLower().Contains($rawPath.ToLower()))) {
            $finalObject["Path_Explicit"] = $rawPath
        }

        [PSCustomObject]$finalObject
    } | ConvertTo-Json -Depth 2 | Set-Content "$OutputDir\procesos_activos.json" -Encoding UTF8

# ------------------------------------------------------------------------
# 4. WINDOWS SERVICES
# ------------------------------------------------------------------------
Write-Output ">> [4/8] Mapping system services..."
Get-CimInstance Win32_Service | Select-Object DisplayName, Name, PathName, State | 
    ConvertTo-Json -Depth 2 | Set-Content "$OutputDir\servicios.json" -Encoding UTF8

# ------------------------------------------------------------------------
# 5. NETWORK CONNECTIONS
# ------------------------------------------------------------------------
Write-Output ">> [5/8] Auditing active network connections (Netstat)..."
Get-NetTCPConnection | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess, 
        @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} |
    ConvertTo-Json -Depth 2 | Set-Content "$OutputDir\netstat.json" -Encoding UTF8

# ------------------------------------------------------------------------
# 6. SCHEDULED TASKS
# ------------------------------------------------------------------------
Write-Output ">> [6/8] Analyzing scheduled tasks and resolving COM objects..."

function Resolve-COMPath {
    param ($guidInput)
    $cleanId = $guidInput.ToString().Trim('{}')
    $guid = "{$cleanId}"; $paths = @()
    $subkeys = @("InProcServer32", "LocalServer32") 
    $baseRegPaths = @("Registry::HKEY_CLASSES_ROOT\CLSID\$guid", "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Wow6432Node\CLSID\$guid")

    foreach ($basePath in $baseRegPaths) {
        foreach ($k in $subkeys) {
            $fullPath = "$basePath\$k"
            if (Test-Path $fullPath) {
                $val = (Get-ItemProperty $fullPath -ErrorAction SilentlyContinue).'(default)'
                if ($val) { 
                    $cleanVal = $val -replace '"',''
                    $expanded = [Environment]::ExpandEnvironmentVariables($cleanVal)
                    if ($expanded -and ($paths -notcontains $expanded)) { $paths += $expanded }
                }
            }
        }
    }
    if ($paths.Count -gt 0) { return $paths -join " | " }
    return $null
}

Get-ScheduledTask | ForEach-Object {
    $actionStr = ""
    if ($_.Actions) {
        $actionStr = ($_.Actions | ForEach-Object { 
            if ($_.Execute) { "$($_.Execute) $($_.Arguments)".Trim() }
            elseif ($_.ClassId) { 
                $cleanId = $_.ClassId.ToString().Trim('{}')
                $displayGuid = "{$cleanId}"
                $realFile = Resolve-COMPath -guidInput $displayGuid
                if ($realFile) { "COM: $displayGuid -> FILE: $realFile" } else { "COM: $displayGuid (Not resolved in registry)" }
            }
            else { $_.ToString() }
        }) -join ' || '
    }

    [PSCustomObject]@{ 
        TaskName  = $_.TaskName
        Path      = $_.TaskPath
        TaskToRun = $actionStr
        RunAs     = $_.Principal.UserId
        State     = $_.State 
    }
} | Where-Object { -not [string]::IsNullOrWhiteSpace($_.TaskToRun) } | ConvertTo-Json -Depth 3 | 
    ForEach-Object { $_ -replace '\\u003e', '>' } | Set-Content "$OutputDir\tasks.json" -Encoding UTF8

# ------------------------------------------------------------------------
# 7. EXTENSIONS
# ------------------------------------------------------------------------
Write-Output ">> [7/8] Reviewing browser and developer extensions..."
$extensionsReport = @()

$vscodePath = "$env:USERPROFILE\.vscode\extensions"
if (Test-Path $vscodePath) { Get-ChildItem $vscodePath -Directory | ForEach-Object { $extensionsReport += [PSCustomObject]@{ Type = "VSCode Extension"; Name = $_.Name; Path = $_.FullName } } }

$antigravityPath = "$env:USERPROFILE\.antigravity\extensions"
if (Test-Path $antigravityPath) { Get-ChildItem $antigravityPath -Directory | ForEach-Object { $extensionsReport += [PSCustomObject]@{ Type = "Antigravity Extension"; Name = $_.Name; Path = $_.FullName } } }

$browserPaths = @{ "Chrome" = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Extensions"; "Edge" = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Extensions" }
foreach ($browser in $browserPaths.GetEnumerator()) {
    if (Test-Path $browser.Value) {
        Get-ChildItem $browser.Value -Directory | ForEach-Object {
            $manifestPath = "$($_.FullName)\*\manifest.json"
            $manifest = Get-Item $manifestPath -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($manifest) {
                try {
                    $jsonContent = Get-Content $manifest.FullName -Raw | ConvertFrom-Json
                    $extName = $jsonContent.name
                    if ($extName -match "^__MSG_") { $extName = "System/Store App ($($_.Name))" }
                    $extensionsReport += [PSCustomObject]@{ Type = "$($browser.Key) Extension"; Name = $extName; ID = $_.Name; Path = $manifest.FullName }
                } catch {
                    $extensionsReport += [PSCustomObject]@{ Type = "$($browser.Key) Extension (Error Reading)"; ID = $_.Name }
                }
            }
        }
    }
}
$extensionsReport | ConvertTo-Json -Depth 2 | Set-Content "$OutputDir\app_extensions.json" -Encoding UTF8

# ------------------------------------------------------------------------
# 8. HOSTS FILE
# ------------------------------------------------------------------------
Write-Output ">> [8/8] Verifying HOSTS file integrity..."
$hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
if (Test-Path $hostsPath) {
    $hostsContent = Get-Content $hostsPath | Where-Object { $_ -notmatch "^\s*#" -and $_ -match "\w" }
    if ($hostsContent) { 
        $hostsContent | ConvertTo-Json -Depth 1 | Set-Content "$OutputDir\hosts_file.json" -Encoding UTF8 
    } else { 
        Set-Content "$OutputDir\hosts_file.json" -Value '[ "CLEAN SYSTEM: Original HOSTS file (Comments only)" ]' -Encoding UTF8 
    }
}

# ------------------------------------------------------------------------
# FINAL UNIFIED REPORT ASSEMBLY
# ------------------------------------------------------------------------
Write-Output ">> [ASSEMBLY] Aggregating telemetry into unified payload..."
$finalFile = "$OutputDir\complete_scan.txt"
$dataSources = @(
    @{ Title = "1. WINDOWS DEFENDER EXCLUSIONS (CRITICAL)"; File = "defender_exclusions.json" },
    @{ Title = "2. STARTUP PROGRAMS"; File = "startup.json" },
    @{ Title = "3. HOSTS FILE"; File = "hosts_file.json" },
    @{ Title = "4. EXTENSIONS (Browsers & VSCode)"; File = "app_extensions.json" },
    @{ Title = "5. ACTIVE PROCESSES"; File = "procesos_activos.json" },
    @{ Title = "6. NETWORK CONNECTIONS (Netstat)"; File = "netstat.json" },
    @{ Title = "7. WINDOWS SERVICES"; File = "servicios.json" },     
    @{ Title = "8. SCHEDULED TASKS"; File = "tasks.json" }	
)

Clear-Content $finalFile -ErrorAction SilentlyContinue

foreach ($item in $dataSources) {
    $path = "$OutputDir\$($item.File)"
    if (Test-Path $path) {
        $jsonContent = Get-Content $path -Raw -Encoding UTF8
        $block = "`n## $($item.Title)`nSTARTJSON`n$jsonContent`nENDJSON`n"
        Add-Content -Path $finalFile -Value $block -Encoding UTF8
        Write-Output ">> [OK] Processed module: $($item.Title)"
    }
}

Write-Output ">> [DONE] Telemetry collection completed successfully."