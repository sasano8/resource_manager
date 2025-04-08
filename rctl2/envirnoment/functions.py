import json

import jinja2

Undefined = object()


class Functions:
    def __init__(self, store_env: dict, store_val: dict, store_secret: dict):
        self._store_env = store_env
        self._store_val = store_val
        self._store_secret = store_secret

    def env(self, key, default=Undefined):
        store = self._store_env
        if default is Undefined:
            value = store[key]
        else:
            value = store.get(key, default)

        return json.dumps(value)

    def val(self, key, default=Undefined):
        store = self._store_val
        if default is Undefined:
            return store[key]
        else:
            return store.get(key, default)

    def secret(self, key, default=Undefined):
        store = self._store_secret
        if default is Undefined:
            return store[key]
        else:
            return store.get(key, default)

    def to_dict(self):
        return {"env": self.env, "val": self.val, "secret": self.secret}


class Envirnoment:
    def __init__(self, _: jinja2.Environment, **functions):
        self._env = _
        self._functions = functions

    def filters(self):
        return self._env.filters.keys()

    def render(self, text) -> str:
        tpl = jinja2.Template(text)
        return tpl.render(**self._functions)

    def repl(self):
        import readline  # 履歴などを有効化する
        import traceback

        while True:
            text = input(">>>")
            if text:
                try:
                    output = self.render(text)
                    print(f"Output: {output}")
                except Exception as e:
                    print("An error occurred:")
                    traceback.print_exc()

    def dump_document(self, f):
        def _to_document(items):
            if isinstance(items, (list, set)):
                for item in items:
                    yield str(item)
            elif isinstance(items, dict):
                for k, v in items.items:
                    yield f"{k}: {v}"
            else:
                raise NotImplementedError(items)

        f.write("# Envirnoment" + "\n")

        f.write("## filters" + "\n")
        for line in _to_document(list(self.filters())):
            f.write(line + "\n")

        f.write("## functions" + "\n")
        for line in _to_document(list(self._functions.keys())):
            f.write(line + "\n")


def create_envirnoment(store_env: dict, store_val: dict, store_secret: dict):
    builtins = Functions(
        store_env=store_env, store_val=store_val, store_secret=store_secret
    )
    env = Envirnoment(jinja2.Environment(), **builtins.to_dict())
    return env
