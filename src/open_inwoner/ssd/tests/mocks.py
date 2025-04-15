from pathlib import Path

FILES_DIR = Path(__file__).parent / "files"


def mock_uitkering_response_basic():
    path = FILES_DIR / "uitkering_response_basic.xml"
    return path.read_text()


def mock_jaaropgave_response():
    path = FILES_DIR / "jaaropgave_response.xml"
    return path.read_text()
