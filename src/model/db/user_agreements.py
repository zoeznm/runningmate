import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "user_agreements"

    id = pw.CharField(max_length=36, primary_key=True)
    user_id = pw.CharField(max_length=36, index=True)
    terms_version = pw.CharField(max_length=10)
    privacy_version = pw.CharField(max_length=10)
    marketing_optin = pw.BooleanField(default=False)
    agreed_at = pw.DateTimeField(index=True)
