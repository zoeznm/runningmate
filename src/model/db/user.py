import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")

class Model(base):
    class Meta:
        db_table = "user"

    id = pw.CharField(max_length=36, primary_key=True)
    username = pw.CharField(max_length=30, unique=True, null=True, index=True)
    email = pw.CharField(max_length=128, unique=True, null=True)
    friend_code = pw.CharField(max_length=16, unique=True, null=True, index=True)
    password_hash = pw.TextField(null=True)
    password = pw.CharField(max_length=200, null=True)
    display_name = pw.CharField(max_length=50, null=True)
    name = pw.CharField(max_length=50, default="")
    gender = pw.CharField(max_length=16, null=True, index=True)
    mobile = pw.CharField(max_length=20, default="")
    running_start_date = pw.DateField(null=True)
    profile_image = pw.TextField(null=True)
    onboarded = pw.BooleanField(default=False, index=True)
    is_public = pw.BooleanField(default=True, index=True)
    password_changed_at = pw.DateTimeField(null=True)
    password_failed_count = pw.IntegerField(default=0)
    password_locked_until = pw.DateTimeField(null=True)
    role = pw.CharField(max_length=16, default="user", index=True)
    created_at = pw.DateTimeField(null=True)
    created = pw.DateTimeField(index=True)
    updated = pw.DateTimeField()
