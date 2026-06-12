import datetime


payload = {
    "success": True,
    "status": "ok",
    "service": "runningmate",
    "checked_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
}

wiz.response.status(200, **payload)
