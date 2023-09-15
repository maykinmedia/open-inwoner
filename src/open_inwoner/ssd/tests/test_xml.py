from pathlib import Path
from unittest import TestCase

from ..xml import get_jaaropgaven, get_uitkeringen

FILES_DIR = Path(__file__).parent.resolve() / "files"

jaaropgave_path1 = FILES_DIR / "jaaropgave_response.xml"
jaaropgave_path2 = FILES_DIR / "jaaropgave_response_extra_spec.xml"
uitkering_path1 = FILES_DIR / "uitkering_response_basic.xml"
uitkering_path2 = FILES_DIR / "uitkering_response_extra_report.xml"
uitkering_path3 = FILES_DIR / "uitkering_response_extra_report2.xml"


class JaaropgaveTest(TestCase):
    pass
