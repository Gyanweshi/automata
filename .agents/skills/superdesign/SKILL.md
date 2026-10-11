---
name: superdesign
description: >
  Superdesign is a design agent specialized in frontend UI/UX design. Use this skill before implementing any UI that requires design thinking. Common commands: superdesign create-project --title "X" (setup project), superdesign create-design-draft --project-id <id> --title "Current UI" -p "Faithfully reproduce..." --context-file src/Component.tsx (faithful reproduction), superdesign iterate-design-draft --draft-id <id> -p "dark theme" -p "minimal" --mode branch --context-file src/Component.tsx (design variations), superdesign execute-flow-pages --draft-id <id> --pages '[...]' --context-file src/Component.tsx (extend to more pages), superdesign create-component --project-id <id> --name "NavBar" --html-file /tmp/navbar.html --props '[...]' (extract reusable component), superdesign update-component --component-id <id> --html-file /tmp/navbar.html (update existing component), superdesign list-components --project-id <id> (list existing components). Supports line ranges: --context-file path:startLine:endLine
metadata:
  author: superdesign
  version: "0.0.2"
---

Read and follow the canonical instructions at
[`skills/superdesign/SKILL.md`](../../../skills/superdesign/SKILL.md).
Resolve its scripts and references relative to that canonical skill directory.
