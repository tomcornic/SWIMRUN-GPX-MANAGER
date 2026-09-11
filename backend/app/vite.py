import json
from pathlib import Path

from flask import Flask


def register_vite(app: Flask) -> None:
    manifest_path = Path(app.static_folder) / "dist" / ".vite" / "manifest.json"

    def vite_asset(entry: str) -> dict:
        if app.config["VITE_DEV_SERVER"]:
            base = app.config["VITE_DEV_SERVER_URL"]
            return {
                "dev": True,
                "client_src": f"{base}/@vite/client",
                "script_src": f"{base}/src/{entry}/main.ts",
                "css_hrefs": [],
            }

        manifest = json.loads(manifest_path.read_text())
        entry_chunk = manifest[f"src/{entry}/main.ts"]

        css_files: list[str] = []
        chunks_to_visit = [entry_chunk]
        while chunks_to_visit:
            chunk = chunks_to_visit.pop()
            css_files.extend(chunk.get("css", []))
            chunks_to_visit.extend(manifest[key] for key in chunk.get("imports", []))

        return {
            "dev": False,
            "script_src": f"/static/dist/{entry_chunk['file']}",
            "css_hrefs": [f"/static/dist/{css}" for css in css_files],
        }

    app.jinja_env.globals["vite_asset"] = vite_asset
