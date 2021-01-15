from typer.testing import CliRunner

from cli import app  # type: ignore # NoQA
from . import TEST_DEVICES

runner = CliRunner()


# class Switch:
#     def __init__(self) -> None:
#         self.data = None
#         self.get_data()

#     def __getattr__(self, key: str):
#         if hasattr(self, key):
#             return getattr(self, key)
#         elif self.data and self.data.get(key):
#             return self.data[key]
#         else:
#             raise AttributeError(f"{self.__name__} object has no Attribute {key}")

#     def get_data(self):
#         cache = Identifires()
#         self.data = cache.DevDB.search(self.Q.type == "switch")


# class TestShow:
# def __init__(self) -> None:
#     self.switch = Switch()

def test_do_bounce_interface():
    result = runner.invoke(app, ["do", "bounce-interface", TEST_DEVICES["switch"]["name"].lower(),
                           TEST_DEVICES["switch"]["test_port"], "-Y", "--debug"])
    assert result.exit_code == 0
    assert "Success command Queued." in result.stdout


def test_do_bounce_poe():
    result = runner.invoke(app, ["do", "bounce-poe", TEST_DEVICES["switch"]["name"].lower(),
                           TEST_DEVICES["switch"]["test_port"], "-Y", "--debug"])
    assert result.exit_code == 0
    assert "Success command Queued." in result.stdout
