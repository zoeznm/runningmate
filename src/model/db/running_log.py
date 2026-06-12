import peewee as pw

orm = wiz.model("portal/season/orm")
base = orm.base("base")


class Model(base):
    class Meta:
        db_table = "running_logs"
        indexes = (
            (("user_id", "date"), False),
        )

    id = pw.CharField(max_length=36, primary_key=True)
    user_id = pw.CharField(max_length=36, index=True)
    date = pw.DateField(index=True)
    distance_km = pw.FloatField()
    avg_pace = pw.CharField(max_length=16, null=True)
    duration = pw.CharField(max_length=16, null=True)
    run_type = pw.CharField(max_length=32, null=True, index=True)
    start_time = pw.CharField(max_length=8, null=True)
    calories = pw.IntegerField(null=True)
    avg_heart_rate = pw.IntegerField(null=True)
    cadence = pw.IntegerField(null=True)
    elevation_gain = pw.FloatField(null=True)
    water_before_ml = pw.IntegerField(null=True)
    water_after_ml = pw.IntegerField(null=True)
    image_url = pw.TextField(null=True)
    journal = pw.TextField(null=True)
    playlist_name = pw.CharField(max_length=200, null=True)
    music_url = pw.TextField(null=True)
    top_tracks = pw.TextField(null=True)
    is_public = pw.BooleanField(default=True, index=True)
    raw_parsed_json = pw.TextField(null=True)
    created_at = pw.DateTimeField(null=True, index=True)
    updated_at = pw.DateTimeField(null=True, index=True)
