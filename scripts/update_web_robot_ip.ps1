param(
    [string]$Path = ".",
    [string]$Ip,
    [switch]$NoBackup
)

$ErrorActionPreference = "Stop"

function Test-SkippedPath {
    param([string]$FullName)

    $skipDirs = @(
        "\.git\",
        "\node_modules\",
        "\dist\",
        "\build\",
        "\.next\",
        "\out\",
        "\coverage\"
    )

    foreach ($dir in $skipDirs) {
        if ($FullName -like "*$dir*") {
            return $true
        }
    }

    return $false
}

function Test-EditableFile {
    param([System.IO.FileInfo]$File)

    $extensions = @(
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".mjs",
        ".cjs",
        ".html",
        ".css",
        ".json",
        ".env",
        ".local",
        ".md"
    )

    if ($File.Name -like "*.bak") {
        return $false
    }

    return ($extensions -contains $File.Extension -or $File.Name -like ".env*")
}

function Get-LocalIPv4Addresses {
    $addresses = @()

    try {
        $addresses = Get-NetIPAddress -AddressFamily IPv4 |
            Where-Object {
                $_.IPAddress -notlike "127.*" -and
                $_.IPAddress -notlike "169.254.*" -and
                $_.PrefixOrigin -ne "WellKnown" -and
                $_.AddressState -eq "Preferred"
            } |
            Select-Object -ExpandProperty IPAddress -Unique
    } catch {
        $addresses = @()
    }

    if (-not $addresses -or $addresses.Count -eq 0) {
        try {
            $addresses = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
                Where-Object {
                    $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and
                    $_.IPAddressToString -notlike "127.*" -and
                    $_.IPAddressToString -notlike "169.254.*"
                } |
                ForEach-Object { $_.IPAddressToString } |
                Select-Object -Unique
        } catch {
            $addresses = @()
        }
    }

    return @($addresses)
}

$resolvedPath = Resolve-Path -LiteralPath $Path
$root = $resolvedPath.Path

if ([string]::IsNullOrWhiteSpace($Ip)) {
    $localIps = Get-LocalIPv4Addresses

    if ($localIps.Count -eq 1) {
        $detectedIp = $localIps[0]
        $answer = Read-Host "IP detectada: $detectedIp. Pulsa Enter para usarla o escribe otra IP"
        $robotIp = if ([string]::IsNullOrWhiteSpace($answer)) { $detectedIp } else { $answer.Trim() }
    } elseif ($localIps.Count -gt 1) {
        Write-Host "Se han detectado varias IPs:"
        for ($i = 0; $i -lt $localIps.Count; $i++) {
            Write-Host (" {0}. {1}" -f ($i + 1), $localIps[$i])
        }

        $answer = Read-Host "Elige un numero, pulsa Enter para usar la primera, o escribe otra IP"

        if ([string]::IsNullOrWhiteSpace($answer)) {
            $robotIp = $localIps[0]
        } elseif ($answer -match "^\d+$" -and [int]$answer -ge 1 -and [int]$answer -le $localIps.Count) {
            $robotIp = $localIps[[int]$answer - 1]
        } else {
            $robotIp = $answer.Trim()
        }
    } else {
        $robotIp = Read-Host "No se pudo detectar la IP. Introduce la IP del PC/robot que ejecuta ROS (ej: 192.168.1.50)"
        $robotIp = $robotIp.Trim()
    }
} else {
    $robotIp = $Ip.Trim()
}

if ([string]::IsNullOrWhiteSpace($robotIp)) {
    Write-Host "No se ha introducido ninguna IP. Cancelado."
    exit 1
}

$files = Get-ChildItem -LiteralPath $root -Recurse -File |
    Where-Object {
        -not (Test-SkippedPath $_.FullName) -and
        (Test-EditableFile $_)
    }

$changedFiles = @()

foreach ($file in $files) {
    $content = Get-Content -LiteralPath $file.FullName -Raw
    $updated = $content

    $updated = $updated -replace "(localhost|127\.0\.0\.1)(:9090)", "$robotIp`$2"
    $updated = $updated -replace "(localhost|127\.0\.0\.1)(:8081)", "$robotIp`$2"
    $updated = $updated -replace "IP_DEL_ROBOT_O_PC_ROS", $robotIp
    $updated = $updated -replace "IP_DEL_PC", $robotIp

    if ($updated -ne $content) {
        if (-not $NoBackup) {
            Copy-Item -LiteralPath $file.FullName -Destination "$($file.FullName).bak" -Force
        }

        [System.IO.File]::WriteAllText($file.FullName, $updated, [System.Text.UTF8Encoding]::new($false))
        $changedFiles += $file.FullName
    }
}

if ($changedFiles.Count -eq 0) {
    Write-Host "No se encontraron URLs localhost/127.0.0.1 ni placeholders para cambiar en: $root"
    exit 0
}

Write-Host ""
Write-Host "Archivos actualizados con la IP ${robotIp}:"
foreach ($changedFile in $changedFiles) {
    Write-Host " - $changedFile"
}

if (-not $NoBackup) {
    Write-Host ""
    Write-Host "Se han creado copias .bak junto a cada archivo modificado."
}

Write-Host ""
Write-Host "Recuerda probar estos endpoints desde el navegador:"
Write-Host (" - ws://{0}:9090" -f $robotIp)
Write-Host (" - http://{0}:8081/stream?topic=/a1an_vision/debug_image&type=mjpeg" -f $robotIp)
