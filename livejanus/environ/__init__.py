from os.path import isfile, join, dirname, abspath
from json import loads

root_path = abspath(join(dirname(__file__), "..", ".."))
new_environ = {}
with open(join(root_path, "environment.default.json")) as environment_default_file:
    environ = loads(environment_default_file.read())
if isfile(join(root_path, "environment.json")):
    with open(join(root_path, "environment.json")) as environment_file:
        new_environ = loads(environment_file.read())
        for key in new_environ:
            environ[key] = new_environ[key]

del new_environ
del root_path
