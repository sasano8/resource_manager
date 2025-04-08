import json

import networkx

from .files import TEMPLATE_GRAPH_HTML_FILE


def generate_sample_html(
    dag: networkx.DiGraph, html_template: str, replace: str = "{{ graph_json }}"
):
    data = generate_json(dag)
    dumped = json.dumps(data)
    generated_html = html_template.replace("{{ graph_json }}", dumped)
    return generated_html


def create_html(dag, output_path: str, html_template: str = None):
    if not html_template:
        with open(TEMPLATE_GRAPH_HTML_FILE) as f:
            html_template = f.read()

    with open(output_path, "w") as f:
        html = generate_sample_html(dag, html_template)
        f.write(html)


def generate_json(dag):
    data = networkx.readwrite.json_graph.node_link_data(dag, edges="edges")
    return data
