from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from web.seo import SITE_URL

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.globals["site_url"] = SITE_URL
