from centralcli import config, utils, log
from pathlib import Path
import sys


# -- break up arguments passed as single string from vscode promptString --
def vscode_arg_handler():

    def get_arguments_from_import(import_file: str, key: str = None) -> list:
        """Get arguments from default import_file (stored_tasks.yaml)

        Args:
            import_file (str): name of import file
            key (str, optional): return single value for specific key if provided. Defaults to None.

        Returns:
            list: updated sys.argv list.
        """
        # args = utils.read_yaml(import_file)
        args = config.get_file_data(Path(import_file))
        if key and key in args:
            args = args[key]

        sys.argv += args

        return sys.argv

    try:
        if len(sys.argv) > 1:
            if " " in sys.argv[1] or not sys.argv[1]:
                vsc_args = sys.argv.pop(1)
                if vsc_args:
                    if "\\'" in vsc_args:
                        _loc = vsc_args.find("\\'")
                        _before = vsc_args[:_loc - 1]
                        _before = _before.split()
                        _str_end = vsc_args.find("\\'", _loc + 1)
                        sys.argv += [i.rstrip(',') for i in _before if i != ',']
                        sys.argv += [f"{vsc_args[_loc + 2:_str_end]}"]
                        _the_rest = vsc_args[_str_end + 2:].split()
                        sys.argv += [i.rstrip(',') for i in _the_rest if i != ',']
                    else:
                        sys.argv += vsc_args.split()

        if len(sys.argv) > 2:
            _import_file, _import_key = None, None
            if sys.argv[2].endswith((".yaml", ".yml", "json")):
                _import_file = sys.argv.pop(2)
                if not utils.valid_file(_import_file):
                    if utils.valid_file(config.dir.joinpath(_import_file)):
                        _import_file = config.dir.joinpath(_import_file)

                if len(sys.argv) > 2:
                    _import_key = sys.argv.pop(2)

                sys.argv = get_arguments_from_import(_import_file, key=_import_key)

    except Exception as e:
        log.exception(f"Exception in vscode arg handler (arg split) {e.__class__.__name__}.{e}", show=True)
        return

    # update launch.json default if launched by vscode debugger
    try:
        # Update prev_args history file
        history_lines = None
        history_file = config.base_dir / ".vscode" / "prev_args"
        this_args = " ".join(sys.argv[1:])
        if not this_args:
            return

        if history_file.is_file() and this_args.strip():
            history_lines = history_file.read_text().splitlines()

            if this_args in history_lines:
                _ = history_lines.pop(history_lines.index(this_args))
                history_lines.insert(0, _)
            else:
                history_lines.insert(0, this_args)
                if len(history_lines) > 10:
                    _ = history_lines.pop(10)
            history_file.write_text("\n".join(history_lines) + "\n")

        # update launch.json default arg
        do_update = False
        launch_data = None
        launch_file = config.base_dir / ".vscode" / "launch.json"
        launch_file_bak = config.base_dir / ".vscode" / "launch.json.bak"
        if launch_file.is_file():
            launch_data = launch_file.read_text()
            launch_data = launch_data.splitlines()
            for idx, line in enumerate(launch_data):
                if "default" in line and "// VSC_PREV_ARGS" in line:
                    _spaces = len(line) - len(line.lstrip(" "))
                    new_line = f'{" ":{_spaces}}"default": "{this_args}"  // VSC_PREV_ARGS'
                    if line != new_line:
                        do_update = True
                        log.debug(f"changing default arg for promptString:\n"
                                  f"\t from: {line}\n"
                                  f"\t to: {new_line}"
                                  )
                        launch_data[idx] = new_line

                elif history_lines and "options" in line and "// VSC_ARG_HISTORY" in line:
                    import json
                    _spaces = len(line) - len(line.lstrip(" "))
                    new_line = f'{" ":{_spaces}}"options": {json.dumps(history_lines)},  // VSC_ARG_HISTORY'
                    if line != new_line:
                        do_update = True
                        log.debug(f"changing options arg for pickString:\n"
                                  f"\t from: {line}\n"
                                  f"\t to: {new_line}"
                                  )
                        launch_data[idx] = new_line

        if do_update and launch_data:
            # backup launch.json only if backup doesn't exist already
            if not launch_file_bak.is_file():
                import shutil
                shutil.copy(launch_file, launch_file_bak)

            # update launch.json
            launch_file.write_text("\n".join(launch_data) + "\n")

    except Exception as e:
        log.exception(f"Exception in vscode arg handler (launch.json update) {e.__class__.__name__}.{e}", show=True)
