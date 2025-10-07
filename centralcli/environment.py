from os import environ


class EnvVar:
    def __init__(self, workspace: str = "CENCLI_WORKSPACE", debug: str = "CENCLI_DEBUG"):
        self.workspace = workspace
        self.debug = debug

env_var = EnvVar()
classic_env_var = EnvVar("ARUBACLI_ACCOUNT", "ARUBACLI_DEBUG")


def _get_current_test() -> str | None:  # pragma: no cover only used when capturing responses for tests
    cur_test = environ.get("PYTEST_CURRENT_TEST")
    if cur_test:
        return cur_test.split("::")[1].split()[0]


class Env:
    _is_pytest: bool = bool(environ.get("PYTEST_VERSION"))
    _cur_test: str | None = _get_current_test

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
    def is_pytest(self, value: bool) -> bool:  # pragma: no cover  This only hits outside of pytest runs with --mock flag
        if value:
            environ["PYTEST_VERSION"] = "MOCK_TEST"
            self._is_pytest = True
        else:
            del environ["PYTEST_VERSION"]
            self._is_pytest = False

        return self._is_pytest

    @property
    def current_test(self) -> str | None:  # pragma: no cover only used when capturing responses for tests
        return self._cur_test

    @current_test.setter
    def current_test(self, value: str | None) -> str | None:  # pragma: no cover  This only hits outside of pytest used with --test <name of test> which implies --capture-raw to capture response for use in automated testing.
        value = value if value.startswith("test_") else f"test_{value}"
        environ["PYTEST_CURRENT_TEST"] = value
        self._cur_test = value

        return self._is_pytest

env = Env()