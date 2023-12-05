# open_inwoner/generate_css.py
import json

design_tokens_path = "conf/fixtures/design-tokens.json"
css_output_path = "../../static/css/oip_-styles.css"

with open(design_tokens_path, "r") as file:
    design_tokens = json.load(file)


def generate_css():
    css = ":root {\n"

    for category in design_tokens:
        tokens = design_tokens[category]

        for token in tokens:
            css += f"  --{token}: {tokens[token]};\n"

    css += "}\n"

    with open(css_output_path, "w") as output_file:
        output_file.write(css)


generate_css()
