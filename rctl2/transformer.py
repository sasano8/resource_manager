from lark import Transformer


class MiniHCLTransformer(Transformer):
    def start(self, items):
        return dict(items)

    def atom(self, items):
        return items[0]

    def statement(self, items):
        return items[0]

    def assignment(self, items):
        if not isinstance(items[0], dict):
            items.insert(0, {})

        if len(items) == 5:
            attr, name, type, _, value = items
            return (
                name,
                {
                    "kind": type[0].lower(),
                    "type": type[1].lower(),
                    "attr": attr,
                    "value": value,
                },
            )
        elif len(items) == 4:
            attr, name, _, value = items
            return (
                name,
                {"kind": "variable", "type": "default", "attr": attr, "value": value},
            )
        else:
            raise Exception(items)

    def attr(self, items):
        return items[0] if items else {}

    def attr_body(self, items):
        return dict(items)

    def group_block(self, items):
        if len(items) == 4:
            attr, identifier, group_type, body = items
        else:
            identifier, group_type, body = items
            attr = {}

        return (
            identifier,
            {"kind": "group", "type": group_type, "attr": attr, "body": dict(body)},
        )

    def group_type(self, items):
        return str(items[0]) if items else ""

    def block(self, items):
        return items

    def type_expr(self, items):
        if len(items) == 1:
            kind = items[0]
            type = "default"
        elif len(items) == 2:
            kind, type = items
        else:
            raise Exception(items)
        return (str(kind), type)

    def object(self, items):
        return dict(items)

    def pair(self, items):
        if len(items) == 2:
            key, value = items
        elif len(items) == 3:
            key, _, value = items
        else:
            raise Exception(items)

        return (str(key), value)

    def pair_value(self, items):
        return items[0]

    def array(self, items):
        return list(items)

    def identifier(self, items):
        return str(items[0])

    def STRING(self, s):
        return s.value.strip('"')

    def SIGNED_NUMBER(self, n):
        return float(n) if "." in n or "e" in n.lower() else int(n)
