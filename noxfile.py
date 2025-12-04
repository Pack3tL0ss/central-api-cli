from nox import Session, options
from nox_uv import session
from pathlib import Path

options.default_venv_backend = "uv"

@session(
    python=["3.10", "3.11", "3.12", "3.13", "3.14"],
    uv_groups=["test"],
    uv_extras=["hook-proxy"],
)
def test(s: Session) -> None:
    s.run("python", "-m", "pytest")

@session(uv_only_groups=["lint"])
def lint(s: Session) -> None:
    s.run("ruff", "check", ".")
    s.run('ruff', 'check', Path(__file__).parent / 'centralcli', '--config', Path(__file__).parent / 'pyproject.toml')

