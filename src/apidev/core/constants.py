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
DEFAULT_INTEGRATION_DIR = f"{APIDEV_DIRNAME}/integration"
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

InitRuntimeProfile = Literal["fastapi", "none"]
INIT_RUNTIMES: tuple[InitRuntimeProfile, ...] = ("fastapi", "none")
INIT_RUNTIMES_DISPLAY = ", ".join(INIT_RUNTIMES)
DEFAULT_INIT_RUNTIME: InitRuntimeProfile = "fastapi"

InitIntegrationMode = Literal["off", "scaffold", "full"]
INIT_INTEGRATION_MODES: tuple[InitIntegrationMode, ...] = ("off", "scaffold", "full")
INIT_INTEGRATION_MODES_DISPLAY = ", ".join(INIT_INTEGRATION_MODES)
DEFAULT_INIT_INTEGRATION_MODE: InitIntegrationMode = "scaffold"

DIAG_CODE_PATH_BOUNDARY_VIOLATION = "validation.PATH_BOUNDARY_VIOLATION"
DIAG_CODE_INIT_PROFILE_INVALID_ENUM = "config.INIT_PROFILE_INVALID_ENUM"
DIAG_CODE_INIT_MODE_CONFLICT = "config.INIT_MODE_CONFLICT"
