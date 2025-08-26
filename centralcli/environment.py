from os import environ


class EnvVar:
    def __init__(self, workspace: str = "CENCLI_WORKSPACE", debug: str = "CENCLI_DEBUG"):
        self.workspace = workspace
        self.debug = debug

env_var = EnvVar()
classic_env_var = EnvVar("ARUBACLI_ACCOUNT", "ARUBACLI_DEBUG")

class Env:
    _is_pytest: bool = bool(environ.get("PYTEST_VERSION"))

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
        return self._is_pytest

    @is_pytest.setter
    def is_pytest(self, value: bool) -> bool:
        if value:
            environ["PYTEST_VERSION"] = "MOCK_TEST"
            self._is_pytest = True
        else:
            del environ["PYTEST_VERSION"]
            self._is_pytest = False

        return self._is_pytest

    @property
    def current_test(self) -> str | None:
        cur_test = environ.get("PYTEST_CURRENT_TEST")
        if cur_test:
            return cur_test.split("::")[1].split()[0]


env = Env()