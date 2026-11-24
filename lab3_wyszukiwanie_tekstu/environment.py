"""Record the hardware and live server versions for the report."""

import datetime
import json
import os
import platform
import subprocess
from zoneinfo import ZoneInfo

from common import RESULTS, ROOT, Solr, pg_connect, write_json


def windows():
    commands = """
$ErrorActionPreference = 'Stop'
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$os = Get-CimInstance Win32_OperatingSystem
$ram = (Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum).Sum
$drive = Get-CimInstance Win32_LogicalDisk -Filter ("DeviceID='" + $env:LAB3_MEASUREMENT_DRIVE + "'")
$partition = Get-CimAssociatedInstance -InputObject $drive -Association Win32_LogicalDiskToPartition | Select-Object -First 1
$disk = Get-CimInstance Win32_DiskDrive -Filter ("Index=" + $partition.DiskIndex)
$media = Get-PhysicalDisk | Where-Object { $_.FriendlyName.Trim() -eq $disk.Model.Trim() } | Select-Object -First 1
@{ cpu = $cpu.Name.Trim(); cores = $cpu.NumberOfCores; threads = $cpu.NumberOfLogicalProcessors
   ram_bytes = $ram; system = ($os.Caption + ' ' + $os.Version); disk = $disk.Model.Trim()
   media = [string]$media.MediaType; drive = $drive.DeviceID } | ConvertTo-Json -Compress
"""
    env = os.environ | {'LAB3_MEASUREMENT_DRIVE': ROOT.drive}
    output = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', commands], env=env, text=True)
    return json.loads(output)


def capture():
    info = Solr().request('admin/info/system')[0]
    with pg_connect() as db:
        pg = db.execute("""
            SELECT current_setting('server_version') AS version,
                   current_setting('shared_buffers') AS buffers,
                   current_setting('maintenance_work_mem') AS maintenance,
                   current_setting('max_parallel_workers_per_gather') AS workers
        """).fetchone()
    hardware = windows() if os.name == 'nt' else {'system': platform.platform(), 'cpu': platform.processor()}
    return {
        'date': datetime.datetime.now(ZoneInfo('Europe/Warsaw')).isoformat(timespec='seconds'),
        'hardware': hardware, 'python': platform.python_version(),
        'postgres': dict(zip(('version', 'shared_buffers', 'maintenance_work_mem', 'max_parallel_workers_per_gather'), pg)),
        'solr': {'version': info['lucene']['solr-spec-version'], 'lucene': info['lucene']['lucene-spec-version'],
                 'java': info['jvm']['version'], 'heap': info['jvm']['memory']['max'], 'mode': info['mode']},
    }


if __name__ == '__main__':
    observed = capture()
    write_json(RESULTS / 'environment.json', observed)
    print(json.dumps(observed, indent=2))
