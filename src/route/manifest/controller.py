ICON_VERSION = "?v=rm-main-logo-20260620"

def icon(path):
    return f"{path}{ICON_VERSION}"

wiz.response.json({
    "id": "/dashboard",
    "name": "RunMate",
    "short_name": "RunMate",
    "description": "러닝 기록을 모바일 홈 화면에서 앱처럼 확인합니다.",
    "lang": "ko-KR",
    "start_url": "/access",
    "scope": "/",
    "display": "standalone",
    "display_override": ["standalone", "minimal-ui"],
    "orientation": "portrait-primary",
    "background_color": "#12121c",
    "theme_color": "#12121c",
    "categories": ["health", "sports", "productivity"],
    "icons": [
        {
            "src": icon("/assets/brand/icon-192.png"),
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any"
        },
        {
            "src": icon("/assets/brand/icon-512.png"),
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any"
        },
        {
            "src": icon("/assets/brand/icon-maskable-192.png"),
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "maskable"
        },
        {
            "src": icon("/assets/brand/icon-maskable-512.png"),
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable"
        }
    ],
    "shortcuts": [
        {
            "name": "대시보드",
            "short_name": "대시보드",
            "url": "/dashboard",
            "icons": [
                {
                    "src": icon("/assets/brand/icon-192.png"),
                    "sizes": "192x192",
                    "type": "image/png"
                }
            ]
        }
    ]
})
