import platform
import subprocess
import json

def get_sys_info():
    print("=== POBIERANIE SPECYFIKACJI SYSTEMU ===\n")
    
    # Podstawowe info o OS i Architekturze
    print(f"System: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Architektura: {platform.machine()} / {platform.architecture()[0]}")
    
    # Procesor, RAM, Płyta i GPU via WMIC/PowerShell
    try_cmd('CPU', 'powershell "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | Format-List"')
    try_cmd('RAM', 'powershell "Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum | Select-Object @{N=\'TotalGB\';E={[math]::round($_.Sum/1GB,2)}} | Format-List"')
    try_cmd('Karta Graficzna', 'powershell "Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion | Format-List"')
    try_cmd('Dysk(i)', 'powershell "Get-CimInstance Win32_LogicalDisk | Where-Object DriveType -eq 3 | Select-Object DeviceID, @{N=\'FreeGB\';E={[math]::round($_.FreeSpace/1GB,2)}}, @{N=\'SizeGB\';E={[math]::round($_.Size/1GB,2)}} | Format-Table"')

def try_cmd(title, cmd):
    print(f"\n--- {title} ---")
    try:
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        print(output.strip())
    except Exception as e:
        print(f"Błąd pobierania danych: {e}")

if __name__ == "__main__":
    get_sys_info()