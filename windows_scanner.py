import subprocess
import os
import sys

def run_local_scan(ps_script_path: str = "script_auditoria.ps1") -> str:
    """
    Simula el comportamiento de un Agente Local (EDR).
    Ejecuta el script de PowerShell para recopilar la telemetría del sistema
    y devuelve todo el texto formateado listo para inyectar en el LLM.
    """
    print("\n[+] Iniciando recolector de telemetría de Windows...")

    if os.getenv("DEBUG_ON") == "1":
        desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")
        result_file = os.path.join(desktop_path, "ANALISIS-VIRUS", "AUDITORIA_SISTEMA_LLM.txt")
        # Leemos todo el contenido masivo
        with open(result_file, "r", encoding="utf-8") as f:
            system_data = f.read()

        print(f"[+] Datos del sistema recopilados correctamente. ({len(system_data)} caracteres)")
        return system_data

    
    # Comprobación básica de que el script existe
    if not os.path.exists(ps_script_path):
        raise FileNotFoundError(f"No se encuentra el script de PowerShell en: {ps_script_path}")

    try:
        # Ejecutamos PowerShell. 
        # Nota: Idealmente la terminal de Python ya debe tener permisos de Administrador.
        comando = [
            "powershell.exe", 
            "-ExecutionPolicy", "Bypass", 
            "-File", ps_script_path
        ]
        
        # subprocess.run bloquea la ejecución hasta que el script de PS termine
        subprocess.run(comando, check=True, capture_output=True, text=True)
        print("[+] Script de PowerShell ejecutado con éxito.")
        
    except subprocess.CalledProcessError as e:
        print(f"[-] Error al ejecutar el script de PowerShell:\n{e.stderr}")
        sys.exit(1)

    # El script original guarda el prompt final en el Escritorio
    desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")
    result_file = os.path.join(desktop_path, "ANALISIS-VIRUS", "AUDITORIA_SISTEMA_LLM.txt")

    if not os.path.exists(result_file):
        raise FileNotFoundError("El script no generó el archivo de salida esperado.")

    # Leemos todo el contenido masivo
    with open(result_file, "r", encoding="utf-8") as f:
        system_data = f.read()

    print(f"[+] Datos del sistema recopilados correctamente. ({len(system_data)} caracteres)")
    return system_data