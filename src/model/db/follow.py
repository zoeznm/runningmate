import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "follows"
        indexes = (
            (("follower_id", "following_id"), True),
        )

    id = pw.CharField(max_length=36, primary_key=True)
    follower_id = pw.CharField(max_length=36, index=True)
    following_id = pw.CharField(max_length=36, index=True)
    created_at = pw.DateTimeField(index=True)
