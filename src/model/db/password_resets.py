import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "password_resets"

    id = pw.CharField(max_length=36, primary_key=True)
    user_id = pw.CharField(max_length=36, index=True)
    token = pw.CharField(max_length=64, unique=True, index=True)
    expires_at = pw.DateTimeField(index=True)
    used = pw.BooleanField(default=False, index=True)
    created_at = pw.DateTimeField(index=True)
