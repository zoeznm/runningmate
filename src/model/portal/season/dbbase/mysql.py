import os

_SOURCE = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../../../portal/season/model/dbbase/mysql.py",
))

with open(_SOURCE, "r", encoding="utf-8") as _fp:
    exec(compile(_fp.read(), _SOURCE, "exec"), globals())
