"""
Centralized Vector Database Connection Layer.
Shared between both OpenedSwarm and Automata agents.
"""
from pathlib import Path
import os

WORKSPACE_ROOT = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE_ROOT / "memory" / "automata_db"

def get_vector_db_client():
    """Returns a unified ChromaDB or Vector DB client for the workspace."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(MEMORY_DIR))
        return client
    except ImportError:
        return None

def store_memory(collection_name: str, doc_id: str, text: str, metadata: dict = None):
    client = get_vector_db_client()
    if not client: return False
    
    collection = client.get_or_create_collection(name=collection_name)
    collection.add(
        documents=[text],
        metadatas=[metadata or {}],
        ids=[doc_id]
    )
    return True
