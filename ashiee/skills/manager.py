"""
Ashiee Progressive Disclosure Skills Engine
Parses SKILL.md files, extracts frontmatter, and manages on-demand skill activation.
"""

from pathlib import Path
from typing import Dict, List, Optional
import re
from pydantic import BaseModel
from ashiee.config import AshieeConfig


class Skill(BaseModel):
    name: str
    description: str
    path: Path
    content: str = ""
    is_loaded: bool = False


class SkillManager:
    def __init__(self, config: AshieeConfig, builtin_skills_dir: Optional[Path] = None):
        self.config = config
        self.builtin_skills_dir = builtin_skills_dir or (Path(__file__).parent.parent.parent / "builtin_skills")
        self._skills: Dict[str, Skill] = {}

    def discover_all(self) -> Dict[str, Skill]:
        """Discovers skills from workspace, global, and builtin roots with precedence."""
        self._skills.clear()

        # 1. Antigravity Collaboration Bridge Skills (Direct from Antigravity core & plugins)
        try:
            from ashiee.core.antigravity_bridge import AntigravityBridge
            bridge = AntigravityBridge.get_instance()
            for sname, sinfo in bridge.shared_skills.items():
                self._skills[sname] = Skill(
                    name=sname,
                    description=sinfo.description,
                    path=Path(sinfo.path)
                )
        except Exception:
            pass

        # 2. Ashiee Built-in skills
        if self.builtin_skills_dir.exists():
            self._scan_directory(self.builtin_skills_dir)

        # 3. Global user skills (~/.ashiee/skills)
        global_skills = self.config.app_data_dir / "skills"
        if global_skills.exists():
            self._scan_directory(global_skills)

        # 4. Workspace skills (.agents/skills) (Highest priority)
        workspace_skills = self.config.workspace_root / ".agents" / "skills"
        if workspace_skills.exists():
            self._scan_directory(workspace_skills)

        return self._skills

    def _scan_directory(self, root: Path) -> None:
        for skill_dir in root.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skill = self._parse_skill_file(skill_file)
                    if skill:
                        self._skills[skill.name] = skill

    def _parse_skill_file(self, file_path: Path) -> Optional[Skill]:
        try:
            raw = file_path.read_text(encoding="utf-8")
            # Parse YAML frontmatter between --- and ---
            match = re.match(r"^---\s*([\s\S]*?)\s*---\s*([\s\S]*)$", raw)
            if not match:
                return None

            frontmatter = match.group(1)
            name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
            desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)

            name = name_match.group(1).strip() if name_match else file_path.parent.name
            desc = desc_match.group(1).strip() if desc_match else "No description provided."

            return Skill(name=name, description=desc, path=file_path)
        except Exception:
            return None

    def get_skill_summary_prompt(self) -> str:
        """Returns compact catalog of skills for the system instructions."""
        if not self._skills:
            return "(No skills registered)"

        lines = ["Available Skills (load on demand with `load_skill`):"]
        for skill in self._skills.values():
            lines.append(f"- **{skill.name}**: {skill.description}")
        return "\n".join(lines)

    def load_skill_content(self, name: str) -> Optional[str]:
        skill = self._skills.get(name)
        if not skill:
            return None
        if not skill.content:
            skill.content = skill.path.read_text(encoding="utf-8")
            skill.is_loaded = True
        return skill.content
