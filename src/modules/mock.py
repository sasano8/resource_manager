from ..base import Resource


class TrueResource(Resource):
    def create(self):
        return True, "a resource created(absolutely True)."

    def delete(self):
        return True, "a resource deleted(absolutely True)."

    def exists(self):
        return True, "a resource exists(absolutely True)."

    def absent(self):
        return True, "a resource absent(absolutely True)."


class FalseResource(Resource):
    def create(self):
        return False, "a resource cant created(absolutely False)."

    def delete(self):
        return False, "a resource cant deleted(absolutely False)."

    def exists(self):
        return False, "a resource not exists(absolutely False)."

    def absent(self):
        return False, "a resource not absent(absolutely False)."
