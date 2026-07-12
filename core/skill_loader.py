"""
core/skill_loader.py

Loads a "skill pack" -- a folder under /skills/<name>/ containing:
  - skill.yaml            : config (name, description, prompt template, contamination rate)
  - feature_extractor.py  : must expose a function `extract_features(raw_df) -> pd.DataFrame`

This is the piece that proves CoreMind is genuinely pluggable: adding a
new domain (study assistant, health tracker, anything) means adding a
new folder here -- the core engine and pipeline never change.
"""

import importlib.util
import os
import yaml


class SkillPack:
    def __init__(self, name: str, config: dict, extract_features_fn):
        self.name = name
        self.config = config
        self.extract_features = extract_features_fn

    @property
    def prompt_template(self) -> str:
        return self.config["prompt_template"]

    @property
    def contamination(self) -> float:
        return self.config.get("contamination", 0.1)

    @property
    def description(self) -> str:
        return self.config.get("description", "")

    @property
    def remediation_rules(self) -> list:
        return self.config.get("remediation_rules", [])


def load_skill(skill_name: str, skills_dir: str = "skills") -> SkillPack:
    skill_dir = os.path.join(skills_dir, skill_name)
    config_path = os.path.join(skill_dir, "skill.yaml")
    extractor_path = os.path.join(skill_dir, "feature_extractor.py")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No skill.yaml found for skill '{skill_name}' at {config_path}")
    if not os.path.exists(extractor_path):
        raise FileNotFoundError(f"No feature_extractor.py found for skill '{skill_name}'")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    spec = importlib.util.spec_from_file_location(f"{skill_name}_extractor", extractor_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "extract_features"):
        raise AttributeError(
            f"feature_extractor.py for '{skill_name}' must define extract_features(raw_df)"
        )

    return SkillPack(skill_name, config, module.extract_features)


def list_available_skills(skills_dir: str = "skills") -> list:
    if not os.path.isdir(skills_dir):
        return []
    return [
        d for d in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, d))
        and os.path.exists(os.path.join(skills_dir, d, "skill.yaml"))
    ]
