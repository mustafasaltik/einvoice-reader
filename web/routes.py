from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse, Response
from starlette.templating import _TemplateResponse

from web.templating import templates
from web.i18n import get_locale, get_trans
from web.seo import SITE_URL
from core.detect import Syntax, detect_syntax, extract_pdf_xml
from core.rules import RULES, RULES_BY_ID, validate

router = APIRouter()

_COOKIE_OPTS = dict(max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")


def _respond(request: Request, name: str, context: dict, lang: str | None) -> _TemplateResponse:
    locale = get_locale(request, lang)
    resp = templates.TemplateResponse(
        request=request,
        name=name,
        context={"trans": get_trans(locale), "locale": locale, **context},
    )
    if lang in ("en", "de", "nl"):
        resp.set_cookie("lang", locale, **_COOKIE_OPTS)
    return resp


def _parse_raw(raw: bytes):
    """Detect syntax, extract XML from PDF if needed, parse to Invoice."""
    syntax = detect_syntax(raw)
    if raw[:4] == b"%PDF":
        raw = extract_pdf_xml(raw)
    if syntax == Syntax.UBL:
        from core.parsers.ubl import parse
    else:
        from core.parsers.cii import parse
    return parse(raw), raw


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, lang: str | None = Query(default=None)):
    return _respond(request, "index.html", {}, lang)


@router.post("/analyse", response_class=HTMLResponse)
async def analyse(request: Request, file: UploadFile = File(None), paste: str = Form(""), lang: str = Form("")):
    locale = get_locale(request, lang or None)
    trans = get_trans(locale)

    if file and file.filename:
        raw = await file.read()
    elif paste.strip():
        raw = paste.strip().encode()
    else:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "trans": trans,
                "locale": locale,
                "error": trans["error_no_input"],
            },
        )

    try:
        invoice, xml_bytes = _parse_raw(raw)
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "trans": trans,
                "locale": locale,
                "error": f"{trans['error_parse_prefix']} {exc}",
            },
        )

    results = validate(invoice)

    resp = templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "trans": trans,
            "locale": locale,
            "invoice": invoice,
            "results": results,
            "raw_xml": xml_bytes.decode("utf-8", errors="replace"),
        },
    )
    if lang in ("en", "de", "nl"):
        resp.set_cookie("lang", locale, **_COOKIE_OPTS)
    return resp


@router.post("/download")
async def download(
    request: Request,
    paste: str = Form(""),
    locale_field: str = Form("en"),
):
    locale = get_locale(request, locale_field if locale_field in ("en", "de", "nl") else None)

    try:
        raw = paste.strip().encode("utf-8")
        invoice, _ = _parse_raw(raw)
    except Exception as exc:
        return HTMLResponse(
            status_code=400,
            content=f"Could not generate PDF: {exc}",
        )

    from core.pdf import build
    pdf_bytes = build(invoice, locale=locale)

    filename = f"invoice-{invoice.number or 'download'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/rules", response_class=HTMLResponse)
async def rules_index(request: Request, lang: str | None = Query(default=None)):
    return _respond(request, "rules_index.html", {"rules": RULES}, lang)


@router.get("/rules/{rule_id}", response_class=HTMLResponse)
async def rule_detail(request: Request, rule_id: str, lang: str | None = Query(default=None)):
    rule = RULES_BY_ID.get(rule_id.upper())
    if rule is None:
        return HTMLResponse(status_code=404, content="Rule not found.")
    return _respond(request, "rule.html", {"rule": rule}, lang)


@router.get("/robots.txt")
async def robots_txt():
    content = f"User-agent: *\nAllow: /\nDisallow: /analyse\nDisallow: /download\nSitemap: {SITE_URL}/sitemap.xml\n"
    return Response(content=content, media_type="text/plain")


@router.get("/sitemap.xml")
async def sitemap_xml():
    urls: list[str] = []

    def url_block(loc: str, priority: str = "0.8", changefreq: str = "monthly", extra: str = "") -> str:
        return (
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"{extra}"
            f"  </url>\n"
        )

    def hreflang_links(path: str) -> str:
        lines = ""
        for code in ("en", "de", "nl"):
            lines += f'    <xhtml:link rel="alternate" hreflang="{code}" href="{SITE_URL}{path}?lang={code}"/>\n'
        lines += f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}{path}"/>\n'
        return lines

    urls.append(url_block(f"{SITE_URL}/", priority="1.0", changefreq="weekly", extra=hreflang_links("/")))
    urls.append(url_block(f"{SITE_URL}/rules", priority="0.9", changefreq="weekly", extra=hreflang_links("/rules")))

    for rule in RULES:
        path = f"/rules/{rule.slug}"
        urls.append(url_block(f"{SITE_URL}{path}", priority="0.7", extra=hreflang_links(path)))

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "".join(urls)
        + "</urlset>\n"
    )
    return Response(content=body, media_type="application/xml")
