Set-Location -Path $PSScriptRoot
git add packages/agency-common/src/agency_common/models.py `
        packages/agency-content/src/agency_content/voice.py `
        packages/agency-content/src/agency_content/writers/instagram.py `
        packages/agency-content/src/agency_content/agent.py `
        packages/agency-research/src/agency_research/agent.py `
        packages/agency-common/src/agency_common/knowledge_reader.py `
        packages/agency-common/src/agency_common/obsidian_writer.py `
        packages/agency-common/src/agency_common/harness_runner.py `
        brands/_template.yaml
git commit -m "fix: voice quality, research synthesis, second brain, session logging

CONTENT QUALITY
- models.py: add sentence_max_words, banned_constructions, example_captions to BrandWritingRules
- voice.py: universal anti-AI-writing rules, archetype hook guidance, sentence constraints,
  brand-specific banned constructions, example copy anchors; replaces vague full_brief
- instagram.py: remove hardcoded generic reel hooks; replace with archetype-derived guidance

RESEARCH SYNTHESIS
- research/agent.py: _generate_summary now produces real output -- top competitor by
  engagement, format distribution, themes, rising/stable hashtags, top post snippets,
  content gap analysis; was previously just a post count

SECOND BRAIN (root cause fix)
- knowledge_reader.py: add Claude_Sessions, Codex_Sessions, Agent_Sessions to
  IGNORED_DIRECTORIES so session transcripts no longer pollute the vector index;
  add parse_brand_yaml_file() and iter_brand_yaml_files() so brand YAML configs
  in vault/Brands/ are indexed as readable text -- brand profiles were previously
  completely invisible to search_second_brain

SESSION LOGGING (root cause fix)
- obsidian_writer.py: rename DEFAULT_SESSIONS_DIR from Claude_Sessions to Agent_Sessions;
  add log_brand_run_summary() which writes structured decision notes to
  vault/Brands/<slug>/Agent_Runs/ -- searchable signal, not transcript noise
- harness_runner.py: use log_agent_session_with_related_notes (adds vault backlinks)
  instead of bare log_agent_session

VAULT WRITE-BACK
- research/agent.py: write structured research summary to vault after each CLI run
- content/agent.py: write content run note to vault after each generate() call
  so future search_second_brain finds brand content history automatically

VAULT CONTEXT IN CLI
- content/agent.py: vault lookup at start of generate() and generate_week()
- research/agent.py: vault lookup at start of run()"
Remove-Item $PSScriptRoot\commit-fixes.ps1
Write-Host ""
Write-Host "Done. Run 'git log --oneline -3' to verify."
Write-Host ""
Write-Host "ACTION REQUIRED: rebuild the vector index to pick up the fixes:"
Write-Host "  python -c `"from agency_common.obsidian_vector_index import build_vector_database; build_vector_database()`""
