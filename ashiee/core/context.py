"""
Ashiee Context Assembler & Rules Engine
Crawls hierarchical workspace rules, system metadata, and injects progressive skills.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List
from ashiee.config import AshieeConfig
from ashiee.skills.manager import SkillManager


class ContextAssembler:
    def __init__(self, config: AshieeConfig, skill_manager: SkillManager):
        self.config = config
        self.skill_manager = skill_manager

    def assemble_system_instructions(self) -> str:
        # 1. Discover hierarchical rules
        rules = self._discover_hierarchical_rules()

        # 2. Get progressive skills catalog
        skills_summary = self.skill_manager.get_skill_summary_prompt()

        # 3. Environment Context
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        ws = str(self.config.workspace_root)

        rules_text = "\n\n".join(f"### Rule: {r['name']}\n{r['content']}" for r in rules)
        if not rules_text:
            rules_text = "No workspace-specific custom rules found."

        return f"""<identity>
You are Ashiee, an advanced autonomous AI coding assistant and pair programmer.
You are running directly in the user's workspace environment: {ws}
System Time: {now}
</identity>

<behavioral_guidelines>
- Be concise, direct, and actionable.
- Prioritize safe, deterministic file edits over destructive overwrites.
- Check file contents before making edits.
- Format code and outputs in clean GitHub-style Markdown.
- Proactively run builds, tests, or linters when completing code changes.
</behavioral_guidelines>

<workspace_rules>
{rules_text}
</workspace_rules>

<skills>
{skills_summary}
</skills>
"""

    def _discover_hierarchical_rules(self) -> List[dict]:
        rules = []
        root = self.config.workspace_root

        # Check for root guideline markdown files
        candidate_files = ["ASHIEE.md", "AGENTS.md", "GEMINI.md"]
        for cname in candidate_files:
            cpath = root / cname
            if cpath.exists() and cpath.is_file():
                try:
                    rules.append({
                        "name": cname,
                        "content": cpath.read_text(encoding="utf-8")
                    })
                except Exception:
                    pass

        # Check .agents/rules/
        rules_dir = root / ".agents" / "rules"
        if rules_dir.exists() and rules_dir.is_dir():
            for rfile in rules_dir.glob("*.md"):
                try:
                    rules.append({
                        "name": rfile.name,
                        "content": rfile.read_text(encoding="utf-8")
                    })
                except Exception:
                    pass

        return rules
