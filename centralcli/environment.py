"""
This provides consistency and a single place to see the various environment variables supported by the CLI
"""
from os import environ


class EnvVar:
    def __init__(self):
        self.workspace = "ARUBACLI_ACCOUNT" if "ARUBACLI_ACCOUNT" in environ else "CENCLI_WORKSPACE"
        self.debug = "ARUBACLI_DEBUG" if "ARUBACLI_DEBUG" in environ else "CENCLI_DEBUG"
        self.dest_workspace = "CENCLI_DEST_WORKSPACE"
        self.do_retry = "CENCLI_DO_RETRY"
        self.delete_ws = "CENCLI_DELETE_WORKSPACE"
        self.move_ws = "CENCLI_MOVE_WORKSPACE"
        self.src_workspace = "CENCLI_SRC_WORKSPACE"  # TODO replace this w delete ws
        self.to_group = "CENCLI_TO_GROUP"
        self.no_refresh = "CENCLI_NO_REFRESH"
        self.no_sub = "CENCLI_NO_SUB"
        self.cx_retain_config = "CENCLI_CX_RETAIN_CONFIG"
        self.cx_retain_config_all = "CENCLI_CX_RETAIN_CONFIG_ALL"
        self.watcher_dir = "CENCLI_WATCHER_DIR"
        self.import_sites = "CENCLI_IMPORT_SITES"
        self.dev_search_dir = "CENCLI_DEV_SEARCH_DIR"  # Only applies to vscode debugger
        self.watcher_no_moves = "CENCLI_WATCHER_NO_MOVES"
        self.watcher_no_deletes = "CENCLI_WATCHER_NO_DELETES"
        self.watcher_current_alerts_past = "CENCLI_WATCHER_CURRENT_ALERTS_PAST"
        self.migrate_lldp_file = "CENCLI_MIGRATE_LLDP_FILE"


env_var = EnvVar()


class Env:
    _is_pytest: bool = bool(environ.get("PYTEST_VERSION"))

    def __init__(self):
        self.workspace: str = environ.get(env_var.workspace)
        self.dest_workspace = environ.get(env_var.dest_workspace)
        self.src_workspace = environ.get(env_var.src_workspace)
        self.delete_workspace = environ.get(env_var.delete_ws)
        self.move_workspace = environ.get(env_var.move_ws)
        self.no_refresh = environ.get(env_var.no_refresh)
        self.to_group = environ.get(env_var.to_group)
        self.import_site = environ.get(env_var.import_sites)
        self.no_sub = environ.get(env_var.no_sub)
        self.cx_retain_config = environ.get(env_var.cx_retain_config)
        self.cx_retain_config_all = environ.get(env_var.cx_retain_config_all)
        self.watcher_dir = environ.get(env_var.watcher_dir)
        self.do_retry = environ.get(env_var.do_retry)
        self.user = environ.get("USER")

    @property
    def watcher_no_moves(self):
        return environ.get(env_var.watcher_no_moves)

    @property
    def watcher_no_deletes(self):
        return environ.get(env_var.watcher_no_deletes)

    @property
    def is_dev_user(self) -> bool:
        return self.user == "wade"

    @property
    def debug(self) -> bool:
        _debug = environ.get(env_var.debug)
        return True if _debug and _debug.lower() in ["1", "true"] else False

    @property
    def is_completion(self) -> bool:
        return bool(environ.get("COMP_WORDS"))

    @property
    def is_pytest(self) -> bool:
        return Env._is_pytest

    @is_pytest.setter
    def is_pytest(self, value: bool) -> bool:  # pragma: no cover  This only hits outside of pytest runs with --mock flag
        if value:
            environ["PYTEST_VERSION"] = "MOCK_TEST"
            Env._is_pytest = True
        else:
            del environ["PYTEST_VERSION"]
            Env._is_pytest = False

        return Env._is_pytest

    @property
    def current_test(self) -> str | None:  # pragma: no cover only used when capturing responses for tests
        cur_test = environ.get("PYTEST_CURRENT_TEST")
        if cur_test:
            return cur_test if "::" not in cur_test else cur_test.split("::")[1].split()[0].split("[")[0]

    @current_test.setter
    def current_test(self, value: str | None) -> str | None:  # pragma: no cover  This only hits outside of pytest used with --test <name of test> which implies --capture-raw to capture response for use in automated testing.
        value = value if value.startswith("test_") else f"test_{value}"
        environ["PYTEST_CURRENT_TEST"] = value
        self._cur_test = value

        return self._is_pytest


env = Env()