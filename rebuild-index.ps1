Set-Location -Path $PSScriptRoot

Write-Host "Rebuilding Second Brain vector index..."
Write-Host ""

# Activate the venv and run the rebuild
& ".\.venv\Scripts\python.exe" -c @"
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from agency_common.obsidian_vector_index import build_vector_database

count = build_vector_database()
print(f'\nDone. {count} documents indexed into ChromaDB.')
print('Brand YAMLs, vault notes, and prior run summaries are now searchable.')
"@

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Index rebuilt successfully."
    Write-Host "You can verify brand profiles were picked up by running:"
    Write-Host ""
    Write-Host "  .\.venv\Scripts\python.exe -c `"from agency_common.obsidian_vector_index import search_second_brain; print(search_second_brain('brand voice content style', num_results=2))`""
} else {
    Write-Host ""
    Write-Host "Something went wrong. Check that OBSIDIAN_VAULT_PATH is set in your .env file"
    Write-Host "and that chromadb is installed: .\.venv\Scripts\pip install -e './packages/agency-common[vector]'"
}
