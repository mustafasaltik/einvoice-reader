from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse
from starlette.templating import _TemplateResponse

from web.templating import templates
from web.i18n import get_locale, get_trans
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
    if lang in ("en", "de"):
        resp.set_cookie("lang", locale, **_COOKIE_OPTS)
    return resp


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, lang: str | None = Query(default=None)):
    return _respond(request, "index.html", {}, lang)


@router.post("/analyse", response_class=HTMLResponse)
async def analyse(request: Request, file: UploadFile = File(None), paste: str = Form("")):
    locale = get_locale(request)
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
                "error": "Please upload a file or paste invoice XML."
                if locale == "en"
                else "Bitte laden Sie eine Datei hoch oder fügen Sie XML ein.",
            },
        )

    try:
        syntax = detect_syntax(raw)
        if raw[:4] == b"%PDF":
            raw = extract_pdf_xml(raw)

        if syntax == Syntax.UBL:
            from core.parsers.ubl import parse
        else:
            from core.parsers.cii import parse

        invoice = parse(raw)
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "trans": trans,
                "locale": locale,
                "error": f"Could not read invoice: {exc}"
                if locale == "en"
                else f"Rechnung konnte nicht gelesen werden: {exc}",
            },
        )

    results = validate(invoice)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"trans": trans, "locale": locale, "invoice": invoice, "results": results},
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
