import json
import networkx

from .parser import parser
from .files import TEMPLATE_GRAPH_HTML_FILE
from .transformer import MiniHCLTransformer


def parse(text):
    ps = parser()
    tree = ps.parse(text)
    data = MiniHCLTransformer().transform(tree)
    return data


# def generate_sample_html(
#     dag: networkx.DiGraph, html_template: str, replace: str = "{{ graph_json }}"
# ):
#     data = generate_json(dag)
#     dumped = json.dumps(data)
#     generated_html = html_template.replace("{{ graph_json }}", dumped)
#     return generated_html

# def create_html(dag, html_template: str = None, output_path="dag_viewer.html"):
#     if not html_template:
#       with open(TEMPLATE_GRAPH_HTML_FILE) as f:
#           html_template = f.read()

#     with open(output_path, "w") as f:
#         html = generate_sample_html(dag, html_template)
#         f.write(html)

# def generate_json(dag):
#     data = networkx.readwrite.json_graph.node_link_data(dag, edges="edges")
#     return data

Undefined = object()


class Node(dict):
    @classmethod
    def create(cls, kind, type, attr, value=Undefined, body=Undefined):
        data = {"kind": kind, "type": type, "attr": attr, "value": value, "body": body}
        if value is Undefined:
            data.pop("value")

        if body is Undefined:
            data.pop("body")

        return cls(**data)

    def get_kind(self):
        return self["kind"]

    def get_type(self):
        return self["type"]

    def get_attr(self):
        return self["attr"]

    def is_group(self):
        return self["kind"] == "group"

    def get_value(self):
        if self["kind"] == "group":
            raise RuntimeError()
        return self["value"]

    def get_body(self):
        if self["kind"] != "group":
            raise RuntimeError()
        return self["body"]


def _flatten_groups(key, node):
    new_node = Node.create(**node)
    if not new_node.get_kind().lower() == "group":
        yield key, new_node
        return

    type = new_node.get_type().lower()
    if type == "root":
        for child_key, child_node in new_node.get_body().items():
            for nest_key, nest_node in _flatten_groups(child_key, child_node):
                yield nest_key, nest_node
    elif type == "parallel":
        prev = key + "_start"
        yield prev, {"kind": "resource", "type": "null", "attr": {}, "value": {}}
        end = {
            "kind": "resource",
            "type": "null",
            "attr": {"depends_on_system": []},
            "value": {},
        }
        if len(new_node.get_body()):
            for child_key, child_node in new_node.get_body().items():
                end["attr"]["depends_on_system"].append(child_key)
                for nest_key, nest_node in _flatten_groups(child_key, child_node):
                    yield nest_key, nest_node
        else:
            end["attr"]["depends_on_system"].append(prev)
        yield key, end
    elif type == "sequential":
        prev = key + "_start"
        yield prev, {"kind": "resource", "type": "null", "attr": {}, "value": {}}
        end = {
            "kind": "resource",
            "type": "null",
            "attr": {"depends_on_system": []},
            "value": {},
        }
        for child_key, child_node in new_node.get_body().items():
            depends_on_system = child_node["attr"].setdefault("depends_on_system", [])
            depends_on_system.append(prev)
            prev = child_key
            for nest_key, nest_node in _flatten_groups(child_key, child_node):
                yield nest_key, nest_node
        end["attr"]["depends_on_system"].append(prev)
        yield key, end
    else:
        raise Exception()


def flatten_groups(nodes):
    root = Node.create(kind="group", type="root", attr={}, body=nodes)
    return {k: dict(v) for k, v in _flatten_groups(None, root)}


def make_dag(resolved_nodes, depends_on: bool = True, depends_on_system: bool = True):
    """
    ノードから depends_on, depends_on_system を抽出し dag を構築する。

    抽出パターン１: タスク実行用のDAGを構築する
      depends_on=True
      depends_on_system=True

    抽出パターン２ 可視化用のDAGを構築する（すべての依存性を表現するとグラフが煩雑になるので、綺麗に表現できる粒度の依存性のみ抽出）
      depends_on=False
      depends_on_system=True
    """

    dag = networkx.DiGraph()

    for key, node in resolved_nodes.items():
        if node["kind"] != "resource":
            continue

        dag.add_node(key)

        if depends_on:
            for depend_name in node["attr"].get("depends_on", []):
                dag.add_edge(depend_name, key)

        if depends_on_system:
            for depend_name in node["attr"].get("depends_on_system", []):
                dag.add_edge(depend_name, key)

    assert networkx.is_directed_acyclic_graph(dag)
    return dag
