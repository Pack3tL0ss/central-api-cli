import json
import shutil
from pathlib import Path
from typing import Any, Callable, Literal
import random

import yaml

from centralcli import common, config, utils
from centralcli.exceptions import ImportException

CAAS_COMMANDS = """cmds:
  - interface vlan 66
  - no ip address
  - !
  - no interface vlan 66
  - no vlan delme-66 66
  - no vlan-name delme-66
  - no vlan 66
"""


caas_commands_group_data = """groups:
  - cencli_test_group1
  - cencli_test_group4
  - cencli_test_cloned
"""

caas_commands_site_data = """sites:
  - cencli_test_site1
  - cencli_test_site4
"""

caas_commands_invalid = """invalid:
  - invalid1
  - invalid2
"""

caas_commands_gateways_data  = """gateways:
  - mock-gw
"""

banner_text_j2 = r"""
banner motd "___       __      _________    ______        ______"
banner motd "__ |     / /_____ ______  /_______  / ______ ___  /_"
banner motd "__ | /| / /_  __ `/  __  /_  _ \_  /  _  __ `/_  __ \"
banner motd "__ |/ |/ / / /_/ // /_/ / /  __/  /___/ /_/ /_  /_/ /"
banner motd "____/|__/  \__,_/ \__,_/  \___//_____/\__,_/ /_.___/"
banner motd "Connected To: {{ name }} AP"
"""


caas_file_data = {
    "groups": caas_commands_group_data,
    "sites": caas_commands_site_data,
    "invalid": caas_commands_invalid,
    "gateways": caas_commands_gateways_data
}

def get_test_data():
    test_file = Path(__file__).parent / 'test_data.yaml'
    if not test_file.is_file():
        raise FileNotFoundError(f"Required test file {test_file} is missing.  Refer to {test_file.name}.example")  # pragma: no cover
    return config.get_file_data(test_file)


def setup_cert_file(cert_path: str, sfx: str = "pem") -> Path:
    test_cert_file = config.cache_dir / f"test_runner_cert.{sfx}"
    file = Path(cert_path)
    if sfx == "pem":
        test_cert_file.write_text(file.read_text())
    else:
        # test_cert_file.write_bytes(file.read_bytes())
        shutil.copy(file, test_cert_file)

    return test_cert_file

def _csv_dump(data: list[dict[str, Any]]) -> str:
    all_keys = list(set([key for d in data for key in d.keys()]))
    data = [{k: d.get(k) for k in all_keys} for d in data]

    data = utils.strip_no_value(data)  # Remove columns where all rows have no value
    return "\n".join([",".join(k for k in data[0].keys()), *[",".join(str(v) for v in inner.values()) for inner in data]])

def _get_dump_func(sfx: str) -> Callable:
    dump_func = {
        "json": json.dumps,
        "yaml": yaml.safe_dump,
        "csv": _csv_dump,
        "txt": lambda data: "serial\n" + "\n".join([inner["serial"] for inner in data])  # only used for devices as txt file with serial per line
    }
    return dump_func.get(sfx, json.dumps)

def setup_batch_import_file(test_data: dict | str, import_type: str = "sites", invalid: bool = False, duplicate: bool = False) -> Path:
    data = test_data["batch"]
    keys = import_type.split(":")
    import_type = keys[0]
    sfx = "json" if len(keys) < 2 else keys[1]
    data = data[import_type] if isinstance(data[import_type], str) or sfx not in data[import_type] else data[import_type][sfx]

    def _invalidate_fields(data: list[dict], fields: list[str]) -> list[dict]:
        return [{k if k not in fields else f"invalid{idx}": v for idx, (k, v) in enumerate(inner.items())} for inner in data]

    if isinstance(data, str):  # pragma: no cover
        seed_file = Path(data)
        data = common._get_import_file(seed_file, import_type=import_type)
    else:
        data = data


    if invalid:
        if import_type == "devices":
            data = _invalidate_fields(data, fields=["serial"])
            # data = [{k if k != "serial" else "invalid": v for k, v in inner.items()} for inner in data]
        elif import_type == "sites":
            data = _invalidate_fields(data, fields=["site", "site_name", "name"])
            # data = [{k if k not in ["site", "site_name", "name"] else "invalid": v for k, v in inner.items()} for inner in data]
        elif import_type == "cloud_auth_macs":
            data = _invalidate_fields(data, fields=["mac", "Mac Address"])
        else:  # pragma: no cover
            ...

    if duplicate:
        data += [data[0]]

    test_batch_file = config.cache_dir / f"test_runner_{import_type}{'' if not duplicate else '_w_dup'}{'' if not invalid else '_invalid'}.{sfx}"
    out_str = _get_dump_func(sfx)(data)
    res = test_batch_file.write_text(out_str)

    if not res:
        raise ImportException("Batch import file creation from test_data returned 0 chars written")  # pragma: no cover

    return test_batch_file

def _create_test_ap_import_file(test_data: dict[str, str]):
    test_batch_file = config.cache_dir / "test_runner_subscriptions_test_ap.json"
    _x_ = "{\n"
    _ = test_batch_file.write_text(
        f"{_x_}\"{test_data['serial']}\": {_x_}"
        f"  \"mac\": \"{test_data['mac']}\",\n"
        f"  \"group\": \"{test_data['group']}\",\n"
        "  \"type\": \"ap\"\n"
        "  }\n"
        "}\n"
    )

    return test_batch_file

def _create_banner_update_import_devices(test_data: dict[str, str]):
    test_batch_file = config.cache_dir / "test_runner_device_banner_ap_import_file.csv"
    header = ",".join(test_data.keys())
    values = ",".join([test_data[key] for key in header.split(",")])
    test_batch_file.write_text(f"{header}\n{values}\n")

    return test_batch_file

def _create_banner_update_import_groups():
    test_batch_file = config.cache_dir / "test_runner_group_banner_ap_import_file.csv"
    header = "name,"
    values = ",\n".join(map(lambda g: f"cencli_test_group{g}", [1, 2, 3]))
    test_batch_file.write_text(f"{header}\n{values},\n")

    return test_batch_file

def _create_banner_file(template: bool = True):
    if template:
        test_batch_file = config.cache_dir / "test_runner_ap_banner.j2"
        test_batch_file.write_text(banner_text_j2.lstrip())
    else:
        test_batch_file = config.cache_dir / "test_runner_ap_banner"
        file_data = "\n".join([line.removeprefix('banner motd "').rstrip('"') for line in banner_text_j2.lstrip().splitlines() if "{{" not in line])
        file_data = f"{file_data.strip()}\n"
        test_batch_file.write_text(file_data)

    return test_batch_file


def _create_caas_commands_file(scope: Literal["groups", "sites", "gateways", "invalid", "empty"]) -> Path:
    commands_file = config.cache_dir / f"test_runner_caas_{scope}.yaml"
    if scope != "empty":
        data = f"{caas_file_data[scope]}{CAAS_COMMANDS}"
        commands_file.write_text(data)
    else:
        commands_file.touch()
    return commands_file


def _create_invalid_var_file(file: str, bad_json: bool = False) -> Path:
    var_file = Path(file)
    test_var_file = config.cache_dir / f"test_runner_invalid_variables{'_bad_json' if bad_json else ''}{var_file.suffix}"
    file_data = "".join([line for line in var_file.read_text().splitlines(keepends=True) if "_sys_lan_mac" not in line])
    if bad_json:
        test_var_file.write_text(file_data.lstrip("{").lstrip("["))
    else:
        test_var_file.write_text(file_data)

    return test_var_file


def setup_deploy_file(group_file: Path, site_file: Path, label_file: Path, device_file: Path) -> Path:
    test_deploy_file = config.cache_dir / "test_runner_deploy.yaml"
    test_deploy_file.write_text(
        f"groups: !include {group_file}\n"
        f"sites: !include {site_file}\n"
        f"labels: !include {label_file}\n"
        f"devices: !include {device_file}\n"
    )
    return test_deploy_file


def setup_j2_file() -> Path:
    test_j2_file = config.cache_dir / "test_runner_template.j2"
    test_j2_file.write_text(
        "This is a simple {{some_var}} j2 template file\n"
    )
    return test_j2_file

def create_var_file(seed_file, file_type: str = "json", flat: bool = False):
    file_data = config.get_file_data(Path(seed_file))
    out_file = config.cache_dir / f"test_runner_variables{'_flat' if flat else ''}.{file_type}"
    if file_type == "csv":
        all_keys = [k for item in file_data.values() for k in list(item.keys())]
        rows = [[item.get(k, "") for k in all_keys] for item in file_data.values()]
        out = "\n".join([",".join(all_keys), *[",".join([item.replace(',', '~').replace('\n', '<br>') for item in r]) for r in rows]])
        out_file.write_text(out)
    else:
        if flat:
            key = list(file_data.keys())[0]
            file_data = file_data[key]
        out_file.write_text(json.dumps(file_data, indent=2, sort_keys=False))
    return out_file

def _create_not_exist_site_file(file: Path, none_exists: bool = False) -> Path:
    site_data = json.loads(file.read_text())
    if not none_exists:
        site_data[-1]["name"] = "not_exist_site"
        out_file = file.parent / f"{file.stem}_one_not_exist{file.suffix}"
    else:
        site_data = [{k: v if not k.endswith("name") else f"not_exist_site{idx}" for k, v in sites.items()} for idx, sites in enumerate(site_data, start=1)]
        out_file = file.parent / f"{file.stem}_none_exist{file.suffix}"

    out_file.write_text(json.dumps(site_data, indent=4))
    return out_file

def _create_not_exist_device_file(file: Path, none_exists: bool = False) -> Path:
    dev_data = json.loads(file.read_text())
    def not_exist_dict(inner: dict) -> dict:
        for key in ["serial", "mac", "name"]:
            if key in inner:
                value = inner[key]
                if key == "mac":
                    value = "".join([char for char in value if char not in list(".:-")])
                value = list(value)
                random.shuffle(value)
                inner[key] = "".join(value)
        return inner

    if not none_exists:
        dev_data[-1] = not_exist_dict(dev_data[-1])
        out_file = file.parent / f"{file.stem}_one_not_exist{file.suffix}"
    else:
        dev_data = [not_exist_dict(inner) for inner in dev_data]
        out_file = file.parent / f"{file.stem}_none_exist{file.suffix}"

    out_file.write_text(json.dumps(dev_data, indent=4))
    return out_file

def _create_bssid_dir_and_files(xlsx: bool = False) -> Path:
    file = config.cache_dir / "test_gen_bssid" / f"test_runner_gen_bssids{'' if not xlsx else '_xlsx'}.{'csv' if not xlsx else 'xlsx'}"
    seed_file = Path(test_data["batch"][f"generate_bssids{'' if not xlsx else '_xlsx'}"])
    file.parent.mkdir(exist_ok=True)
    if xlsx:
        file.write_bytes(seed_file.read_bytes())
    else:
        file.write_text(seed_file.read_text())

    return file

test_data: dict[str, Any] = get_test_data()
test_outfile: Path = config.cache_dir / "test_runner_outfile"
test_invalid_empty_file: Path = config.cache_dir / "test_runner_empty_file"
test_invalid_empty_file.touch()
test_device_file: Path = setup_batch_import_file(test_data=test_data, import_type="devices")
test_device_file_w_dup: Path = setup_batch_import_file(test_data=test_data, import_type="devices:yaml", duplicate=True)
test_device_file_one_not_exist: Path = _create_not_exist_device_file(test_device_file)
test_device_file_none_exist: Path = _create_not_exist_device_file(test_device_file, none_exists=True)
test_invalid_device_file_csv: Path = setup_batch_import_file(test_data=test_data, import_type="devices:csv", invalid=True)
test_device_file_txt: Path = setup_batch_import_file(test_data=test_data, import_type="devices:txt")
test_group_file: Path = setup_batch_import_file(test_data=test_data, import_type="groups_by_name")
test_sub_file_yaml: Path = setup_batch_import_file(test_data=test_data, import_type="subscriptions:yaml")
test_sub_file_csv: Path = setup_batch_import_file(test_data=test_data, import_type="subscriptions:csv")
test_sub_file_test_ap: Path = _create_test_ap_import_file(test_data=test_data["test_devices"]["ap"])
test_rename_aps_file: Path = setup_batch_import_file(test_data=test_data, import_type="rename_aps")
test_update_aps_file: Path = setup_batch_import_file(test_data=test_data, import_type="update_aps")
test_verify_file: Path = setup_batch_import_file(test_data=test_data, import_type="verify")
test_label_file: Path = setup_batch_import_file(test_data=test_data, import_type="labels")
test_mpsk_file: Path = setup_batch_import_file(test_data=test_data, import_type="mpsk")
test_site_file: Path = setup_batch_import_file(test_data=test_data)
test_site_file_one_not_exist: Path = _create_not_exist_site_file(test_site_file)
test_site_file_none_exist: Path = _create_not_exist_site_file(test_site_file, none_exists=True)
test_invalid_site_file: Path = setup_batch_import_file(test_data=test_data, import_type="sites:yaml", invalid=True)
test_cert_file: Path = setup_cert_file(cert_path=test_data["certificate"]["pem"])
test_cert_file_p12: Path = setup_cert_file(cert_path=test_data["certificate"]["p12"], sfx="p12")
test_cert_file_der: Path = setup_cert_file(cert_path=test_data["certificate"]["der"], sfx="der")
test_invalid_var_file = _create_invalid_var_file(test_data["template"]["variable_file"])
test_invalid_var_file_bad_json = _create_invalid_var_file(test_data["template"]["variable_file"], bad_json=True)
test_switch_var_file_json = create_var_file(test_data["test_devices"]["switch"]["variable_file"])
test_switch_var_file_flat = create_var_file(test_data["test_devices"]["switch"]["variable_file"], flat=True)
test_switch_var_file_csv = create_var_file(test_data["test_devices"]["switch"]["variable_file"], file_type="csv")
test_deploy_file = setup_deploy_file(group_file=test_group_file, site_file=test_site_file, label_file=test_label_file, device_file=test_device_file)
test_j2_file = setup_j2_file()
test_cloud_auth_mac_file = setup_batch_import_file(test_data=test_data, import_type="cloud_auth_macs")
test_cloud_auth_mac_file_invalid = setup_batch_import_file(test_data=test_data, import_type="cloud_auth_macs", invalid=True)
test_caas_devs_commands_file = _create_caas_commands_file("gateways")
test_caas_groups_commands_file = _create_caas_commands_file("groups")
test_caas_sites_commands_file = _create_caas_commands_file("sites")
test_caas_invalid_commands_file = _create_caas_commands_file("invalid")
test_caas_empty_commands_file = _create_caas_commands_file("empty")
test_banner_file_j2 = _create_banner_file()
test_banner_file = _create_banner_file(template=False)
test_banner_devices_file = _create_banner_update_import_devices(test_data["test_devices"]["ap"])
test_banner_groups_file = _create_banner_update_import_groups()
test_gen_bssid_file = _create_bssid_dir_and_files()
test_gen_bssid_xlsx_file = _create_bssid_dir_and_files(xlsx=True)
test_gen_bssid_xlsx_interim_file = test_gen_bssid_xlsx_file.parent / f"{test_gen_bssid_xlsx_file.stem}.csv"
test_gen_bssid_xlsx_out_file = test_gen_bssid_xlsx_file.parent / "delme.csv"  # we specify --out for this test
test_gen_bssid_file_out = test_gen_bssid_file.parent / f"{test_gen_bssid_file.stem}_out.csv"  # this is deleted
# Persistent files, not deleted
test_ap_ui_group_template = Path(test_data["template"]["ap_ui_group"]["template_file"])
test_ap_ui_group_variables = Path(test_data["template"]["ap_ui_group"]["variable_file"])
gw_group_config_file = config.cache_dir / "test_runner_gw_grp_config"

test_files = [
    test_outfile,
    test_invalid_empty_file,
    test_device_file,
    test_device_file_w_dup,
    test_invalid_device_file_csv,
    test_group_file,
    test_sub_file_csv,
    test_sub_file_yaml,
    test_sub_file_test_ap,
    test_rename_aps_file,
    test_verify_file,
    test_site_file,
    test_site_file_one_not_exist,
    test_site_file_none_exist,
    test_invalid_site_file,
    test_cert_file,
    test_mpsk_file,
    test_invalid_var_file,
    test_label_file,
    test_sub_file_yaml,
    test_deploy_file,
    test_j2_file,
    test_update_aps_file,
    test_switch_var_file_json,
    test_switch_var_file_flat,
    test_switch_var_file_csv,
    test_caas_devs_commands_file,
    test_caas_groups_commands_file,
    test_caas_sites_commands_file,
    test_caas_invalid_commands_file,
    test_caas_empty_commands_file,
    test_cloud_auth_mac_file,
    test_cloud_auth_mac_file_invalid,
    test_banner_file_j2,
    test_banner_file,
    test_banner_devices_file,
    test_banner_groups_file,
    test_gen_bssid_file,
    test_gen_bssid_file_out,
    test_gen_bssid_xlsx_file,
    test_gen_bssid_xlsx_interim_file,
    test_gen_bssid_xlsx_out_file,
    test_gen_bssid_file.parent,
]