import asyncio
import httpx
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.analysis_ai.graph.graph_config import GraphConfig


class HashLookupInput(BaseModel):
    hashes: List[str] = Field(
        description="List of SHA-256 hashes. Example: ['a1b2...', 'd4e5i...']"
    )


async def _fetch_single_hash(
    client: httpx.AsyncClient, file_hash: str, base_url: str
) -> str:
    """
    Helper function to perform an asynchronous HTTP GET request for a single hash.
    Validates the hash length and handles standard API HTTP response codes.
    """
    clean_hash = file_hash.strip().lower()

    # Pre-flight validation: Ensure the input is a valid SHA-256 string length
    if len(clean_hash) != 64:
        return f"❌ Hash {file_hash}: Invalid format (Requires a 64-character SHA-256 hash)."

    try:
        response = await client.get(f"{base_url}/{clean_hash}")

        # 200 OK: Hash is documented in the CIRCL database
        if response.status_code == 200:
            data = response.json()
            file_name = data.get("FileName", "N/A")
            product_name = data.get("ProductName", "N/A")
            return f"✅ Hash {clean_hash}: FOUND. Name: {file_name} | Product: {product_name}"

        # 404 Not Found: Hash is not present in the database
        elif response.status_code == 404:
            return f"❓ Hash {clean_hash}: NOT FOUND in database."

        # Handle rate limiting or server-side errors
        else:
            return f"⚠️ Hash {clean_hash}: Remote server error (HTTP {response.status_code})."

    except httpx.RequestError as e:
        return f"⚠️ Hash {clean_hash}: Network timeout or request error -> {str(e)}"


@tool("check_hash_circl", args_schema=HashLookupInput)
async def check_hash_circl(hashes: List[str], config: RunnableConfig) -> str:
    """Queries the CIRCL Hashlookup database to verify if hashes belong to legitimate software or malware."""
    notifier = GraphConfig.get_notifier(config)
    await notifier.send_log(
        f"Querying CIRCL intelligence database for {len(hashes)} hashes..."
    )

    base_url = "https://hashlookup.circl.lu/lookup/sha256"

    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        # Prepare tasks for concurrent execution
        tasks = [_fetch_single_hash(client, h, base_url) for h in hashes]

        # Execute all HTTP requests concurrently
        results = await asyncio.gather(*tasks)

    final_results = "\n".join(results)
    await notifier.send_log(f"CIRCL Results:\n{final_results}")

    return final_results
