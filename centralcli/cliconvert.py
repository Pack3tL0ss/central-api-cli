#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

import typer
from rich import print

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, config
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, config
    else:
        print(pkg_dir.parts)
        raise e

app = typer.Typer()

@app.command()
def template(
    template: Path = typer.Argument(..., help="j2 template to convert", exists=True),
    var_file: Path = typer.Argument(
        None,
        help="Optional variable file, will automatically look for file with same name as template and supported extension/format.",
        exists=True,
        ),
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    workspace: str = cli.options.workspace,
) -> None:
    """Convert jinja2 (j2) template into final form based on variable file.

    --var-file is optional, If not provided cencli will look in the same dir as the template
    for a file with the same name (as the template) and a supported extension.

    cencli supports most common extension for variable import:
    '.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf'

    """
    if not var_file:
        var_file = [
            template.parent / f"{template.stem}{sfx}"
            for sfx in config.valid_suffix
            if Path.joinpath(template.parent, f"{template.stem}{sfx}").exists()
        ]
        if not var_file:
            print(f":x: No variable file found matching template base-name [cyan]{template.stem}[/]")
            print(f"and valid extension: [cyan]{'[/], [cyan]'.join(config.valid_suffix)}[/].")
            raise typer.Exit(1)
        elif  len(var_file) > 1:
            cli.exit(f"Too many matches, found [cyan]{len(var_file)}[/] files with base-name [cyan]{template.stem}[/].")
        else:
            var_file = var_file[0]
    final_config = utils.generate_template(template, var_file=var_file)
    cli.display_results(data=final_config.splitlines(), outfile=outfile)


@app.command("config", hidden=not config.is_old_cfg)
def config_(
    yes: bool = cli.options.yes,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
) -> None:
    """Convert Existing cencli config file to [dark_olive_green2]CFG_VERSION: 2[/]. Required to add support for [bright_green]GLP[/] and [dark_orange3]New Central[/].

    This command will parse the legacy cencli config [cyan]config.yaml[/] and convert it to [dark_olive_green2]CFG_VERSION: 2[/].
    The existing config will be backed up to [cyan]config.yaml.bak[/], and a new config will be created.

    To enable Commands that use GreenLake or New Central APIs please add
    glp:
        client_id: <GLP Client ID>
        client_secret: <GLP Client Secret>
    to the workspace configuration.

    Refer to: https://raw.githubusercontent.com/Pack3tL0ss/central-api-cli/master/config/config.yaml.example
    for example with all available options.
    """
    if not config.file.is_file():
        cli.exit(f"Config file {config.file} not found.")
    if not config.is_old_cfg:
        cli.exit("Your config already appears to be [dark_olive_green2]CFG_VERSION: 2[/] compliant.")

    print("Convert existing [cyan]cencli[/] config to [dark_olive_green2]CFG_VERSION: 2[/]")
    cli.confirm(yes)
    bak_config = config.file.parent / f"{config.file.name}.bak"
    config.file.rename(bak_config)
    caption = [
        f"New config Written to {config.file}",
        f"Previous config backed up to {bak_config}",
        "[yellow]:information:[/]  Add [cyan]glp:[/] section [dim italic](within a workspace)[/] with [cyan]client_id[/] and [cyan]client_secret[/] to enable commands that utilize GreenLake and/or New Central"
    ]
    config.file.write_text(config.new_config)
    cli.display_results(data=config.new_config, caption=caption, tablefmt="simple")

callback_str = f"Convert j2 Templates{'' if not config.is_old_cfg else ' or convert the cencli config to CFG_VERSION: 2'}"
@app.callback(help=callback_str)
def callback():
    pass


if __name__ == "__main__":
    app()
