from pathlib import Path
from typing import Iterable, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
CHATDEV_PACKAGE_DIR = REPO_ROOT / "chatdev"

LEGACY_COMPANY_CONFIG_DIRNAME = "CompanyConfig"
COMPANY_CONFIG_CANDIDATES = (
    "config",
    "CompanyConfig",
    "company_config",
)
WORKSPACE_DIR_CANDIDATES = (
    "outputs",
    "WareHouse",
    "workspace",
)
CONFIG_FILES = (
    "ChatChainConfig.json",
    "PhaseConfig.json",
    "RoleConfig.json",
)


def _first_existing_dir(root: Path, candidates: Iterable[str]) -> Optional[Path]:
    """Return the first existing directory that matches one of the candidate names."""
    for name in candidates:
        path = root / name
        if path.is_dir():
            return path
    return None


def get_repo_root() -> Path:
    """Return the repository root directory."""
    return REPO_ROOT


def get_company_config_root() -> Path:
    """Return the active company-config root, preferring existing modern aliases."""
    existing_dir = _first_existing_dir(REPO_ROOT, COMPANY_CONFIG_CANDIDATES)
    if existing_dir is not None:
        return existing_dir
    return REPO_ROOT / LEGACY_COMPANY_CONFIG_DIRNAME


def get_company_config_dir(company: str) -> Path:
    """Return the directory containing configuration JSON files for a company."""
    return get_company_config_root() / company


def get_default_company_config_dir() -> Path:
    """Return the fallback configuration directory used when a company file is missing."""
    return get_company_config_dir("Default")


def resolve_company_config_paths(company: str) -> Tuple[str, str, str]:
    """Resolve the three config file paths, falling back to Default for missing files."""
    config_dir = get_company_config_dir(company)
    default_config_dir = get_default_company_config_dir()

    config_paths = []
    for config_file in CONFIG_FILES:
        company_config_path = config_dir / config_file
        default_config_path = default_config_dir / config_file
        selected_path = company_config_path if company_config_path.exists() else default_config_path
        config_paths.append(str(selected_path))

    return tuple(config_paths)


def get_workspace_root() -> Path:
    """Return the workspace root, supporting both legacy and newer directory names."""
    existing_dir = _first_existing_dir(REPO_ROOT, WORKSPACE_DIR_CANDIDATES)
    if existing_dir is not None:
        return existing_dir
    return REPO_ROOT / "outputs"


def ensure_workspace_root() -> Path:
    """Create the workspace root if needed and return it."""
    workspace_root = get_workspace_root()
    workspace_root.mkdir(parents=True, exist_ok=True)
    return workspace_root


def build_workspace_name(project_name: str, org_name: str, timestamp: str) -> str:
    """Build the canonical workspace directory name for a generated project."""
    return "_".join([project_name, org_name, timestamp])


def get_workspace_path(project_name: str, org_name: str, timestamp: str) -> Path:
    """Return the generated project's workspace directory path."""
    return ensure_workspace_root() / build_workspace_name(project_name, org_name, timestamp)


def get_log_path(project_name: str, org_name: str, timestamp: str) -> Path:
    """Return the default log file path for a generated project run."""
    return ensure_workspace_root() / f"{build_workspace_name(project_name, org_name, timestamp)}.log"


def get_memory_dir() -> Path:
    """Return the directory used by the optional memory subsystem."""
    return REPO_ROOT / "chatdev" / "memory"
