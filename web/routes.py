from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse

from web.templating import templates
from core.detect import Syntax, detect_syntax, extract_pdf_xml
from core.rules import RULES, RULES_BY_ID, validate

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.post("/analyse", response_class=HTMLResponse)
async def analyse(request: Request, file: UploadFile = File(None), paste: str = Form("")):
    if file and file.filename:
        raw = await file.read()
    elif paste.strip():
        raw = paste.strip().encode()
    else:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": "Please upload a file or paste invoice XML."},
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
            context={"error": f"Could not read invoice: {exc}"},
        )

    results = validate(invoice)
    locale = "de" if request.headers.get("accept-language", "").startswith("de") else "en"

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"invoice": invoice, "results": results, "locale": locale},
    )


@router.get("/rules", response_class=HTMLResponse)
async def rules_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="rules_index.html",
        context={"rules": RULES},
    )


@router.get("/rules/{rule_id}", response_class=HTMLResponse)
async def rule_detail(request: Request, rule_id: str):
    rule = RULES_BY_ID.get(rule_id.upper())
    if rule is None:
        return HTMLResponse(status_code=404, content="Rule not found.")
    locale = "de" if request.headers.get("accept-language", "").startswith("de") else "en"
    return templates.TemplateResponse(
        request=request,
        name="rule.html",
        context={"rule": rule, "locale": locale},
    )
