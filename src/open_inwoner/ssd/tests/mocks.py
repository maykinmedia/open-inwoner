from pathlib import Path

FILES_DIR = Path(__file__) / "files"


def mock_report(test_response: str) -> str:
    xml_response = str(FILES_DIR / test_response)
    with open(xml_response, "r") as file:
        res = file.read()
    return res
