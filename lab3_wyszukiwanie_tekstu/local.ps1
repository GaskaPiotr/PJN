param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Install', 'Start', 'Stop')]
    [string]$Action
)

$ErrorActionPreference = 'Stop'
$runtime = Join-Path $PSScriptRoot '.runtime'
$pg = Join-Path $runtime 'pgsql/bin'
$data = Join-Path $runtime 'pgdata'
$pgctl = Join-Path $pg 'pg_ctl.exe'
$solrHome = Join-Path $runtime 'solr-10.1.0-slim'
$solr = Join-Path $solrHome 'bin/solr.cmd'
$portFile = Join-Path $solrHome 'bin/solr-18983.port'
$env:SOLR_HOST_BIND = '127.0.0.1'
$env:SOLR_HOST_ADVERTISE = '127.0.0.1'
$env:SOLR_LOGS_DIR = Join-Path $runtime 'solr-logs'
$env:SOLR_PID_DIR = $runtime
$env:SOLR_START_WAIT = '180'
if ($env:LAB3_JAVA_HOME) { $env:SOLR_JAVA_HOME = $env:LAB3_JAVA_HOME }

function Invoke-Checked($exe, [string[]]$arguments) {
    & $exe @arguments
    if ($LASTEXITCODE -ne 0) { throw "$exe exited with code $LASTEXITCODE" }
}

function Get-Package([string]$uri, [string]$destination, [string]$algorithm, [string]$expected) {
    if (!(Test-Path -LiteralPath $destination)) {
        $partial = "$destination.partial"
        Invoke-Checked 'curl.exe' @('--fail', '--location', '--silent', '--show-error', '--retry', '2', '-o', $partial, $uri)
        Move-Item -LiteralPath $partial -Destination $destination
    }
    if ((Get-FileHash -LiteralPath $destination -Algorithm $algorithm).Hash -ne $expected) {
        throw "Checksum mismatch for $destination"
    }
}

function Test-SolrEndpoint {
    try {
        $reply = & curl.exe --noproxy '*' --silent --fail --max-time 3 'http://127.0.0.1:18983/solr/admin/collections?action=LIST&wt=json'
        if ($LASTEXITCODE -ne 0) { return $false }
        return (($reply | ConvertFrom-Json).responseHeader.status -eq 0)
    } catch {
        return $false
    }
}

if ($Action -eq 'Install') {
    New-Item -ItemType Directory -Path $runtime -Force | Out-Null
    if (!(Test-Path -LiteralPath $solr)) {
        $archive = Join-Path $runtime 'solr-10.1.0-slim.tgz'
        Get-Package 'https://downloads.apache.org/solr/solr/10.1.0/solr-10.1.0-slim.tgz' $archive SHA512 'd22df360764a024ea59dbe0e29367ef0dfaabcfe9d7f6b568b35f73e034c7346ca325e5e18f51da312ae292eb4d1cff3c7380967f9288e56c6563306bab67f06'
        Invoke-Checked 'tar.exe' @('-xzf', $archive, '-C', $runtime)
    }
    if (!(Test-Path -LiteralPath $pgctl)) {
        $archive = Join-Path $runtime 'postgresql-17.12.zip'
        Get-Package 'https://get.enterprisedb.com/postgresql/postgresql-17.12-1-windows-x64-binaries.zip' $archive SHA256 'A2CD8A774389347B70BE7748AC4A37EF43CB6EE539C5FC3E85AE264B15E4A04C'
        Invoke-Checked 'tar.exe' @('-xf', $archive, '-C', $runtime, 'pgsql/bin', 'pgsql/lib', 'pgsql/share')
    }
    return
}

if (!(Test-Path -LiteralPath $pgctl) -or !(Test-Path -LiteralPath $solr)) {
    throw 'Najpierw uruchom local.ps1 -Action Install.'
}

if ($Action -eq 'Start') {
    if (!(Test-Path -LiteralPath (Join-Path $data 'PG_VERSION'))) {
        Invoke-Checked (Join-Path $pg 'initdb.exe') @('-D', $data, '-U', 'lab3', '--auth=trust', '--encoding=UTF8', '--locale=C')
    }
    & $pgctl -D $data status
    if ($LASTEXITCODE -ne 0) {
        Invoke-Checked $pgctl @('-D', $data, '-l', (Join-Path $runtime 'postgres.log'), '-o',
            '-h 127.0.0.1 -p 15436 -c shared_buffers=256MB -c maintenance_work_mem=256MB', '-w', 'start')
    }
    if (!(Test-SolrEndpoint)) {
        Invoke-Checked $solr @('start', '-p', '18983', '-m', '2g')
        $deadline = [DateTime]::UtcNow.AddMinutes(3)
        while (!(Test-SolrEndpoint)) {
            if ([DateTime]::UtcNow -ge $deadline) {
                throw "Solr did not become ready. See $env:SOLR_LOGS_DIR."
            }
            Start-Sleep -Seconds 2
        }
    }
    if (!(Test-Path -LiteralPath $portFile)) { throw 'Port 18983 is used by a different Solr instance.' }
    Write-Output 'Solr ready on localhost:18983.'
    return
}

if (Test-Path -LiteralPath $portFile) {
    Invoke-Checked $solr @('stop', '-p', '18983')
}
if (Test-Path -LiteralPath (Join-Path $data 'postmaster.pid')) {
    Invoke-Checked $pgctl @('-D', $data, '-m', 'fast', '-w', 'stop')
}
