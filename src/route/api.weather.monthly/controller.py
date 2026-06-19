import datetime
import ipaddress
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_SERVICE_KEY = "BOSIHO7gl1tSe4mkEEfU0TErgpn97yFSS8q7aBAJ/WkDdRB4F450fg8Sfts8jfBjIxx69ea/cxlSpFzL77XWMQ=="
ENV_FILE = os.environ.get("RUNNINGMATE_WEATHER_ENV_FILE") or os.environ.get("RUNNINGMATE_OPENAI_ENV_FILE", "/opt/app/config/openai.env")
SERVICE_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService"
VILAGE_SERVICE_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
IP_LOCATION_URL = "https://ipapi.co/{ip}/json/"
KST_OFFSET = datetime.timedelta(hours=9)
CACHE_TTL_SECONDS = 30 * 60
IP_LOCATION_CACHE_TTL_SECONDS = 12 * 60 * 60
CACHE_DIR = os.environ.get("RUNNINGMATE_WEATHER_CACHE_DIR", "/opt/app/data/weather_cache")
SNAPSHOT_FILE = os.environ.get("RUNNINGMATE_WEATHER_SNAPSHOT_FILE", "/opt/app/data/weather_snapshots.json")
DEFAULT_LAND_REG_ID = "11B00000"
DEFAULT_TEMP_REG_ID = "11B10101"
DEFAULT_LAT = 37.5665
DEFAULT_LON = 126.9780
KOREA_MIN_LAT = 32.0
KOREA_MAX_LAT = 39.5
KOREA_MIN_LON = 124.0
KOREA_MAX_LON = 132.0
SHORT_BASE_HOURS = (23, 20, 17, 14, 11, 8, 5, 2)
SHORT_CATEGORIES = {"TMP", "TMN", "TMX", "SKY", "PTY", "POP", "REH", "WSD"}
SKY_LABELS = {
    "1": "맑음",
    "3": "구름많음",
    "4": "흐림",
}
PTY_LABELS = {
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "4": "소나기",
    "5": "빗방울",
    "6": "빗방울/눈날림",
    "7": "눈날림",
}
OPEN_METEO_WEATHER_CODES = {
    0: ("맑음", "sunny"),
    1: ("대체로 맑음", "sunny"),
    2: ("구름 조금", "cloud"),
    3: ("흐림", "cloud"),
    45: ("안개", "cloud"),
    48: ("안개", "cloud"),
    51: ("이슬비", "rain"),
    53: ("이슬비", "rain"),
    55: ("이슬비", "rain"),
    56: ("어는 이슬비", "mixed"),
    57: ("어는 이슬비", "mixed"),
    61: ("비", "rain"),
    63: ("비", "rain"),
    65: ("강한 비", "rain"),
    66: ("어는 비", "mixed"),
    67: ("어는 비", "mixed"),
    71: ("눈", "snow"),
    73: ("눈", "snow"),
    75: ("강한 눈", "snow"),
    77: ("눈", "snow"),
    80: ("소나기", "rain"),
    81: ("소나기", "rain"),
    82: ("강한 소나기", "rain"),
    85: ("눈 소나기", "snow"),
    86: ("강한 눈 소나기", "snow"),
    95: ("뇌우", "rain"),
    96: ("우박 동반 뇌우", "mixed"),
    99: ("우박 동반 뇌우", "mixed"),
}
WEATHER_LOCATIONS = [
    {"name": "서울", "lat": 37.5665, "lon": 126.9780, "landRegId": "11B00000", "tempRegId": "11B10101"},
    {"name": "인천", "lat": 37.4563, "lon": 126.7052, "landRegId": "11B00000", "tempRegId": "11B20201"},
    {"name": "수원", "lat": 37.2636, "lon": 127.0286, "landRegId": "11B00000", "tempRegId": "11B20601"},
    {"name": "춘천", "lat": 37.8813, "lon": 127.7298, "landRegId": "11D10000", "tempRegId": "11D10301"},
    {"name": "원주", "lat": 37.3422, "lon": 127.9202, "landRegId": "11D10000", "tempRegId": "11D10401"},
    {"name": "강릉", "lat": 37.7519, "lon": 128.8761, "landRegId": "11D20000", "tempRegId": "11D20501"},
    {"name": "청주", "lat": 36.6424, "lon": 127.4890, "landRegId": "11C10000", "tempRegId": "11C10301"},
    {"name": "충주", "lat": 36.9910, "lon": 127.9259, "landRegId": "11C10000", "tempRegId": "11C10101"},
    {"name": "대전", "lat": 36.3504, "lon": 127.3845, "landRegId": "11C20000", "tempRegId": "11C20401"},
    {"name": "세종", "lat": 36.4801, "lon": 127.2890, "landRegId": "11C20000", "tempRegId": "11C20404"},
    {"name": "전주", "lat": 35.8242, "lon": 127.1480, "landRegId": "11F10000", "tempRegId": "11F10201"},
    {"name": "광주", "lat": 35.1595, "lon": 126.8526, "landRegId": "11F20000", "tempRegId": "11F20501"},
    {"name": "목포", "lat": 34.8118, "lon": 126.3922, "landRegId": "11F20000", "tempRegId": "21F20801"},
    {"name": "여수", "lat": 34.7604, "lon": 127.6622, "landRegId": "11F20000", "tempRegId": "11F20401"},
    {"name": "대구", "lat": 35.8714, "lon": 128.6014, "landRegId": "11H10000", "tempRegId": "11H10701"},
    {"name": "안동", "lat": 36.5684, "lon": 128.7294, "landRegId": "11H10000", "tempRegId": "11H10501"},
    {"name": "포항", "lat": 36.0190, "lon": 129.3435, "landRegId": "11H10000", "tempRegId": "11H10201"},
    {"name": "부산", "lat": 35.1796, "lon": 129.0756, "landRegId": "11H20000", "tempRegId": "11H20201"},
    {"name": "울산", "lat": 35.5384, "lon": 129.3114, "landRegId": "11H20000", "tempRegId": "11H20101"},
    {"name": "창원", "lat": 35.2280, "lon": 128.6811, "landRegId": "11H20000", "tempRegId": "11H20301"},
    {"name": "진주", "lat": 35.1800, "lon": 128.1076, "landRegId": "11H20000", "tempRegId": "11H20701"},
    {"name": "제주", "lat": 33.4996, "lon": 126.5312, "landRegId": "11G00000", "tempRegId": "11G00201"},
    {"name": "서귀포", "lat": 33.2541, "lon": 126.5601, "landRegId": "11G00000", "tempRegId": "11G00401"},
]


def _load_env_file():
    if not ENV_FILE or not os.path.exists(ENV_FILE):
        return

    try:
        with open(ENV_FILE, "r", encoding="utf-8") as fp:
            for line in fp:
                key, _, value = line.strip().partition("=")
                if key and value and key not in os.environ:
                    os.environ[key] = value.strip().strip('"').strip("'")
    except Exception:
        return


def _now_kst():
    return datetime.datetime.utcnow() + KST_OFFSET


def _lat_lon_to_grid(lat, lon):
    re_km = 6371.00877
    grid_km = 5.0
    slat1 = 30.0
    slat2 = 60.0
    olon = 126.0
    olat = 38.0
    xo = 43.0
    yo = 136.0
    degrad = math.pi / 180.0

    re_grid = re_km / grid_km
    slat1_rad = slat1 * degrad
    slat2_rad = slat2 * degrad
    olon_rad = olon * degrad
    olat_rad = olat * degrad

    sn = math.tan(math.pi * 0.25 + slat2_rad * 0.5) / math.tan(math.pi * 0.25 + slat1_rad * 0.5)
    sn = math.log(math.cos(slat1_rad) / math.cos(slat2_rad)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1_rad * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1_rad) / sn
    ro = math.tan(math.pi * 0.25 + olat_rad * 0.5)
    ro = re_grid * sf / math.pow(ro, sn)

    ra = math.tan(math.pi * 0.25 + lat * degrad * 0.5)
    ra = re_grid * sf / math.pow(ra, sn)
    theta = lon * degrad - olon_rad
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    return {
        "nx": int(ra * math.sin(theta) + xo + 0.5),
        "ny": int(ro - ra * math.cos(theta) + yo + 0.5),
    }


def _year_month():
    value = str(wiz.request.query("year_month", "") or "").strip()
    if re.match(r"^\d{4}-\d{2}$", value):
        return value
    return _now_kst().strftime("%Y-%m")


def _query_or_env(query_name, env_name, default):
    return str(wiz.request.query(query_name, "") or os.environ.get(env_name, "") or default).strip()


def _truthy_query(name):
    return str(wiz.request.query(name, "") or "").strip().lower() in ("1", "true", "yes", "y")


def _service_key():
    return str(os.environ.get("RUNNINGMATE_WEATHER_SERVICE_KEY") or DEFAULT_SERVICE_KEY).strip()


def _float_query(*names):
    for name in names:
        raw = str(wiz.request.query(name, "") or "").strip()
        if not raw:
            continue
        try:
            value = float(raw)
            if value == value:
                return value
        except Exception:
            continue
    return None


def _distance_km(lat1, lon1, lat2, lon2):
    lat_km = (lat1 - lat2) * 111.0
    lon_km = (lon1 - lon2) * 88.8
    return (lat_km * lat_km + lon_km * lon_km) ** 0.5


def _nearest_weather_location(lat, lon, source="browser"):
    if lat is None or lon is None:
        return None
    if not (KOREA_MIN_LAT <= lat <= KOREA_MAX_LAT and KOREA_MIN_LON <= lon <= KOREA_MAX_LON):
        return None

    nearest = min(
        WEATHER_LOCATIONS,
        key=lambda item: _distance_km(lat, lon, item["lat"], item["lon"])
    )
    return {
        "name": nearest["name"],
        "landRegId": nearest["landRegId"],
        "tempRegId": nearest["tempRegId"],
        "lat": lat,
        "lon": lon,
        **_lat_lon_to_grid(lat, lon),
        "source": source,
        "distanceKm": round(_distance_km(lat, lon, nearest["lat"], nearest["lon"]), 1),
    }


def _public_request_ip():
    try:
        request = wiz.server.package.flask.request
        candidates = []
        for header in ("CF-Connecting-IP", "X-Forwarded-For", "X-Real-IP"):
            value = str(request.headers.get(header) or "").strip()
            if value:
                candidates.extend(part.strip() for part in value.split(","))
        if getattr(request, "remote_addr", None):
            candidates.append(str(request.remote_addr).strip())

        for value in candidates:
            try:
                ip = ipaddress.ip_address(value)
            except Exception:
                continue
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local or ip.is_multicast:
                continue
            return str(ip)
    except Exception:
        return None
    return None


def _ip_location():
    ip = _public_request_ip()
    if not ip:
        return None

    cache_key = f"ip_location_{ip}"
    cached = _read_cache(cache_key, IP_LOCATION_CACHE_TTL_SECONDS)
    if cached:
        return cached

    try:
        request = urllib.request.Request(
            IP_LOCATION_URL.format(ip=urllib.parse.quote(ip, safe="")),
            headers={"User-Agent": "runningmate-weather/1.0"},
        )
        with urllib.request.urlopen(request, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception:
        return None

    lat = _to_float(payload.get("latitude") if isinstance(payload, dict) else None)
    lon = _to_float(payload.get("longitude") if isinstance(payload, dict) else None)
    if lat is None or lon is None:
        return None

    location = {
        "ip": ip,
        "lat": lat,
        "lon": lon,
        "city": _clean_text(payload.get("city")) if isinstance(payload, dict) else "",
        "region": _clean_text(payload.get("region")) if isinstance(payload, dict) else "",
        "country": _clean_text(payload.get("country")) if isinstance(payload, dict) else "",
    }
    _write_cache(cache_key, location)
    return location


def _weather_location():
    lat = _float_query("lat", "latitude")
    lon = _float_query("lon", "lng", "longitude")
    requested_source = str(wiz.request.query("location_source", "") or "").strip().lower()
    requested_source = "ip" if requested_source == "ip" else "browser"
    location = _nearest_weather_location(lat, lon, requested_source)
    if location:
        return location

    ip_location = _ip_location()
    if ip_location:
        location = _nearest_weather_location(ip_location["lat"], ip_location["lon"], "ip")
        if location:
            location["city"] = ip_location.get("city", "")
            location["region"] = ip_location.get("region", "")
            return location

    if _truthy_query("require_location"):
        return None

    name = _query_or_env("location", "RUNNINGMATE_WEATHER_LOCATION", "서울") or "서울"
    default_location = next((item for item in WEATHER_LOCATIONS if item["name"] == name), WEATHER_LOCATIONS[0])
    grid = _lat_lon_to_grid(default_location.get("lat", DEFAULT_LAT), default_location.get("lon", DEFAULT_LON))
    return {
        "name": name,
        "landRegId": _query_or_env("land_reg_id", "RUNNINGMATE_WEATHER_LAND_REG_ID", DEFAULT_LAND_REG_ID) or DEFAULT_LAND_REG_ID,
        "tempRegId": _query_or_env("temp_reg_id", "RUNNINGMATE_WEATHER_TEMP_REG_ID", DEFAULT_TEMP_REG_ID) or DEFAULT_TEMP_REG_ID,
        "lat": default_location.get("lat", DEFAULT_LAT),
        "lon": default_location.get("lon", DEFAULT_LON),
        **grid,
        "source": "default",
    }


def _short_base_candidates(now=None):
    anchor = (now or _now_kst()) - datetime.timedelta(minutes=45)
    candidates = []
    for day_offset in range(0, 3):
        day = anchor.date() - datetime.timedelta(days=day_offset)
        for hour in SHORT_BASE_HOURS:
            base_dt = datetime.datetime.combine(day, datetime.time(hour, 0))
            if base_dt <= anchor:
                candidates.append(base_dt)

    candidates.sort(reverse=True)
    return [(item.strftime("%Y%m%d"), item.strftime("%H00")) for item in candidates[:8]]


def _tmfc_candidates(now=None):
    anchor = (now or _now_kst()) - datetime.timedelta(hours=1)
    candidates = []
    for day_offset in range(0, 5):
        day = anchor.date() - datetime.timedelta(days=day_offset)
        for hour in (18, 6):
            base_dt = datetime.datetime.combine(day, datetime.time(hour, 0))
            if base_dt <= anchor:
                candidates.append(base_dt)

    candidates.sort(reverse=True)
    return [item.strftime("%Y%m%d%H00") for item in candidates[:8]]


def _cache_path(cache_key):
    safe_key = re.sub(r"[^A-Za-z0-9_.-]", "_", cache_key)
    return os.path.join(CACHE_DIR, safe_key + ".json")


def _read_cache(cache_key, max_age=None):
    path = _cache_path(cache_key)
    if not os.path.exists(path):
        return None
    if max_age is not None and time.time() - os.path.getmtime(path) > max_age:
        return None

    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return None


def _write_cache(cache_key, payload):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(_cache_path(cache_key), "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False)
    except Exception:
        return


def _current_user_id():
    try:
        session = wiz.model("portal/season/session").use()
        return _clean_text(session.get("id"))
    except Exception:
        return ""


def _read_snapshot_store():
    try:
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as fp:
            payload = json.load(fp)
    except Exception:
        return {"version": 1, "users": {}}

    if not isinstance(payload, dict):
        return {"version": 1, "users": {}}
    users = payload.get("users")
    if not isinstance(users, dict):
        users = {}
    return {"version": 1, "users": users}


def _write_snapshot_store(payload):
    try:
        os.makedirs(os.path.dirname(SNAPSHOT_FILE), exist_ok=True)
        tmp_path = SNAPSHOT_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False)
        os.replace(tmp_path, SNAPSHOT_FILE)
    except Exception:
        return False
    return True


def _snapshot_location(location):
    source = location if isinstance(location, dict) else {}
    return {
        "name": _clean_text(source.get("name")),
        "source": _clean_text(source.get("source")),
        "lat": source.get("lat"),
        "lon": source.get("lon"),
        "distanceKm": source.get("distanceKm"),
    }


def _annotate_weather_day(summary, location, base=None, stored=False, captured_at=None):
    row = dict(summary) if isinstance(summary, dict) else {}
    loc = _snapshot_location(location)
    if loc["name"]:
        row["locationName"] = loc["name"]
    if loc["source"]:
        row["locationSource"] = loc["source"]
    if loc["lat"] is not None:
        row["locationLat"] = loc["lat"]
    if loc["lon"] is not None:
        row["locationLon"] = loc["lon"]
    if loc["distanceKm"] is not None:
        row["locationDistanceKm"] = loc["distanceKm"]
    if base:
        row["base"] = base
    if stored:
        row["stored"] = True
    if captured_at:
        row["capturedAt"] = captured_at
    return row


def _annotate_weather_days(days, location, base=None):
    return {
        date_key: _annotate_weather_day(summary, location, base, stored=False)
        for date_key, summary in sorted((days or {}).items())
    }


def _save_weather_snapshots(user_id, days, location, base=None):
    if not user_id or not isinstance(days, dict):
        return

    today_key = _now_kst().strftime("%Y-%m-%d")
    captured_at = _now_kst().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    rows = {
        date_key: _annotate_weather_day(summary, location, base, stored=True, captured_at=captured_at)
        for date_key, summary in days.items()
        if isinstance(date_key, str) and date_key <= today_key
    }
    if not rows:
        return

    store = _read_snapshot_store()
    users = store.setdefault("users", {})
    user_days = users.setdefault(user_id, {})
    if not isinstance(user_days, dict):
        user_days = {}
        users[user_id] = user_days
    user_days.update(rows)

    sorted_keys = sorted(user_days.keys())
    for date_key in sorted_keys[:-730]:
        user_days.pop(date_key, None)
    _write_snapshot_store(store)


def _merge_weather_snapshots(user_id, days, year_month):
    merged = dict(days or {})
    if not user_id:
        return merged

    store = _read_snapshot_store()
    user_days = store.get("users", {}).get(user_id, {})
    if not isinstance(user_days, dict):
        return merged

    prefix = year_month + "-"
    for date_key, summary in sorted(user_days.items()):
        if isinstance(date_key, str) and date_key.startswith(prefix) and date_key not in merged:
            merged[date_key] = summary
    return merged


def _snapshot_response(user_id, year_month, message="저장된 날씨 기록입니다."):
    days = _merge_weather_snapshots(user_id, {}, year_month)
    filtered = _filter_days(days, year_month)
    if not filtered:
        return None
    return {
        "success": True,
        "data": {
            "year_month": year_month,
            "location": {},
            "base": {"message": message},
            "coverage": _coverage_from_days(filtered),
            "days": filtered,
        },
    }


def _is_permission_error(result_code, result_message):
    text = f"{result_code} {result_message}".upper()
    if str(result_code) in ("20", "22", "30", "31", "32", "33"):
        return True
    return any(word in text for word in ("SERVICE_KEY", "AUTH", "DENIED", "FORBIDDEN", "UNREGISTERED"))


def _items_from_payload(payload):
    response = payload.get("response") if isinstance(payload, dict) else {}
    header = response.get("header") if isinstance(response, dict) else {}
    result_code = str(header.get("resultCode") or "")
    result_message = str(header.get("resultMsg") or header.get("resultMessage") or "")
    if result_code and result_code != "00":
        if _is_permission_error(result_code, result_message):
            raise PermissionError(result_message or result_code)
        raise RuntimeError(result_message or result_code)

    body = response.get("body") if isinstance(response, dict) else {}
    items = body.get("items") if isinstance(body, dict) else {}
    rows = items.get("item") if isinstance(items, dict) else []
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list):
        rows = []
    return [row for row in rows if isinstance(row, dict)]


def _fetch_mid(endpoint, service_key, reg_id, tmfc):
    cache_key = f"mid_{endpoint}_{reg_id}_{tmfc}"
    cached = _read_cache(cache_key, CACHE_TTL_SECONDS)
    if cached:
        return cached, True

    params = urllib.parse.urlencode({
        "serviceKey": service_key,
        "pageNo": 1,
        "numOfRows": 10,
        "dataType": "JSON",
        "regId": reg_id,
        "tmFc": tmfc,
    })
    request = urllib.request.Request(
        f"{SERVICE_URL}/{endpoint}?{params}",
        headers={"User-Agent": "runningmate-weather/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise PermissionError(f"WEATHER_API_{exc.code}")
        raise

    try:
        payload = json.loads(raw)
    except Exception:
        if _is_permission_error("", raw):
            raise PermissionError("WEATHER_API_PERMISSION")
        raise RuntimeError("WEATHER_API_INVALID_RESPONSE")

    if not _items_from_payload(payload):
        raise RuntimeError("NO_WEATHER_ITEMS")

    _write_cache(cache_key, payload)
    return payload, False


def _fetch_village(service_key, nx, ny, base_date, base_time):
    cache_key = f"village_getVilageFcst_{nx}_{ny}_{base_date}_{base_time}"
    cached = _read_cache(cache_key, CACHE_TTL_SECONDS)
    if cached:
        return cached, True

    params = urllib.parse.urlencode({
        "serviceKey": service_key,
        "pageNo": 1,
        "numOfRows": 2000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    })
    request = urllib.request.Request(
        f"{VILAGE_SERVICE_URL}/getVilageFcst?{params}",
        headers={"User-Agent": "runningmate-weather/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise PermissionError(f"WEATHER_API_{exc.code}")
        raise

    try:
        payload = json.loads(raw)
    except Exception:
        if _is_permission_error("", raw):
            raise PermissionError("WEATHER_API_PERMISSION")
        raise RuntimeError("WEATHER_API_INVALID_RESPONSE")

    if not _items_from_payload(payload):
        raise RuntimeError("NO_WEATHER_ITEMS")

    _write_cache(cache_key, payload)
    return payload, False


def _fetch_open_meteo(lat, lon):
    lat_key = f"{float(lat):.3f}"
    lon_key = f"{float(lon):.3f}"
    cache_key = f"openmeteo_{lat_key}_{lon_key}"
    cached = _read_cache(cache_key, CACHE_TTL_SECONDS)
    if cached:
        return cached, True

    params = urllib.parse.urlencode({
        "latitude": f"{float(lat):.5f}",
        "longitude": f"{float(lon):.5f}",
        "timezone": "Asia/Seoul",
        "forecast_days": 16,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
        ]),
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "weather_code",
            "wind_speed_10m",
        ]),
        "wind_speed_unit": "ms",
    })
    request = urllib.request.Request(
        f"{OPEN_METEO_URL}?{params}",
        headers={"User-Agent": "runningmate-weather/1.0"},
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))

    if not isinstance(payload, dict) or "daily" not in payload:
        raise RuntimeError("OPEN_METEO_INVALID_RESPONSE")

    _write_cache(cache_key, payload)
    return payload, False


def _open_meteo_payload(lat, lon):
    payload, from_cache = _fetch_open_meteo(lat, lon)
    now = _now_kst()
    return payload, {
        "date": now.strftime("%Y%m%d"),
        "time": now.strftime("%H00"),
        "source": "open-meteo",
        "from_cache": from_cache,
        "stale": False,
    }


def _merge_open_meteo_days(all_days, location, base=None, prefer_base=False):
    open_payload, open_base = _open_meteo_payload(location["lat"], location["lon"])
    for date_key, summary in _build_open_meteo_days(open_payload).items():
        all_days.setdefault(date_key, summary)
    if base is None or prefer_base:
        return open_base
    base["open_meteo"] = open_base
    return base


def _short_forecast_payload(service_key, nx, ny):
    stale_item = None
    errors = []

    for base_date, base_time in _short_base_candidates():
        cache_key = f"village_getVilageFcst_{nx}_{ny}_{base_date}_{base_time}"
        cached = _read_cache(cache_key)
        if cached and stale_item is None:
            stale_item = (base_date, base_time, cached)

        try:
            payload, from_cache = _fetch_village(service_key, nx, ny, base_date, base_time)
            return payload, {
                "date": base_date,
                "time": base_time,
                "source": "short",
                "from_cache": from_cache,
                "stale": False,
            }
        except PermissionError:
            raise
        except Exception as exc:
            errors.append(f"{base_date}{base_time}:{exc}")

    if stale_item:
        base_date, base_time, payload = stale_item
        return payload, {
            "date": base_date,
            "time": base_time,
            "source": "short",
            "from_cache": True,
            "stale": True,
        }

    raise RuntimeError(errors[0] if errors else "SHORT_WEATHER_UNAVAILABLE")


def _forecast_payloads(service_key, land_reg_id, temp_reg_id):
    stale_pair = None
    errors = []

    for tmfc in _tmfc_candidates():
        land_cache_key = f"mid_getMidLandFcst_{land_reg_id}_{tmfc}"
        temp_cache_key = f"mid_getMidTa_{temp_reg_id}_{tmfc}"
        cached_land = _read_cache(land_cache_key)
        cached_temp = _read_cache(temp_cache_key)
        if cached_land and cached_temp and stale_pair is None:
            stale_pair = (tmfc, cached_land, cached_temp)

        try:
            land_payload, land_from_cache = _fetch_mid("getMidLandFcst", service_key, land_reg_id, tmfc)
            temp_payload, temp_from_cache = _fetch_mid("getMidTa", service_key, temp_reg_id, tmfc)
            return land_payload, temp_payload, {
                "date": tmfc[:8],
                "time": tmfc[8:12],
                "tmFc": tmfc,
                "from_cache": land_from_cache and temp_from_cache,
                "stale": False,
            }
        except PermissionError:
            raise
        except Exception as exc:
            errors.append(f"{tmfc}:{exc}")

    if stale_pair:
        tmfc, land_payload, temp_payload = stale_pair
        return land_payload, temp_payload, {
            "date": tmfc[:8],
            "time": tmfc[8:12],
            "tmFc": tmfc,
            "from_cache": True,
            "stale": True,
        }

    raise RuntimeError(errors[0] if errors else "WEATHER_UNAVAILABLE")


def _first_item(payload):
    items = _items_from_payload(payload)
    return items[0] if items else {}


def _clean_text(value):
    return str(value or "").strip()


def _to_float(value):
    if value is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    if not match:
        return None
    try:
        return float(match.group(0))
    except Exception:
        return None


def _format_number(value, digits=0):
    if value is None:
        return "-"
    if digits <= 0 or abs(value - round(value)) < 0.05:
        return str(int(round(value)))
    return f"{value:.{digits}f}"


def _format_pop(value):
    return f"{_format_number(value)}%" if value is not None else "-"


def _format_humidity(value):
    return f"{_format_number(value)}%" if value is not None else "-"


def _format_wind(value):
    return f"{_format_number(value, 1)}m/s" if value is not None else "-"


def _format_temp_range(temp_min, temp_max):
    if temp_min is not None and temp_max is not None:
        return f"{_format_number(temp_min)}~{_format_number(temp_max)}°C"
    if temp_min is not None:
        return f"최저 {_format_number(temp_min)}°C"
    if temp_max is not None:
        return f"최고 {_format_number(temp_max)}°C"
    return "-"


def _condition_from_text(value):
    text = _clean_text(value)
    has_rain = any(word in text for word in ("비", "소나기", "강수"))
    has_snow = "눈" in text
    if has_rain and has_snow:
        return "mixed"
    if has_snow:
        return "snow"
    if has_rain:
        return "rain"
    if "맑" in text:
        return "sunny"
    return "cloud"


def _icon_for_tone(tone):
    if tone == "sunny":
        return "fa-solid fa-sun"
    if tone == "rain":
        return "fa-solid fa-umbrella"
    if tone == "snow":
        return "fa-solid fa-snowflake"
    if tone == "mixed":
        return "fa-solid fa-cloud-rain"
    return "fa-solid fa-cloud"


def _dominant_tone(texts):
    tones = [_condition_from_text(text) for text in texts if _clean_text(text)]
    return _dominant_tone_from_tones(tones)


def _dominant_tone_from_tones(tones):
    if not tones:
        return "cloud"
    if "mixed" in tones or ("rain" in tones and "snow" in tones):
        return "mixed"
    for tone in ("snow", "rain"):
        if tone in tones:
            return tone
    if all(tone == "sunny" for tone in tones):
        return "sunny"
    return "cloud"


def _forecast_texts(land_item, day):
    if day <= 7:
        return [
            ("오전", _clean_text(land_item.get(f"wf{day}Am")), _to_float(land_item.get(f"rnSt{day}Am"))),
            ("오후", _clean_text(land_item.get(f"wf{day}Pm")), _to_float(land_item.get(f"rnSt{day}Pm"))),
        ]
    return [("종일", _clean_text(land_item.get(f"wf{day}")), _to_float(land_item.get(f"rnSt{day}")))]


def _short_condition(row):
    pty = _clean_text(row.get("PTY"))
    if pty in PTY_LABELS:
        if pty in ("2", "6"):
            return PTY_LABELS[pty], "mixed"
        if pty in ("3", "7"):
            return PTY_LABELS[pty], "snow"
        return PTY_LABELS[pty], "rain"

    sky = _clean_text(row.get("SKY"))
    text = SKY_LABELS.get(sky, "날씨")
    return text, "sunny" if sky == "1" else "cloud"


def _open_meteo_condition(code):
    try:
        numeric_code = int(float(code))
    except Exception:
        numeric_code = -1
    return OPEN_METEO_WEATHER_CODES.get(numeric_code, ("날씨", "cloud"))


def _open_meteo_severity(code):
    _, tone = _open_meteo_condition(code)
    if tone == "mixed":
        return 5
    if tone == "snow":
        return 4
    if tone == "rain":
        return 3
    if tone == "cloud":
        return 1
    return 0


def _short_rows_for_period(rows, start_hour, end_hour):
    selected = []
    for time_key, row in rows:
        try:
            hour = int(time_key[:2])
        except Exception:
            continue
        if start_hour <= hour < end_hour:
            selected.append((time_key, row))
    return selected


def _select_short_condition_row(rows):
    wet_rows = [(time_key, row) for time_key, row in rows if _clean_text(row.get("PTY")) not in ("", "0")]
    source = wet_rows or rows
    if not source:
        return None

    def sort_key(item):
        time_key, row = item
        pop = _to_float(row.get("POP"))
        return (pop if pop is not None else -1, time_key)

    return max(source, key=sort_key)


def _numbers_from_rows(rows, category):
    values = []
    for _, row in rows:
        value = _to_float(row.get(category))
        if value is not None:
            values.append(value)
    return values


def _first_number_from_rows(rows, category):
    values = _numbers_from_rows(rows, category)
    return values[0] if values else None


def _avg(values):
    return sum(values) / len(values) if values else None


def _short_period_summary(label, rows, daily_temp_text):
    selected = _select_short_condition_row(rows)
    if not selected:
        return None

    _, selected_row = selected
    text, tone = _short_condition(selected_row)
    temps = _numbers_from_rows(rows, "TMP")
    pops = _numbers_from_rows(rows, "POP")
    humidity_values = _numbers_from_rows(rows, "REH")
    wind_values = _numbers_from_rows(rows, "WSD")
    temp_text = _format_temp_range(min(temps), max(temps)) if temps else daily_temp_text
    pop_max = max(pops) if pops else None

    return {
        "label": label,
        "summary": text,
        "tone": tone,
        "pop": pop_max,
        "tempText": temp_text,
        "popText": _format_pop(pop_max),
        "humidityText": _format_humidity(_avg(humidity_values)),
        "windText": _format_wind(max(wind_values) if wind_values else None),
    }


def _summary_from_periods(periods):
    texts = [text for _, text, _ in periods if text]
    if not texts:
        return "날씨"
    if len(texts) == 1 or len(set(texts)) == 1:
        return texts[0]
    return " / ".join(f"{label} {text}" for label, text, _ in periods if text)


def _day_summary(forecast_date, day, land_item, temp_item):
    periods = _forecast_texts(land_item, day)
    summary = _summary_from_periods(periods)
    tone = _dominant_tone([text for _, text, _ in periods])
    temp_min = _to_float(temp_item.get(f"taMin{day}"))
    temp_max = _to_float(temp_item.get(f"taMax{day}"))
    if not any(text for _, text, _ in periods) and temp_min is None and temp_max is None:
        return None

    pops = [pop for _, _, pop in periods if pop is not None]
    pop_max = max(pops) if pops else None
    temp_text = _format_temp_range(temp_min, temp_max)
    hourly = []

    for label, text, pop in periods:
        if not text:
            continue
        period_tone = _condition_from_text(text)
        hourly.append({
            "time": label,
            "icon": _icon_for_tone(period_tone),
            "tone": period_tone,
            "summary": text,
            "tempText": temp_text,
            "popText": _format_pop(pop),
            "humidityText": "-",
            "windText": "-",
        })

    return {
        "date": forecast_date.strftime("%Y-%m-%d"),
        "icon": _icon_for_tone(tone),
        "tone": tone,
        "summary": summary,
        "tempText": temp_text,
        "popText": _format_pop(pop_max),
        "rainText": _format_pop(pop_max),
        "snowText": "예보 있음" if tone in ("snow", "mixed") else "-",
        "humidityText": "-",
        "windText": "-",
        "hourly": hourly,
    }


def _short_day_summary(date_key, rows_by_time):
    rows = sorted(rows_by_time.items())
    if not rows:
        return None

    tmp_values = _numbers_from_rows(rows, "TMP")
    tmn = _first_number_from_rows(rows, "TMN")
    tmx = _first_number_from_rows(rows, "TMX")
    temp_min = tmn if tmn is not None else min(tmp_values) if tmp_values else None
    temp_max = tmx if tmx is not None else max(tmp_values) if tmp_values else None
    temp_text = _format_temp_range(temp_min, temp_max)
    pops = _numbers_from_rows(rows, "POP")
    humidity_values = _numbers_from_rows(rows, "REH")
    wind_values = _numbers_from_rows(rows, "WSD")

    period_details = [
        _short_period_summary("오전", _short_rows_for_period(rows, 5, 12), temp_text),
        _short_period_summary("오후", _short_rows_for_period(rows, 12, 24), temp_text),
    ]
    period_details = [item for item in period_details if item]
    if not period_details:
        all_day = _short_period_summary("종일", rows, temp_text)
        period_details = [all_day] if all_day else []

    if not period_details and temp_min is None and temp_max is None and not pops:
        return None

    periods = [(item["label"], item["summary"], item["pop"]) for item in period_details]
    summary = _summary_from_periods(periods)
    tone = _dominant_tone_from_tones([item["tone"] for item in period_details])
    pop_max = max(pops) if pops else None
    hourly = [
        {
            "time": item["label"],
            "icon": _icon_for_tone(item["tone"]),
            "tone": item["tone"],
            "summary": item["summary"],
            "tempText": item["tempText"],
            "popText": item["popText"],
            "humidityText": item["humidityText"],
            "windText": item["windText"],
        }
        for item in period_details
    ]

    return {
        "date": date_key,
        "icon": _icon_for_tone(tone),
        "tone": tone,
        "summary": summary,
        "tempText": temp_text,
        "popText": _format_pop(pop_max),
        "rainText": _format_pop(pop_max),
        "snowText": "예보 있음" if tone in ("snow", "mixed") else "-",
        "humidityText": _format_humidity(_avg(humidity_values)),
        "windText": _format_wind(max(wind_values) if wind_values else None),
        "hourly": hourly,
    }


def _open_meteo_period_summary(label, rows, daily_temp_text):
    if not rows:
        return None

    def sort_key(row):
        pop = _to_float(row.get("precipitation_probability"))
        return (_open_meteo_severity(row.get("weather_code")), pop if pop is not None else -1, row.get("time", ""))

    selected_row = max(rows, key=sort_key)
    text, tone = _open_meteo_condition(selected_row.get("weather_code"))
    temps = [value for value in (_to_float(row.get("temperature_2m")) for row in rows) if value is not None]
    pops = [value for value in (_to_float(row.get("precipitation_probability")) for row in rows) if value is not None]
    humidity_values = [value for value in (_to_float(row.get("relative_humidity_2m")) for row in rows) if value is not None]
    wind_values = [value for value in (_to_float(row.get("wind_speed_10m")) for row in rows) if value is not None]
    temp_text = _format_temp_range(min(temps), max(temps)) if temps else daily_temp_text
    pop_max = max(pops) if pops else None

    return {
        "label": label,
        "summary": text,
        "tone": tone,
        "pop": pop_max,
        "tempText": temp_text,
        "popText": _format_pop(pop_max),
        "humidityText": _format_humidity(_avg(humidity_values)),
        "windText": _format_wind(max(wind_values) if wind_values else None),
    }


def _open_meteo_day_summary(date_key, daily_row, hourly_rows):
    temp_min = _to_float(daily_row.get("temperature_2m_min"))
    temp_max = _to_float(daily_row.get("temperature_2m_max"))
    if (temp_min is None or temp_max is None) and hourly_rows:
        temps = [value for value in (_to_float(row.get("temperature_2m")) for row in hourly_rows) if value is not None]
        if temps:
            temp_min = temp_min if temp_min is not None else min(temps)
            temp_max = temp_max if temp_max is not None else max(temps)
    temp_text = _format_temp_range(temp_min, temp_max)

    morning = [row for row in hourly_rows if 5 <= int(row.get("time", "00")[:2]) < 12]
    afternoon = [row for row in hourly_rows if 12 <= int(row.get("time", "00")[:2]) < 24]
    period_details = [
        _open_meteo_period_summary("오전", morning, temp_text),
        _open_meteo_period_summary("오후", afternoon, temp_text),
    ]
    period_details = [item for item in period_details if item]
    if not period_details:
        all_day = _open_meteo_period_summary("종일", hourly_rows, temp_text)
        period_details = [all_day] if all_day else []

    if period_details:
        periods = [(item["label"], item["summary"], item["pop"]) for item in period_details]
        summary = _summary_from_periods(periods)
        tone = _dominant_tone_from_tones([item["tone"] for item in period_details])
    else:
        summary, tone = _open_meteo_condition(daily_row.get("weather_code"))

    daily_pop = _to_float(daily_row.get("precipitation_probability_max"))
    hourly_pops = [value for value in (_to_float(row.get("precipitation_probability")) for row in hourly_rows) if value is not None]
    pop_max = daily_pop if daily_pop is not None else max(hourly_pops) if hourly_pops else None
    humidity_values = [value for value in (_to_float(row.get("relative_humidity_2m")) for row in hourly_rows) if value is not None]
    wind_values = [value for value in (_to_float(row.get("wind_speed_10m")) for row in hourly_rows) if value is not None]
    hourly = [
        {
            "time": item["label"],
            "icon": _icon_for_tone(item["tone"]),
            "tone": item["tone"],
            "summary": item["summary"],
            "tempText": item["tempText"],
            "popText": item["popText"],
            "humidityText": item["humidityText"],
            "windText": item["windText"],
        }
        for item in period_details
    ]

    return {
        "date": date_key,
        "icon": _icon_for_tone(tone),
        "tone": tone,
        "summary": summary,
        "tempText": temp_text,
        "popText": _format_pop(pop_max),
        "rainText": _format_pop(pop_max),
        "snowText": "예보 있음" if tone in ("snow", "mixed") else "-",
        "humidityText": _format_humidity(_avg(humidity_values)),
        "windText": _format_wind(max(wind_values) if wind_values else None),
        "hourly": hourly,
    }


def _array_value(values, index):
    if not isinstance(values, list) or index >= len(values):
        return None
    return values[index]


def _build_open_meteo_days(payload):
    daily = payload.get("daily") if isinstance(payload, dict) else {}
    hourly = payload.get("hourly") if isinstance(payload, dict) else {}
    if not isinstance(daily, dict) or not isinstance(hourly, dict):
        return {}

    hourly_by_date = {}
    for index, stamp in enumerate(hourly.get("time") or []):
        if not isinstance(stamp, str) or "T" not in stamp:
            continue
        date_key, time_text = stamp.split("T", 1)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_key):
            continue
        hourly_by_date.setdefault(date_key, []).append({
            "time": time_text[:5].replace(":", ""),
            "temperature_2m": _array_value(hourly.get("temperature_2m"), index),
            "relative_humidity_2m": _array_value(hourly.get("relative_humidity_2m"), index),
            "precipitation_probability": _array_value(hourly.get("precipitation_probability"), index),
            "weather_code": _array_value(hourly.get("weather_code"), index),
            "wind_speed_10m": _array_value(hourly.get("wind_speed_10m"), index),
        })

    days = {}
    for index, date_key in enumerate(daily.get("time") or []):
        if not isinstance(date_key, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date_key):
            continue
        daily_row = {
            "weather_code": _array_value(daily.get("weather_code"), index),
            "temperature_2m_max": _array_value(daily.get("temperature_2m_max"), index),
            "temperature_2m_min": _array_value(daily.get("temperature_2m_min"), index),
            "precipitation_probability_max": _array_value(daily.get("precipitation_probability_max"), index),
        }
        summary = _open_meteo_day_summary(date_key, daily_row, hourly_by_date.get(date_key, []))
        if summary:
            days[date_key] = summary
    return days


def _build_short_days(village_payload):
    grouped = {}
    for item in _items_from_payload(village_payload):
        category = _clean_text(item.get("category"))
        fcst_date = _clean_text(item.get("fcstDate"))
        fcst_time = _clean_text(item.get("fcstTime"))
        if category not in SHORT_CATEGORIES:
            continue
        if not re.match(r"^\d{8}$", fcst_date) or not re.match(r"^\d{4}$", fcst_time):
            continue

        date_key = f"{fcst_date[:4]}-{fcst_date[4:6]}-{fcst_date[6:8]}"
        grouped.setdefault(date_key, {}).setdefault(fcst_time, {})[category] = item.get("fcstValue")

    days = {}
    for date_key, rows_by_time in grouped.items():
        summary = _short_day_summary(date_key, rows_by_time)
        if summary:
            days[date_key] = summary
    return days


def _build_all_days(land_payload, temp_payload, base):
    land_item = _first_item(land_payload)
    temp_item = _first_item(temp_payload)
    if not land_item or not temp_item:
        return {}

    base_date = datetime.datetime.strptime(base["date"], "%Y%m%d").date()
    days = {}
    for day in range(3, 11):
        forecast_date = base_date + datetime.timedelta(days=day)
        date_key = forecast_date.strftime("%Y-%m-%d")
        summary = _day_summary(forecast_date, day, land_item, temp_item)
        if summary:
            days[date_key] = summary

    return days


def _filter_days(days, year_month):
    target_prefix = year_month + "-"
    return {
        date_key: summary
        for date_key, summary in sorted(days.items())
        if date_key.startswith(target_prefix)
    }


def _coverage_from_days(days):
    date_keys = sorted(days.keys())
    if not date_keys:
        return None
    return {
        "startDate": date_keys[0],
        "endDate": date_keys[-1],
        "message": "날씨 예보 제공 범위 밖입니다.",
    }


_load_env_file()
service_key = _service_key()
if not service_key:
    response_payload = {"success": False, "message": "날씨 인증키가 설정되지 않았습니다."}
else:
    year_month = _year_month()
    user_id = _current_user_id()
    location = _weather_location()
    if not location:
        response_payload = _snapshot_response(user_id, year_month) or {"success": False, "message": "현재 위치를 확인해야 날씨를 불러올 수 있습니다."}
    else:
        land_reg_id = location["landRegId"]
        temp_reg_id = location["tempRegId"]

        try:
            all_days = {}
            base = None
            permission_errors = []
            weather_errors = []

            try:
                short_payload, short_base = _short_forecast_payload(service_key, location["nx"], location["ny"])
                all_days.update(_build_short_days(short_payload))
                base = short_base
            except PermissionError as exc:
                permission_errors.append(str(exc))
                try:
                    base = _merge_open_meteo_days(all_days, location, base)
                except Exception as fallback_exc:
                    weather_errors.append(str(fallback_exc))
            except Exception as exc:
                weather_errors.append(str(exc))
                try:
                    base = _merge_open_meteo_days(all_days, location, base)
                except Exception as fallback_exc:
                    weather_errors.append(str(fallback_exc))

            try:
                land_payload, temp_payload, mid_base = _forecast_payloads(service_key, land_reg_id, temp_reg_id)
                for date_key, summary in _build_all_days(land_payload, temp_payload, mid_base).items():
                    all_days.setdefault(date_key, summary)
                if base is None:
                    base = mid_base
                else:
                    base["mid"] = mid_base
            except PermissionError as exc:
                permission_errors.append(str(exc))
            except Exception as exc:
                weather_errors.append(str(exc))

            today_key = _now_kst().strftime("%Y-%m-%d")
            if today_key not in all_days:
                try:
                    base = _merge_open_meteo_days(all_days, location, base, prefer_base=True)
                except Exception as fallback_exc:
                    weather_errors.append(str(fallback_exc))

            if not all_days:
                if permission_errors:
                    raise PermissionError(permission_errors[0])
                raise RuntimeError(weather_errors[0] if weather_errors else "WEATHER_UNAVAILABLE")

            all_days = _annotate_weather_days(all_days, location, base)
            _save_weather_snapshots(user_id, all_days, location, base)
            all_days = _merge_weather_snapshots(user_id, all_days, year_month)

            response_payload = {
                "success": True,
                "data": {
                    "year_month": year_month,
                    "location": location,
                    "base": base,
                    "coverage": _coverage_from_days(all_days),
                    "days": _filter_days(all_days, year_month),
                },
            }
        except PermissionError:
            response_payload = _snapshot_response(user_id, year_month, "저장된 날씨 기록입니다.") or {
                "success": False,
                "message": "날씨 API 권한 확인이 필요합니다. 공공데이터포털에서 기상청 단기예보/중기예보 활용신청 승인 상태를 확인해 주세요.",
            }
        except Exception:
            response_payload = _snapshot_response(user_id, year_month, "저장된 날씨 기록입니다.") or {"success": False, "message": "날씨 정보를 불러오지 못했습니다."}

wiz.response.json(response_payload)
