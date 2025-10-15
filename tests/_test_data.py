import json
from pathlib import Path
from typing import Any, Callable

import yaml

from centralcli import common, config
from centralcli.exceptions import ImportException


def get_test_data():
    test_file = Path(__file__).parent / 'test_data.yaml'
    if not test_file.is_file():
        raise FileNotFoundError(f"Required test file {test_file} is missing.  Refer to {test_file.name}.example")  # pragma: no cover
    return config.get_file_data(test_file)


def setup_cert_file(cert_path: str) -> Path:
    test_cert_file = config.cache_dir / "test_runner_cert.pem"
    file = Path(cert_path)
    test_cert_file.write_text(file.read_text())

    return test_cert_file

def _get_dump_func(sfx: str) -> Callable:
    dump_func = {
        "json": json.dumps,
        "yaml": yaml.safe_dump,
        "csv": lambda data: "\n".join([",".join(k for k in data[0].keys()), *[",".join(v for v in inner.values()) for inner in data]])
    }
    return dump_func.get(sfx, json.dumps)

def setup_batch_import_file(test_data: dict | str, import_type: str = "sites") -> Path:
    data = test_data["batch"]
    keys = import_type.split(":")
    sfx = "json" if len(keys) < 2 else keys[1]
    import_type = keys[0]
    for k in keys:
        data = data[k]

    if isinstance(data, str):  # pragma: no cover
        seed_file = Path(data)
        data = common._get_import_file(seed_file, import_type=import_type)
    else:
        data = data

    test_batch_file = config.cache_dir / f"test_runner_{import_type}.{sfx}"
    res = test_batch_file.write_text(
        _get_dump_func(sfx)(data)
    )
    if not res:
        raise ImportException("Batch import file creation from test_data returned 0 chars written")  # pragma: no cover

    return test_batch_file

def _create_invalid_var_file(file: str) -> Path:
    var_file = Path(file)
    test_var_file = config.cache_dir / f"test_runner_invalid_variables{var_file.suffix}"
    test_var_file.write_text("".join([line for line in var_file.read_text().splitlines(keepends=True) if "_sys_lan_mac" not in line]))
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


test_data: dict[str, Any] = get_test_data()
test_device_file: Path = setup_batch_import_file(test_data=test_data, import_type="devices")
test_group_file: Path = setup_batch_import_file(test_data=test_data, import_type="groups_by_name")
test_sub_file_yaml: Path = setup_batch_import_file(test_data=test_data, import_type="subscriptions:yaml")
test_sub_file_csv: Path = setup_batch_import_file(test_data=test_data, import_type="subscriptions:csv")
test_rename_aps_file: Path = setup_batch_import_file(test_data=test_data, import_type="rename_aps")
test_update_aps_file: Path = setup_batch_import_file(test_data=test_data, import_type="update_aps")
test_verify_file: Path = setup_batch_import_file(test_data=test_data, import_type="verify")
test_label_file: Path = setup_batch_import_file(test_data=test_data, import_type="labels")
test_mpsk_file: Path = setup_batch_import_file(test_data=test_data, import_type="mpsk")
test_site_file: Path = setup_batch_import_file(test_data=test_data)
test_cert_file: Path = setup_cert_file(cert_path=test_data["certificate"])
test_invalid_var_file = _create_invalid_var_file(test_data["template"]["variable_file"])
test_deploy_file = setup_deploy_file(group_file=test_group_file, site_file=test_site_file, label_file=test_label_file, device_file=test_device_file)
test_j2_file = setup_j2_file()
gw_group_config_file = config.cache_dir / "test_runner_gw_grp_config"

test_files = [
    test_device_file,
    test_group_file,
    test_sub_file_csv,
    test_sub_file_yaml,
    test_rename_aps_file,
    test_verify_file,
    test_site_file,
    test_cert_file,
    test_mpsk_file,
    test_invalid_var_file,
    test_label_file,
    test_sub_file_yaml,
    test_sub_file_csv,
    test_deploy_file,
    test_j2_file,
    test_update_aps_file,
]