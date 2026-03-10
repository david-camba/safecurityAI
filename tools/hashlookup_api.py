import os
import requests
from datetime import datetime
from typing import List
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# --- 1. TOOL: CIRCL HASH ---
class HashLookupInput(BaseModel):
    hashes: List[str] = Field(
        description="Lista de hashes SHA-256 a consultar. Ejemplo: ['a1b2...', 'd4e5...']"
    )

@tool("check_hash_circl", args_schema=HashLookupInput)
def check_hash_circl(hashes: List[str]) -> str:
    """Consulta la BD CIRCL Hashlookup para verificar si los hashes son software legítimo o malware."""
    print(f"\n🔎 [TOOL] Consultando {len(hashes)} hashes en CIRCL Hashlookup...")
    base_url = "https://hashlookup.circl.lu/lookup/sha256"
    resultados = []
    
    for h in hashes:
        clean_hash = h.strip().lower()
        if len(clean_hash) != 64:
            resultados.append(f"❌ Hash {h}: Inválido (Debe ser SHA-256 de 64 caracteres).")
            continue
            
        try:
            response = requests.get(f"{base_url}/{clean_hash}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                resultados.append(f"✅ Hash {clean_hash}: ENCONTRADO. Nombre: {data.get('FileName', 'N/D')} | Producto: {data.get('ProductName', 'N/D')}")
            elif response.status_code == 404:
                resultados.append(f"❓ Hash {clean_hash}: NO ENCONTRADO.")
            else:
                resultados.append(f"⚠️ Hash {clean_hash}: Error del servidor (HTTP {response.status_code}).")
        except requests.exceptions.RequestException as e:
            resultados.append(f"⚠️ Hash {clean_hash}: Error de red -> {str(e)}")
            
    return "\n".join(resultados)