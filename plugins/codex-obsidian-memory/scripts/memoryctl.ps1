param(
    [string]$Action = 'help',
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments = @()
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex' }
$cpu = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
$runtimeRoot = if ($env:CODEX_OBSIDIAN_RUNTIME_DIR) { $env:CODEX_OBSIDIAN_RUNTIME_DIR } else { Join-Path $codexRoot "obsidian-memory\runtime\Windows-$cpu" }
$cacheFile = Join-Path $runtimeRoot 'python-path.txt'
$probe = "import sys; sys.exit(1) if sys.version_info < (3,11) else None; sys.stdout.reconfigure(encoding='utf-8'); print(sys.executable)"

function Invoke-Program([string]$Executable, [string[]]$ProgramArgs, [string]$InputText = '', [int]$Timeout = 300000) {
    $start = New-Object Diagnostics.ProcessStartInfo
    $start.FileName = $Executable
    $quoted = foreach ($value in $ProgramArgs) {
        $escaped = [regex]::Replace($value, '(\\*)"', '$1$1\"')
        $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
        '"' + $escaped + '"'
    }
    $start.Arguments = $quoted -join ' '
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardInput = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.StandardOutputEncoding = [Text.Encoding]::UTF8
    $start.StandardErrorEncoding = [Text.Encoding]::UTF8
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $start
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if ($InputText) {
            $payload = [Text.Encoding]::UTF8.GetBytes($InputText)
            $process.StandardInput.BaseStream.Write($payload, 0, $payload.Length)
        }
        $process.StandardInput.Close()
        if (-not $process.WaitForExit($Timeout)) {
            $process.Kill()
            throw 'Runtime command timed out.'
        }
        return @{ Code = $process.ExitCode; Out = $stdout.Result; Err = $stderr.Result }
    } finally { $process.Dispose() }
}

function Test-Python([string]$Executable, [string[]]$Prefix = @()) {
    try {
        if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { return $null }
        if ($Executable -like '*\Microsoft\WindowsApps\*') { return $null }
        $result = Invoke-Program $Executable (@($Prefix) + @('-I', '-c', $probe)) '' 8000
        if ($result.Code -eq 0 -and $result.Out) { return $result.Out.Trim() }
    } catch { }
    return $null
}

function Find-Python([bool]$ManagedOnly = $false) {
    if (Test-Path -LiteralPath $cacheFile) {
        $cached = [IO.File]::ReadAllText($cacheFile, [Text.Encoding]::UTF8).Trim()
        if (-not $ManagedOnly -or $cached.StartsWith((Join-Path $runtimeRoot 'python') + '\', [StringComparison]::OrdinalIgnoreCase)) {
            $found = Test-Python $cached
            if ($found) { return $found }
        }
    }
    if (-not $ManagedOnly) {
        foreach ($name in @('py.exe', 'python.exe', 'python3.exe')) {
            $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($command) {
                $prefixArgs = if ($name -eq 'py.exe') { @('-3') } else { @() }
                $found = Test-Python $command.Source $prefixArgs
                if ($found) { return $found }
            }
        }
    }
    return $null
}

if ($Action -in @('help','--help','-h')) {
    Write-Output 'Usage: memoryctl.ps1 -Action prepare-runtime [--managed] | python-path | hook | routine ARGS | COMMAND ARGS'
    exit 0
}

if ($Action -eq 'prepare-runtime') {
    $managed = $Arguments.Count -eq 1 -and $Arguments[0] -eq '--managed'
    if ($Arguments.Count -gt 0 -and -not $managed) { throw 'Usage: -Action prepare-runtime [--managed]' }
    New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
    $lock = Join-Path $runtimeRoot 'prepare.lock'
    try { New-Item -ItemType Directory -Path $lock -ErrorAction Stop | Out-Null }
    catch { throw 'Runtime preparation is already running. Retry after it finishes.' }
    $staging = $null
    $previousInstallDir = $env:UV_PYTHON_INSTALL_DIR
    $previousNoModify = $env:UV_NO_MODIFY_PATH
    try {
        $selected = Find-Python $managed
        if (-not $selected) {
            $target = switch ($cpu.ToUpperInvariant()) {
                'AMD64' { 'x86_64-pc-windows-msvc' }
                'ARM64' { 'aarch64-pc-windows-msvc' }
                default { throw 'Unsupported CPU for automatic runtime setup.' }
            }
            $manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\assets\runtime\uv-assets.txt')
            $version = (($manifest | Where-Object { $_ -match '^version ' }) -split ' ')[1]
            $archive = "uv-$target.zip"
            $entry = $manifest | Where-Object { $_.StartsWith($archive + ' ') }
            if (-not $entry) { throw 'Missing pinned runtime checksum.' }
            $expected = ($entry -split ' ')[1]
            $staging = Join-Path $runtimeRoot ('.prepare.' + [Guid]::NewGuid().ToString('N'))
            New-Item -ItemType Directory -Path $staging | Out-Null
            $download = Join-Path $staging $archive
            [Console]::Error.WriteLine('Preparing a private Python runtime for this plugin...')
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/astral-sh/uv/releases/download/$version/$archive" -OutFile $download
            if ((Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Runtime bootstrap checksum mismatch.' }
            Expand-Archive -LiteralPath $download -DestinationPath $staging
            $uv = (Get-ChildItem -LiteralPath $staging -Filter uv.exe -Recurse | Select-Object -First 1).FullName
            $env:UV_PYTHON_INSTALL_DIR = Join-Path $runtimeRoot 'python'
            $env:UV_NO_MODIFY_PATH = '1'
            $install = Invoke-Program $uv @('python', 'install', '3.12', '--no-bin', '--no-registry', '--no-config', '--no-cache')
            if ($install.Code -ne 0) { throw "Private Python preparation failed: $($install.Err)" }
            $found = Invoke-Program $uv @('python', 'find', '3.12', '--managed-python', '--no-python-downloads', '--no-config', '--no-cache')
            if ($found.Code -ne 0) { throw 'Prepared Python could not be located.' }
            $selected = Test-Python $found.Out.Trim()
            if (-not $selected) { throw 'Prepared Python did not pass its version check.' }
        }
        $temporary = Join-Path $runtimeRoot 'python-path.tmp'
        [IO.File]::WriteAllText($temporary, $selected + "`n", (New-Object Text.UTF8Encoding($false)))
        Move-Item -LiteralPath $temporary -Destination $cacheFile -Force
        Write-Output $selected
    } finally {
        $env:UV_PYTHON_INSTALL_DIR = $previousInstallDir
        $env:UV_NO_MODIFY_PATH = $previousNoModify
        if ($staging -and (Test-Path -LiteralPath $staging)) { Remove-Item -LiteralPath $staging -Recurse -Force }
        Remove-Item -LiteralPath $lock -Force
    }
    exit 0
}

$selected = Find-Python
if (-not $selected) { throw 'Plugin runtime is not ready. Ask Codex to run memoryctl.ps1 -Action prepare-runtime.' }
switch ($Action) {
    'python-path' { Write-Output $selected; exit 0 }
    'hook' { $result = Invoke-Program $selected (@('-B', (Join-Path $PSScriptRoot 'hook.py')) + $Arguments) ([Console]::In.ReadToEnd()) }
    'routine' { $result = Invoke-Program $selected (@('-B', (Join-Path $PSScriptRoot 'routine_runner.py')) + $Arguments) }
    default { $result = Invoke-Program $selected (@('-B', (Join-Path $PSScriptRoot 'memoryctl.py'), $Action) + $Arguments) }
}
[Console]::Out.Write($result.Out)
[Console]::Error.Write($result.Err)
exit $result.Code
