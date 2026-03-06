from pathlib import Path
from typing import Literal

APIDEV_DIRNAME = ".apidev"
APIDEV_CONFIG_FILENAME = "config.toml"
APIDEV_CONFIG_RELATIVE_PATH = f"{APIDEV_DIRNAME}/{APIDEV_CONFIG_FILENAME}"
APIDEV_BASELINE_CACHE_RELATIVE_ROOT = Path(APIDEV_DIRNAME) / "cache" / "baseline"

DEFAULT_CONTRACTS_DIR = f"{APIDEV_DIRNAME}/contracts"
DEFAULT_SHARED_MODELS_DIR = f"{APIDEV_DIRNAME}/models"
DEFAULT_TEMPLATES_DIR = f"{APIDEV_DIRNAME}/templates"
DEFAULT_GENERATED_DIR = f"{APIDEV_DIRNAME}/output/api"
DEFAULT_RELEASE_STATE_FILE = f"{APIDEV_DIRNAME}/release-state.json"

ScaffoldWritePolicy = Literal["create-missing", "skip-existing", "fail-on-conflict"]
DEFAULT_SCAFFOLD_WRITE_POLICY: ScaffoldWritePolicy = "create-missing"
SCAFFOLD_WRITE_POLICIES: tuple[ScaffoldWritePolicy, ...] = (
    "create-missing",
    "skip-existing",
    "fail-on-conflict",
)
SCAFFOLD_WRITE_POLICIES_DISPLAY = ", ".join(SCAFFOLD_WRITE_POLICIES)

CompatibilityPolicyValue = Literal["warn", "strict"]
DEFAULT_COMPATIBILITY_POLICY: CompatibilityPolicyValue = "warn"
COMPATIBILITY_POLICIES: tuple[CompatibilityPolicyValue, ...] = ("warn", "strict")
COMPATIBILITY_POLICIES_DISPLAY = ", ".join(COMPATIBILITY_POLICIES)
