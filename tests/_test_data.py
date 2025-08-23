import json
from pathlib import Path
from typing import Any

from centralcli import config
from centralcli.exceptions import ImportException


def get_test_data():
    test_file = Path(__file__).parent / 'test_data.yaml'
    if not test_file.is_file():
        raise FileNotFoundError(f"Required test file {test_file} is missing.  Refer to {test_file.name}.example")  # pragma: no cover
    return config.get_file_data(test_file)


def setup_batch_import_file(test_data: dict | str | Path, import_type: str = "sites") -> Path:
    if isinstance(test_data, (str, Path)):
        return test_data if isinstance(test_data, Path) else Path(test_data)  # pragma: no cover

    test_batch_file = config.cache_dir / f"test_runner_{import_type}.json"
    res = test_batch_file.write_text(
        json.dumps(test_data["batch"][import_type])
    )
    if not res:
        raise ImportException("Batch import file creation from test_data returned 0 chars written")  # pragma: no cover
    return test_batch_file


test_data: dict[str, Any] = get_test_data()
test_device_file: Path = setup_batch_import_file(test_data=test_data, import_type="devices")
test_group_file: Path = setup_batch_import_file(test_data=test_data, import_type="groups_by_name")
test_site_file: Path = setup_batch_import_file(test_data=test_data)
gw_group_config_file = config.cache_dir / "test_runner_gw_grp_config"