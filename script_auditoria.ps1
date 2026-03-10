New-Item -Path "C:\Users\$env:USERNAME\Desktop\ANALISIS-VIRUS" -ItemType Directory -Force

# --- NUEVO: Imprime las exclusiones de Windows Defender (CRÍTICO) ---
# Esto revela carpetas donde el antivirus tiene prohibido mirar.
try {
    Get-MpPreference | 
        Select-Object ExclusionPath, ExclusionExtension, ExclusionProcess | 
        ConvertTo-Json -Depth 2 | 
        Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\defender_exclusions.json" -Encoding UTF8
} catch {
    Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\defender_exclusions.json" -Value '{ "error": "No se pudo acceder a Defender o no hay permisos." }' -Encoding UTF8
}

# Imprime los procesos de inicio con HASH
Get-CimInstance Win32_StartupCommand | 
    ForEach-Object {
        $rawCmd = $_.Command
        $cleanPath = $rawCmd
        $hash = "N/A"

        # LÓGICA DE LIMPIEZA DE RUTA
        # 1. Si empieza por comillas, cogemos lo de dentro: "C:\Ruta\File.exe" /arg -> C:\Ruta\File.exe
        if ($rawCmd -match '^"([^"]+)"') {
            $cleanPath = $matches[1]
        } 
        # 2. Si no tiene comillas y parece tener argumentos: C:\Windows\notepad.exe /a -> C:\Windows\notepad.exe
        elseif ($rawCmd -match " ") {
            # Probamos si la ruta entera existe (por si es C:\Program Files\...)
            if (-not (Test-Path $rawCmd -ErrorAction SilentlyContinue)) {
                # Si no existe entera, asumimos que se corta en el primer espacio (común en system32)
                $cleanPath = ($rawCmd -split " ")[0]
            }
        }

        # CÁLCULO DE HASH
        if ($cleanPath -and (Test-Path $cleanPath -PathType Leaf)) {
            try {
                $hash = (Get-FileHash $cleanPath -Algorithm SHA256 -ErrorAction Stop).Hash
            } catch {
                $hash = "ERROR_ACCESO"
            }
        } else {
            $hash = "ARCHIVO_NO_ENCONTRADO_O_RUTA_COMPLEJA"
        }

        # Objeto final
        [PSCustomObject]@{
            Name        = $_.Name
            User        = $_.User
            Location    = $_.Location
            Command     = $rawCmd     # Comando original (Contexto para el LLM)
            Hash_SHA256 = $hash       # La prueba forense
        }
    } | 
    ConvertTo-Json -Depth 2 | 
    Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\startup.json" -Encoding UTF8

# Imprime los procesos activos con sus rutas

# --- VERSIÓN 8.0: OPTIMIZADA (Ahorro de Tokens + Flags Neutras) ---
Write-Host "Analizando procesos (Lógica Condicional de Rutas)..." -ForegroundColor Cyan

# Patrones de confianza (Tus regex actualizados)
$MicrosoftRegex = "^(Microsoft Corporation|Microsoft Windows|Microsoft Ostc)"
$BigTechRegex   = "^(Google LLC|NVIDIA|Intel|AMD|ASUSTeK|Adobe|Mozilla|Conexant|Realtek|HP Inc\.|Dell|Lenovo|Logitech|Synaptics|Oracle)"

Get-CimInstance Win32_Process | 
    Select-Object Name, ProcessId, ExecutablePath, CommandLine | 
    Sort-Object Name |
    ForEach-Object {
        # Inicialización
        $hash = "N/A"
        $signer = "SIN_VERIFICAR"
        $sigStatus = "N/A"
        $etiquetaLLM = "[ANALIZAR_HASH]" 
        
        # DATOS CRUDOS
        $rawPath = $_.ExecutablePath
        $fullCommand = $_.CommandLine 

        # PREPARACIÓN DE RUTA LIMPIA (Solo para uso interno)
        $cleanPath = $rawPath
        if ($cleanPath) {
            $cleanPath = $cleanPath.Trim('"')
            if ($cleanPath -match "^\\\\\?\\") { $cleanPath = $cleanPath.Substring(4) }
        }

        # Comprobamos si el archivo existe usando la ruta limpia
        if ($cleanPath -and (Test-Path $cleanPath -PathType Leaf)) {
            
            # 1. HASH
            try {
                $hash = (Get-FileHash $cleanPath -Algorithm SHA256 -ErrorAction Stop).Hash
            } catch {
                $hash = "ERROR_HASH"
            }

            # 2. FIRMA DIGITAL
            $sig = Get-AuthenticodeSignature $cleanPath -ErrorAction SilentlyContinue
            $sigStatus = $sig.Status
            
            # Nombre del firmante
            $rawSubject = $sig.SignerCertificate.Subject
            if ($rawSubject -match "CN=([^,]+)") { 
                $cleanSigner = $matches[1] 
            } else {
                $cleanSigner = $rawSubject
            }

            # --- LÓGICA DE SEGURIDAD NEUTRA ---
            
            if ($sigStatus -eq 'Valid') {
                $signer = $cleanSigner
                if ($signer -match $MicrosoftRegex) {
                    $etiquetaLLM = "[MICROSOFT]"
                } elseif ($signer -match $BigTechRegex) {
                    $etiquetaLLM = "[BIGTECH]"
                } else {
                    $etiquetaLLM = "[FIRMA_TERCEROS]" 
                }

            } elseif ($sigStatus -eq 'HashMismatch') {
                $etiquetaLLM = "[PELIGRO_FIRMA_ALTERADA]"
                if ([string]::IsNullOrWhiteSpace($cleanSigner)) {
                    $signer = "Firma Rota (Origen Desconocido)"
                } else {
                    $signer = "DICE SER: $cleanSigner (FIRMA INVALIDA)"
                }

            } else {
                # NotSigned o error
                $signer = "NO_FIRMADO ($sigStatus)"
                if ($cleanPath -match "^C:\\Windows\\(System32|SysWOW64)\\" -and $sigStatus -eq "NotSigned") {
                    $etiquetaLLM = "[SISTEMA_CATALOGO_REVISAR]"
                } else {
                    $etiquetaLLM = "[ALERTA_SIN_FIRMA]"
                }
            }

        } elseif (-not $cleanPath) {
            $etiquetaLLM = "[INFO_KERNEL]"
            $signer = "Kernel/System"
        } else {
            $etiquetaLLM = "[ERROR_RUTA]"
        }
        
        # --- CONSTRUCCIÓN DEL OBJETO CONDICIONAL ---
        # Usamos [ordered] para mantener el orden visual, pero solo añadimos Path si hace falta.
        
        $finalObject = [ordered]@{
            SIGNATURE_FLAG = $etiquetaLLM
            Name           = $_.Name
            PID            = $_.ProcessId
            Signer_Info    = $signer   
            # Status_Firma = $sigStatus # Opcional: Descomentar si quieres el detalle técnico
            Command_Line   = $fullCommand
            Hash_SHA256    = $hash
        }

        # Lógica de Redundancia:
        # Si el comando está vacío O la ruta NO está contenida dentro del comando -> Añadimos la ruta explicita
        if ([string]::IsNullOrWhiteSpace($fullCommand) -or ($rawPath -and -not $fullCommand.ToLower().Contains($rawPath.ToLower()))) {
            # Insertamos el Path solo si es necesario para no perder el rastro
            $finalObject["Path_Explicit"] = $rawPath
        }

        # Devolvemos el objeto (PowerShell lo convertirá a JSON correctamente aunque tengan claves distintas)
        [PSCustomObject]$finalObject

    } |
    ConvertTo-Json -Depth 2 | 
    Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\procesos_activos.json" -Encoding UTF8

Write-Host "Análisis optimizado completado." -ForegroundColor Green

# Imprime los servicios de Windows 
# OPTIMIZABLE, podemos aqui analizar un archivo conocido (como el scheduler, que ocupa la gran mayoria) con hash y firma y ya está, si luego ese mismo archivo reaparece, pasamos de él
Get-CimInstance Win32_Service | 
    Select-Object DisplayName, Name, PathName, State | 
    ConvertTo-Json -Depth 2 | 
    Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\servicios.json" -Encoding UTF8

# Imprime las redes activas
Get-NetTCPConnection | 
    Select-Object `
        LocalAddress, `
        LocalPort, `
        RemoteAddress, `
        RemotePort, `
        State, `
        OwningProcess, `
        @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} |
    ConvertTo-Json -Depth 2 | 
    Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\netstat.json" -Encoding UTF8

# Imprime las tareas programadas 
# OPTIMIZAR: eliminar tareas COM
# Vale, yo creo que una forma de optimizar, tanto el LLM como velocidad, es extraer estas cadenas, por ejemplo windows 10/11, lo que sepamos que es seguro. Así quitamos los COM seguros, y quedan los raros si los hubiera. Esta misma técnica, de quitar cosas seguras/repetidas, podríamos hacerlo en general. Es un poco más tedioso, pero podemos generar whilelists, estrictas pero con muchos casos que sabemos que son seguros. (aquí lo dejo como idea, no hagas nada)
# Lo ideal sería un "filtro inteligente", que se mantenga durante la ejecución del Script, que se vaya llenando con los "archivos limpios" y cuando se vea algo repetido, pum, fuera en siguientes analisis
# O mejor, quitar por ejemplos los procesos firmados por BigTech/Microsoft de los procesos una vez que la firma está validada.

# Optimización COM: probablemente quitar el COM si se encontró el archivo sea lo mejor

# Imprime las tareas programadas (RESOLUCIÓN COM -> RUTA REAL | SIN FILTROS)
Write-Host "Analizando TODAS las tareas y resolviendo objetos COM..." -ForegroundColor Cyan

function Resolve-COMPath {
    param ($guidInput)
    
    # 1. Limpieza de GUID
    $cleanId = $guidInput.ToString().Trim('{}')
    $guid = "{$cleanId}"

    $paths = @()
    $subkeys = @("InProcServer32", "LocalServer32") 
    
    # Busca en registro normal y en nodo 32 bits
    $baseRegPaths = @(
        "Registry::HKEY_CLASSES_ROOT\CLSID\$guid",
        "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Wow6432Node\CLSID\$guid"
    )

    foreach ($basePath in $baseRegPaths) {
        foreach ($k in $subkeys) {
            $fullPath = "$basePath\$k"
            if (Test-Path $fullPath) {
                $val = (Get-ItemProperty $fullPath -ErrorAction SilentlyContinue).'(default)'
                if ($val) { 
                    $cleanVal = $val -replace '"',''
                    # Expande variables de entorno (%SystemRoot%, etc)
                    $expanded = [Environment]::ExpandEnvironmentVariables($cleanVal)
                    if ($expanded -and ($paths -notcontains $expanded)) {
                        $paths += $expanded 
                    }
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
            if ($_.Execute) { 
                "$($_.Execute) $($_.Arguments)".Trim() 
            }
            elseif ($_.ClassId) { 
                # Limpiamos el GUID para visualización y búsqueda
                $cleanId = $_.ClassId.ToString().Trim('{}')
                $displayGuid = "{$cleanId}"
                
                $realFile = Resolve-COMPath -guidInput $displayGuid
                
                if ($realFile) {
                    # Usamos una flecha simple para evitar problemas de JSON
                    "COM: $displayGuid -> ARCHIVO: $realFile" 
                } else {
                    "COM: $displayGuid (No resuelto en registro)"
                }
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
} | 
Where-Object { -not [string]::IsNullOrWhiteSpace($_.TaskToRun) } | 
ConvertTo-Json -Depth 3 | 
ForEach-Object { 
    # TRUCO: Reemplazamos el código unicode \u003e por el símbolo real >
    $_ -replace '\\u003e', '>' 
} | 
Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\tasks.json" -Encoding UTF8

Write-Host "Tareas exportadas. Símbolos corregidos." -ForegroundColor Green

# ANALIZAMOS EXTENSIONES: VSCODE, CHROME, EDGE
$extensionsReport = @()

# 1. AUDITORÍA DE VSCODE (Busca en la carpeta de usuario)
$vscodePath = "$env:USERPROFILE\.vscode\extensions"
if (Test-Path $vscodePath) {
    Get-ChildItem $vscodePath -Directory | ForEach-Object {
        $extensionsReport += [PSCustomObject]@{
            Type = "VSCode Extension"
            Name = $_.Name
            InstallDate = $_.CreationTime
            Path = $_.FullName
        }
    }
}

# 2. AUDITORÍA DE ANTIGRAVITY (Busca en la carpeta de usuario)
$antigravityPath = "$env:USERPROFILE\.antigravity\extensions"
if (Test-Path $antigravityPath) {
    Get-ChildItem $antigravityPath -Directory | ForEach-Object {
        $extensionsReport += [PSCustomObject]@{
            Type = "Antigravity Extension"
            Name = $_.Name
            InstallDate = $_.CreationTime
            Path = $_.FullName
        }
    }
}

# 2. AUDITORÍA DE NAVEGADORES (Chrome y Edge - Perfil Default)
$browserPaths = @{
    "Chrome" = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Extensions";
    "Edge"   = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Extensions"
}

foreach ($browser in $browserPaths.GetEnumerator()) {
    if (Test-Path $browser.Value) {
        Get-ChildItem $browser.Value -Directory | ForEach-Object {
            $manifestPath = "$($_.FullName)\*\manifest.json"
            $manifest = Get-Item $manifestPath -ErrorAction SilentlyContinue | Select-Object -First 1
            
            if ($manifest) {
                try {
                    # Leemos el JSON del manifiesto para sacar el nombre real
                    $jsonContent = Get-Content $manifest.FullName -Raw | ConvertFrom-Json
                    $extName = $jsonContent.name
                    # Si el nombre es una variable tipo __MSG_appName__, usamos el ID de carpeta
                    if ($extName -match "^__MSG_") { $extName = "System/Store App ($($_.Name))" }

                    $extensionsReport += [PSCustomObject]@{
                        Type = "$($browser.Key) Extension"
                        Name = $extName
                        ID = $_.Name
                        Path = $manifest.FullName
                    }
                } catch {
                    $extensionsReport += [PSCustomObject]@{
                        Type = "$($browser.Key) Extension (Error Reading)"
                        ID = $_.Name
                    }
                }
            }
        }
    }
}

# 3. GUARDAR TODO EN JSON
$extensionsReport | ConvertTo-Json -Depth 2 | Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\app_extensions.json" -Encoding UTF8

# Analizar archivo HOSTS
$hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
if (Test-Path $hostsPath) {
    # Leemos y filtramos
    $hostsContent = Get-Content $hostsPath | Where-Object { $_ -notmatch "^\s*#" -and $_ -match "\w" }
    
    # Si tras filtrar hay algo (es decir, hay modificaciones), guardamos el JSON
    if ($hostsContent) {
        $hostsContent | ConvertTo-Json -Depth 1 | Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\hosts_file.json" -Encoding UTF8
    } else {
        # Si está vacío (lo normal en un PC sano), guardamos un array vacío o mensaje para que el LLM lo sepa
        Set-Content "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\hosts_file.json" -Value '[ "SISTEMA LIMPIO: Archivo HOSTS original (Solo comentarios)" ]' -Encoding UTF8
    }
}

#A PARTIR DE AQUI SE GENERA EL PROMPT
# NOTA: habría que mejorarlo para que la salida final fuera: haz esto, en función del resultado, dos caminos.
# Analiza en virusTotal: todo bien? Perfecto, ya está. Mal? Borra y avísame

# Definimos la ruta de salida (usamos .txt ya que es un formato personalizado)
$finalFile = "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\AUDITORIA_SISTEMA_LLM.txt"

# 1. EL PROMPT MAESTRO (Instrucciones para el LLM)
$promptHeader = @"
# ROL: ANALISTA FORENSE Y DE SISTEMAS WINDOWS (Nivel Senior)

## INSTRUCCIONES GENERALES
A continuación, recibirás varios bloques de datos en formato JSON extraídos de un sistema Windows.
Tu objetivo es realizar un análisis de seguridad, salud del sistema y detección de amenazas.

## GESTIÓN DE ATENCIÓN Y CONTEXTO (CRÍTICO)
Si el volumen de datos es grande, NO intentes analizarlo todo superficialmente en una sola respuesta.
Es preferible que detectes tus propias limitaciones y propongas profundizar en partes específicas en siguientes turnos.
Esto evitará que pierdas detalles importantes por saturación de contexto.

## TAREAS A REALIZAR EN ESTA RESPUESTA (PRIORIDAD ALTA)
1. **EXCLUSIONES DE DEFENDER (CRÍTICO):** Revisa el bloque de 'Exclusiones'. Si hay rutas en AppData, Temp o archivos específicos excluidos, es un indicador de compromiso ALTO (Malware tipo Tsunami/Mineros).
2. **Analizar Persistencia:** Revisa 'Startup' y 'Tareas Programadas'.
3. **Correlación de Procesos y Red:** Cruza 'Netstat' con 'Procesos Activos'.
4. **Anomalías en Rutas:** Busca ejecutables en carpetas temporales (AppData, Temp, Downloads).
5. **Extensiones:** Revisa 'Extensiones' en busca de anomalías.

### GUÍA RÁPIDA: IPROCESOS ACTIVOS
Los procesos incluyen validación criptográfica real (no metadatos de texto):
*   **`[MICROSOFT]` / `[BIGTECH]` / `[FIRMA_TERCEROS]`**: Firma Digital **VÁLIDA**. El archivo es íntegro y auténtico.
*   **`[PELIGRO_FIRMA_ALTERADA]`**: **CRÍTICO**. La firma existe pero el HASH no coincide. El archivo ha sido **modificado o infectado**.
*   **`[ALERTA_SIN_FIRMA]`**: Archivo sin firmar. Analiza su peligrosidad basándote en la Ruta y el Hash.
*Nota1: Si el campo `Path_Explicit` no aparece, es porque la ruta ya está visible dentro de `Command_Line`.*
*Nota2: Signer_Info es el nombre encontrado en la firma
*Nota3: Puedes usar el hash para pasarle el link a VirusTotal al usuario como https://www.virustotal.com/gui/file/[HASH]
Ejemplo: https://www.virustotal.com/gui/file/ad659a539d3a621074c69aca534e9324543ad33b564751a1bf1fb099182f6246

## FORMATO DE SALIDA REQUERIDO

### 1. HALLAZGOS CRÍTICOS (Prioridad Máxima)
* (Amenazas inmediatas confirmadas. SI HAY EXCLUSIONES RARAS, VAN AQUÍ)

### 2. ADVERTENCIAS
* (Comportamientos sospechosos a vigilar)

### 3. ESTADO GENERAL
* (Resumen breve de la salud del sistema)

### 4. ESTRATEGIA DE PROFUNDIZACIÓN (Iteración)
Aquí es donde guías la investigación. Tienes dos tipos de solicitudes permitidas:

* **A) ACCIÓN EXTERNA DEL USUARIO (VirusTotal):**
  Si ves un archivo sospechoso, pide al usuario que lo verifique externamente.
  * IMPRESCINDIBLE: Debes proporcionar la **[RUTA COMPLETA]** del archivo para que el usuario pueda localizarlo y subirlo.
  * Ejemplo: "Detecto un ejecutable raro excluido en Defender. Por favor, sube el archivo 'C:\Users\...\Runtime Broker.exe' a VirusTotal."

* **B) FOCO DE ATENCIÓN INTERNO (Tu análisis):**
  El usuario NO va a filtrar datos. TÚ ya tienes todos los datos. Pide permiso para enfocar tu próxima respuesta en un solo bloque JSON si es complejo.
  * Ejemplo Tareas: "El JSON de Tareas Programadas es muy extenso. ¿Me das permiso para dedicar mi próxima respuesta ÍNTEGRAMENTE a analizar ese bloque?"

**Tu objetivo en este punto:** Proponer en qué parte de los datos YA SUMINISTRADOS quieres centrar el 100% de tu capacidad de análisis en la siguiente respuesta.

---
AQUÍ COMIENZAN LOS DATOS DEL SISTEMA:
"@

# Inicializamos el archivo con el prompt
$promptHeader | Set-Content $finalFile -Encoding UTF8

# 2. LISTA DE ARCHIVOS A PROCESAR
$dataSources = @(
    @{ Title = "1. EXCLUSIONES DE WINDOWS DEFENDER (CRÍTICO)"; File = "defender_exclusions.json" },
    @{ Title = "2. PROGRAMAS DE INICIO (Startup)"; File = "startup.json" },
    @{ Title = "3. EXTENSIONES (Navegadores y VSCode)"; File = "app_extensions.json" },
    @{ Title = "4. PROCESOS ACTIVOS (Running Processes)"; File = "procesos_activos.json" },
    @{ Title = "5. SERVICIOS DE WINDOWS (Services)"; File = "servicios.json" },
    @{ Title = "6. CONEXIONES DE RED (Netstat con Procesos)"; File = "netstat.json" },
	@{ Title = "7. HOSTS"; File = "hosts_file.json" }, 
    @{ Title = "8. TAREAS PROGRAMADAS (Scheduled Tasks)"; File = "tasks.json" }	
)

# 3. BUCLE DE CONSTRUCCIÓN (Con tus delimitadores personalizados)
foreach ($item in $dataSources) {
    $path = "$env:USERPROFILE\Desktop\ANALISIS-VIRUS\$($item.File)"
    
    if (Test-Path $path) {
        # Leemos el JSON crudo
        $jsonContent = Get-Content $path -Raw -Encoding UTF8
        
        # Construimos el bloque con tus etiquetas y los nuevos delimitadores
        $customBlock = "
## $($item.Title)
INICIOJSON
$jsonContent
FINJSON
"
        # Añadimos al archivo final
        Add-Content -Path $finalFile -Value $customBlock -Encoding UTF8
        Write-Host "[OK] Agregado: $($item.Title)" -ForegroundColor Green
    } else {
        Add-Content -Path $finalFile -Value "`n## $($item.Title)`n> [!WARNING] ARCHIVO NO ENCONTRADO: $($item.File)" -Encoding UTF8
        Write-Host "[ERROR] No encontrado: $($item.File)" -ForegroundColor Red
    }
}

Write-Host "`n--- PROCESO COMPLETADO ---" -ForegroundColor Cyan
Write-Host "El informe listo para copiar está en: $finalFile" -ForegroundColor Yellow
# Abrimos el archivo para que lo veas al instante
Invoke-Item $finalFile