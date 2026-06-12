import os


candidate_paths = [
    wiz.project.fs("bundle", "src", "assets", "brand").abspath("icon.ico"),
    wiz.project.fs("src", "assets", "brand").abspath("icon.ico"),
]

for filepath in candidate_paths:
    if os.path.isfile(filepath):
        wiz.response.headers.set(**{"Cache-Control": "public, max-age=86400"})
        wiz.response.download(filepath, as_attachment=False)

wiz.response.abort(404)
