from rctl.base2 import StepDataExtension


def apply_resource(from_file: str = None):
    step = StepDataExtension.from_file(from_file)
    step.apply()


def create_resource(from_file: str = None):
    step = StepDataExtension.from_file(from_file).override(state="created")
    step.apply()


def exists_resource(from_file: str = None):
    step = StepDataExtension.from_file(from_file).override(state="exists")
    step.apply()


def absent_resource(from_file: str = None):
    step = StepDataExtension.from_file(from_file).override(state="absent")
    step.apply()


def delete_resource(from_file: str = None):
    step = StepDataExtension.from_file(from_file).override(state="deleted")
    step.apply()


def recreate_resource(from_file: str = None):
    step = StepDataExtension.from_file(from_file).override(state="recreated")
    step.apply()


def apply_manifest(): ...
