#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

import typer

from centralcli import common, config, render
from centralcli.clicommon import Mac
from rich.markup import escape

app = typer.Typer()


def _generate_bssids_from_file(file: Path, out: Path = None, num_bssids: int = 6):
    out_file = out or Path(str(file).replace(file.suffix, f"_out{file.suffix}"))
    file_data = config.get_file_data(file)

    if not file_data:
        common.exit(f"No data found in {file}")

    macs = [Mac(ap["mac"] , bssids=True, num_bssids=6) for ap in file_data]
    invalid_macs = [(idx, m) for idx, m in enumerate(macs, start=2) if not m.ok]
    if invalid_macs:
        err = "\n".join([f"Mac: {m.orig} on row {row} in invalid." for row, m in invalid_macs])
        common.exit(err)
    out_data = []
    for ap, mac_obj in zip(file_data, macs):
        to_end = ["BSSID", "LocationId", "LocationValue", "Description"]
        bssids = [bssid for radio_bssid_list in mac_obj.bssids.values() for bssid in radio_bssid_list[0:num_bssids]]
        out_data += [{**{k: v for k, v in ap.items() if k not in to_end}, "BSSID": bssid, "LocationId": ap.get("LocationId"), "Description": ap.get("Description")} for bssid in bssids]
        # out_data += [{**{k: v for k, v in ap.items() if k not in to_end}, "BSSID": bssid, "LocationId": ap.get("LocationId"), "LocationValue": ap.get("LocationValue"), "Description": ap.get("Description")} for bssid in bssids]

    headers = ",".join(out_data[0].keys())
    values = "\n".join([",".join(['' if v is None else v for v in inner.values()]) for inner in out_data])
    csv_data = f"{headers}\n{values}"
    written = out_file.write_text(csv_data)

    render.console.print(csv_data)
    render.console.print(f"Output written to {out_file}")
    return written


# F070-11-1600 Market Street-Floor11
def _build_description(ap_name: str, site_name: str | None, description: str | None) -> str:
    if site_name is None and description:
        return description
    _, site_code, floor, _, _ = map(lambda txt: txt.removeprefix("WAP").removeprefix("wap"), ap_name.split("-"))
    padded_floor = floor if len(floor) == 2 else f"{floor:02s}"
    floor = padded_floor.removeprefix("0")
    return f"{site_code}-{padded_floor}-{site_name}-Floor{floor}"


def bssids_from_xls(
    file: Path,
    site: str = None,
    out: Path = None,
    bssids: bool = True,
    num_bssids: int = 6,
    bssid_out: Path = None
):
    prepped_file = out or file.parent / f"{file.stem}.csv"
    import tablib
    import importlib.util
    if importlib.util.find_spec("et_xmlfile") is None:
        common.exit(f"Missing optional xlsx support.  re-install centralcli with optional dependency to add support for xlsx files. [cyan]uv tool install {escape('centralcli[xlsx]')}[/]\n[italic]No need to uninstall, just re-run as described to add support for xlsx[/]")

    book = tablib.Databook()
    book.xlsx = file.read_bytes()  # type: ignore

    datasets = [ds for ds in book.sheets() if "summary" not in ds.title.lower()]
    out_keys = ["name", "serial", "mac", "BSSID", "LocationId", "Description"]
    output = []
    for ds in datasets:
        as_dict = [{k.lower().removesuffix(" number").removesuffix("-address"): v for k, v in inner.items()} for inner in ds.dict]
        as_dict = [{**inner, "BSSID": None, "LocationId": None, "Description": None if ds.title.lower().startswith("spare") else _build_description(inner['name'], site_name=site, description=inner.get("Description", inner.get("description")))} for inner in as_dict if any(inner.values())]
        output += as_dict

    header = ",".join(out_keys)
    written = prepped_file.write_text(
        "\n".join([header, *[",".join('' if ap.get(key) is None else ap[key] for key in out_keys) for ap in output]])
    )
    if not bssids or not written:
        common.exit(f"Wrote {written} bytes to {prepped_file.name}", code=0 if written else 1)

    written = _generate_bssids_from_file(prepped_file, out=bssid_out, num_bssids=num_bssids)
    common.exit(code=0 if written else 1)

@app.command()
def bssids(
    ap_mac: str = typer.Argument(None, help="AP Mac Address", show_default=False),
    file: Path = typer.Option(None, help="fetch MACs from file for bssid calc", exists=True, show_default=False),
    dir: Path = typer.Option(None, help="process all files in dir for bssid calc", exists=True, show_default=False),
    site: str = typer.Option(None, "--site", "-s", help="The official name of the site (from SFDC), not required if [cyan]description[/] field is in the input file.  [dim italic]Only applies with [cyan]--file[/][/] :triangular_flag:"),
    num_bssids: int = typer.Option(None, "-n", help="The number of BSSIDs to generate in output file.  [dim italic]Only applies with [cyan]--file[/][/] :triangular_flag:"),  # TODO render.help_block add helper for this common... Valid/Only applies with --{flag} :triangular_flag:
    vertical: bool = typer.Option(False, "-V", "--vertical", help="Display BSSIDs vertically with no headers"),
    out: Path = typer.Option(None, help="Output to file.  --file option will always create an output file ... by default will create new file with same name as --file with _out appended to the file name.",),
):
    """Generate bssids based on AP MAC(s)

    Using --file :triangular_flag: will result in a file containing the headers necessary for import into MS Teams for e911 location.
    """
    if ap_mac and Path(ap_mac).exists():
        file = Path(ap_mac)  # allow them to specify the file as the first arg

    if file:
        if file.suffix == ".xlsx":
            bssids_from_xls(file, site=site, num_bssids=num_bssids, bssid_out=out)
        written = _generate_bssids_from_file(file, out=out, num_bssids=num_bssids)
        common.exit(code=0 if written else 1)
    elif dir:
        files = [file for file in dir.iterdir() if file.suffix in [".csv", ".yaml", ".yml", ".json"]]
        written = [_generate_bssids_from_file(file, out=out, num_bssids=num_bssids) for file in files]
        common.exit(code=0 if all(written) else 1)
    else:
        typer.echo(Mac(ap_mac, bssids=True, num_bssids=num_bssids, tablefmt="table" if not vertical else "vertical"))


@app.callback()
def callback():
    """Generate bssids based on AP MAC(s)"""
    pass


if __name__ == "__main__":
    app()
