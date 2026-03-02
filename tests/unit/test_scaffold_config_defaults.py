from apidev.core.models.config import ApidevConfig
from apidev.infrastructure.config.toml_loader import default_config_text


def test_config_model_sets_scaffold_defaults() -> None:
    config = ApidevConfig()

    assert config.generator.scaffold is True
    assert config.generator.scaffold_dir == "integration"


def test_default_config_text_contains_scaffold_defaults() -> None:
    text = default_config_text()

    assert "scaffold = true" in text
    assert 'scaffold_dir = "integration"' in text
