import nox
from pathlib import Path

@nox.session(python=['venv3.9/bin/python3', 'venv3.10/bin/python3', 'venv3.11/bin/python3', 'venv3.12/bin/python3', 'venv3.13/bin/python3'])
def tests(session):
    requirements = nox.project.load_toml("pyproject.toml")["project"]["dependencies"]
    session.install(*requirements)
    session.install('pytest')
    session.run('pytest')

@nox.session()
def lint(session):
    session.install('ruff')
    session.run('ruff', 'check', Path(__file__).parent / 'centralcli', '--config', Path(__file__).parent / 'pyproject.toml')