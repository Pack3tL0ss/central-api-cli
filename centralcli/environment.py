from os import environ


class EnvVar:
    def __init__(self, workspace: str = "CENCLI_WORKSPACE", debug: str = "CENCLI_DEBUG"):
        self.workspace = workspace
        self.debug = debug

env_var = EnvVar()
classic_env_var = EnvVar("ARUBACLI_ACCOUNT", "ARUBACLI_DEBUG")

class Env:
    def __init__(self):
        self.workspace: str = environ.get(env_var.workspace) or environ.get(classic_env_var.workspace)

    @property
    def debug(self) -> bool:
        _debug = environ.get(env_var.debug) if environ.get(env_var.debug) is not None else environ.get(classic_env_var.debug)
        return True if _debug and _debug.lower() in ["1", "true"] else False

    @property
    def is_completion(self) -> bool:
        return bool(environ.get("COMP_WORDS"))

    @property
    def is_pytest(self) -> bool:
        return bool(environ.get("PYTEST_VERSION"))


env = Env()