from pathlib import Path

from django.http import Http404, HttpResponse
from django.views import View

from lxml import etree

from open_inwoner.ssd.rendering import XSLT_DIR

TEST_FILES_DIR = Path(__file__).resolve().parent.parent / "tests/files"


def dummy(context, *args):
    print("yoo dummy", args)
    return f"dummy({', '.join(args)})"


user_functions = etree.FunctionNamespace("urn:custFunc")
# user_functions.prefix = "user"
user_functions["CalculateLoonZVW"] = dummy
user_functions["FormatDate"] = dummy
user_functions["FormatNumberD"] = dummy
user_functions["formatPeriode"] = dummy
user_functions["GetDate"] = dummy
user_functions["RemoveUnnecessaryCharacters"] = dummy

ext_dict = {
    ("urn:custFunc", "CalculateLoonZVW"): dummy,
    ("urn:custFunc", "FormatDate"): dummy,
    ("urn:custFunc", "FormatNumberD"): dummy,
    ("urn:custFunc", "formatPeriode"): dummy,
    ("urn:custFunc", "GetDate"): dummy,
    ("urn:custFunc", "RemoveUnnecessaryCharacters"): dummy,
}


class XSLTDevView(View):
    """
    quick view for hacking and developing the html output
    """

    examples = {
        "jaaropgave": (
            TEST_FILES_DIR / "jaaropgave-testresponse.xml",
            XSLT_DIR / "Jaaropgave/Response2018_patched.xslt",
        ),
        "uitkering": (
            TEST_FILES_DIR / "UitkeringsSpecificatieClient_v0500.xml",
            XSLT_DIR / "Uitkeringsspecificatie/Response.xslt",
        ),
    }

    def index_reponse(self, request):
        html = f"""<html><body><ul>{''.join(f'<li><a href="?example={e}">{e}</a></li>' for e in self.examples.keys())}</ul></body></html>"""
        return HttpResponse(html, content_type="text/html")

    def get(self, request, *args, **kwargs):
        example = request.GET.get("example")
        if not example in self.examples:
            return self.index_reponse(request)

        soap_path, xslt_path = self.examples[example]

        with open(soap_path, "rb") as f:
            soap_doc = etree.parse(f)

        with open(xslt_path, "rb") as f:
            xslt_root = etree.parse(f)

        transform = etree.XSLT(xslt_root, extensions=ext_dict)
        result = transform(soap_doc)
        for entry in transform.error_log:
            print(
                "message from line %s, col %s: %s"
                % (entry.line, entry.column, entry.message)
            )
            print("domain: %s (%d)" % (entry.domain_name, entry.domain))
            print("type: %s (%d)" % (entry.type_name, entry.type))
            print("level: %s (%d)" % (entry.level_name, entry.level))
            print("filename: %s" % entry.filename)

        output = etree.tostring(result, encoding="utf-8", xml_declaration=False)

        return HttpResponse(output, content_type="text/html")
