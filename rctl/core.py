from rctl.base2 import StepDataExtension
from .scanner import scan_files
import os


def scan(from_file: str = None, from_dir: str = None):
    if from_dir:
        return scan_files(from_dir, include=["*.yml", "*.yaml"])

    if from_file:
        return [from_file]

    raise Exception()


def apply_resource(from_file: str = None, from_dir: str = None):
    for f in scan(from_file, from_dir):
        step = StepDataExtension.from_file(f)
        step.apply()


def create_resource(from_file: str = None, from_dir: str = None):
    for f in scan(from_file, from_dir):
        step = StepDataExtension.from_file(f).override(state="created")
        step.apply()


def exists_resource(from_file: str = None, from_dir: str = None):
    for f in scan(from_file, from_dir):
        step = StepDataExtension.from_file(f).override(state="exists")
        step.apply()


def absent_resource(from_file: str = None, from_dir: str = None):
    for f in scan(from_file, from_dir):
        step = StepDataExtension.from_file(f).override(state="absent")
        step.apply()


def delete_resource(from_file: str = None, from_dir: str = None):
    for f in scan(from_file, from_dir):
        step = StepDataExtension.from_file(f).override(state="deleted")
        step.apply()


def recreate_resource(from_file: str = None, from_dir: str = None):
    for f in scan(from_file, from_dir):
        step = StepDataExtension.from_file(f).override(state="recreated")
        step.apply()


def scan_resource(from_file: str = None, from_dir: str = "."):
    for f in scan(from_file, from_dir):
        print(f)


def apply_manifest(): ...
