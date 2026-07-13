from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillCompatibilityTest(unittest.TestCase):
    def test_shared_skill_entrypoint_stays_portable(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: fireworks-tech-graph", skill)
        self.assertIn("${CLAUDE_SKILL_DIR:-/absolute/path/from-codex-skill-metadata}", skill)
        self.assertNotIn("./scripts/", skill)
        self.assertLessEqual(len(skill.splitlines()), 500)

    def test_runtime_metadata_and_bundled_resources_exist(self) -> None:
        for relative_path in (
            "agents/openai.yaml",
            "references/png-export.md",
            "scripts/generate-diagram.sh",
            "scripts/svg2png.js",
        ):
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

        openai_yaml = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$fireworks-tech-graph", openai_yaml)

    def test_distribution_includes_codex_metadata(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["version"], "1.0.5")
        self.assertIn("agents/", package["files"])
        self.assertNotIn("main", package)

    def test_install_docs_cover_both_discovery_paths(self) -> None:
        for readme in ("README.md", "README.zh.md"):
            content = (ROOT / readme).read_text(encoding="utf-8")
            self.assertIn("~/.agents/skills/fireworks-tech-graph", content)
            self.assertIn("~/.claude/skills/fireworks-tech-graph", content)


if __name__ == "__main__":
    unittest.main()
