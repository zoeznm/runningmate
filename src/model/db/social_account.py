import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "social_account"
        indexes = (
            (("provider", "provider_user_id"), True),
        )

    id = pw.CharField(max_length=36, primary_key=True)
    user_id = pw.CharField(max_length=36, index=True)
    provider = pw.CharField(max_length=20, index=True)
    provider_user_id = pw.CharField(max_length=128)
    email = pw.CharField(max_length=128, null=True)
    name = pw.CharField(max_length=50, null=True)
    profile_image = pw.TextField(null=True)
    created_at = pw.DateTimeField(null=True)
    updated = pw.DateTimeField()
