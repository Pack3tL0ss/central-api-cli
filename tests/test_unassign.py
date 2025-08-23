import asyncio

import pytest
from typer.testing import CliRunner

from centralcli import cache
from centralcli.cli import app

from . import capture_logs, config, test_data

runner = CliRunner()


@pytest.fixture(scope="function")
def ensure_cache():
    if config.dev.mock_tests and "cencli_test_label1" not in cache.labels_by_name:
        asyncio.run(cache.update_db(cache.LabelDB, data={"id": 1106, "name": "cencli_test_label1", "devices": 0}, truncate=False))
    yield

    if config.dev.mock_tests and "cencli_test_label1" in cache.labels_by_name:
        doc_id = cache.labels_by_name["cencli_test_label1"].doc_id
        asyncio.run(cache.update_db(cache.LabelDB, doc_ids=[doc_id]))


def test_unassign_label(ensure_cache):
    """Relies on label created in test_add.test_add_label"""
    result = runner.invoke(
        app,
        [
            "unassign",
            "label",
            "cencli_test_label1",
            test_data["ap"]["name"],
            "-Y"
        ]
    )
    capture_logs(result, "test_unassign_label")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert test_data["ap"]["serial"].upper() in result.stdout
