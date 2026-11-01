import json
from pathlib import Path
from typing import Optional

from app.skills.models import Skill


class SkillRegistry:
    """Discovers and loads skills from the ``skills/`` directory.

    The filesystem is the source of truth: adding a new skill only requires
    a new directory containing ``skill.json`` and ``SKILL.md``. No changes to
    this class or the graph are necessary.
    """

    def __init__(self, skills_dir: Path | None = None) -> None:
        if skills_dir is None:
            # app/skills/registry.py -> parents[2] = project root
            skills_dir = Path(__file__).resolve().parents[2] / "skills"

        self.skills_dir = Path(skills_dir)
        self._skills: dict[str, Skill] = {}
        self._discover()

    def _discover(self) -> None:
        if not self.skills_dir.exists():
            return

        for entry in sorted(self.skills_dir.iterdir()):
            if not entry.is_dir():
                continue

            config = entry / "skill.json"
            if not config.exists():
                continue

            try:
                data = json.loads(config.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            name = data.get("name") or entry.name
            self._skills[name] = Skill(
                name=name,
                description=data.get("description", ""),
                allowed_tools=list(data.get("allowed_tools", [])),
                require_approval_for=list(data.get("require_approval_for", [])),
                path=entry,
            )

    def list_skills(self) -> list[tuple[str, str]]:
        """Return (name, description) pairs for the planner catalogue."""

        return [(skill.name, skill.description) for skill in self._skills.values()]

    def load_skill(self, name: str) -> Optional[Skill]:
        """Return the named skill, lazily loading its SKILL.md instructions."""

        skill = self._skills.get(name)
        if skill is None:
            return None

        if not skill.instructions and skill.path is not None:
            markdown = skill.path / "SKILL.md"
            if markdown.exists():
                skill.instructions = markdown.read_text()

        return skill

    def catalogue_text(self) -> str:
        """Human-readable catalogue of available skills for the planner."""

        lines = ["Available skills:"]
        for name, description in self.list_skills():
            lines.append(f"- {name}: {description}")
        lines.append("- general: Handle requests that do not match a specific skill.")
        return "\n".join(lines)
