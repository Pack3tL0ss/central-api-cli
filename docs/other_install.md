# Alternative methods for installing CentralCLI

## Installing via `uv`  as descibed on [the main docs page](https://central-api-cli.readthedocs.io) is the reccomended way to install CentralCLI.  Below are some alternative, less preferred methods.


### pipx
`centralcli` can also be installed via pipx, similar to `uv` pipx will install `centralcli` in an isolated environment, and expose the `cencli` command in PATH.

> The first section below is for Debian based systems refer to [pipx documentation](https://pipx.pypa.io/stable/installation/) for instructions on other OSs.
  ```bash
  # install pipx (Debian)
  sudo apt update
  sudo apt install pipx
  pipx ensurepath

  # install central CLI
  pipx install centralcli --include-deps

  # optional install speedups for centralcli (this pulls in additional optional dependencies, that can improve performance.)  Minimal impact in most scenarios.
  pipx install centralcli[speedups] --force  # force if centralcli was already installed and you are just adding speedups
  ```

Then to Upgrade `centralcli`
```bash
pip upgrade centralcli
```

### pip (manually install in virtual environment)

> The example below is for Debian based systems, where `apt` is referenced but should be easy to translate to other OSs given you have some familiarity with the package management commands (i.e. `dnf`).  On Windows python should install with pip.  The pip commands are still valid.
  ```shell
  # (Debian) If you don't have pip
  sudo apt update
  sudo apt install python3-pip
  sudo apt install python3-virtualenv

  # create a directory to store the venv in
  cd ~                                              # ensure you are in your home dir
  mkdir .venvs                                      # creates hidden .venvs dir to store venv in
  cd .venvs                                         # change to that directory
  export DEB_PYTHON_INSTALL_LAYOUT='deb'            # Just ensures the directory structure for simpler instructions (Ubuntu 22.04 changed the dir layout of venvs without it)
  python3 -m virtualenv centralcli --prompt cencli  # prompt is optional
  source centralcli/bin/activate                    # activates the venv

  # Install centralcli
  pip install centralcli

  # optional install speedups for centralcli (this pulls in additional optional dependencies, that can improve performance.)  Minimal impact in most scenarios.
  pip install centralcli[speedups]

  which centralcli # Should return ~/.venvs/centralcli/bin/centralcli

  # for BASH shell Update .bashrc to update PATH on login (keep the single quotes)
  echo 'export PATH="$PATH:$HOME/.venvs/centralcli/bin"' >> ~/.bashrc

  # for zsh or others, do the equivalent... i.e. update .zshrc in a similar manner
  ```

  Then to upgrade:
```bash
~/.venvs/centralcli/bin/pip install -U centralcli
```

### pip (in system python environment)
[Requires python3.10 or above and pip.](#if-you-do-not-have-python)

It's recommended to use the `uv` install method above, however if you don't use a lot of python apps (meaning a dependency conflict with other apps is not a concern).  Then simply installing via pip is possible (*albeit not recommended*).
> This method is primarily feasible on Windows, as current versions of many Linux distributions do not allow installing apps in the system python environment.


```bash
pip install centralcli

# optional install speedups for centralcli (this pulls in additional optional dependencies, that can improve performance.)  Minimal impact in most scenarios.
pip install centralcli[speedups]
```

Then to upgrade:
```bash
pip install -U centralcli
```

### if you do not have python

- You can get it for any platform @ [https://www.python.org](https://www.python.org)
- On Windows it's also available in the Windows store, and via winget.