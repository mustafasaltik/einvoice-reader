from __future__ import annotations

from enum import Enum

from core.exceptions import NoPdfAttachmentError, UnknownFormatError


class Syntax(str, Enum):
    UBL = "UBL"
    CII = "CII"


_UBL_NAMESPACES = (
    b"urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    b"urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
)

_CII_NAMESPACES = (
    b"urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    b"urn:ferd:CrossIndustryDocument:invoice:1p0",  # ZUGFeRD 1.x
)

_PDF_MAGIC = b"%PDF"


def detect_syntax(raw: bytes) -> Syntax:
    """Return the e-invoice syntax carried in *raw*.

    For ZUGFeRD/Factur-X PDFs the embedded XML is extracted first; the
    caller receives a Syntax value and should call extract_pdf_xml to get
    the actual XML bytes before parsing.

    Raises ValueError for unrecognised input.
    """
    if raw[:4] == _PDF_MAGIC:
        # Peek inside without full extraction — presence of CII namespace
        # string is sufficient for detection.
        if any(ns in raw for ns in _CII_NAMESPACES):
            return Syntax.CII
        raise NoPdfAttachmentError()

    for ns in _UBL_NAMESPACES:
        if ns in raw:
            return Syntax.UBL

    for ns in _CII_NAMESPACES:
        if ns in raw:
            return Syntax.CII

    raise UnknownFormatError()


def extract_pdf_xml(raw: bytes) -> bytes:
    """Extract the embedded XML from a ZUGFeRD/Factur-X PDF.

    Uses pypdf to locate the attached XML file (factur-x.xml or
    zugferd-invoice.xml) and returns its raw bytes.

    Raises ValueError if no recognised attachment is found.
    """
    import pypdf  # import here so core/detect.py has no mandatory dep on pypdf

    reader = pypdf.PdfReader(__import__("io").BytesIO(raw))
    names = reader.trailer["/Root"].get("/Names", {})
    embedded = names.get("/EmbeddedFiles", {}).get("/Names", [])

    # EmbeddedFiles/Names is a flat list: [name, ref, name, ref, ...]
    it = iter(embedded)
    for name in it:
        ref = next(it)
        lower = name.lower() if isinstance(name, str) else ""
        if "factur-x" in lower or "zugferd" in lower or lower.endswith(".xml"):
            obj = ref.get_object()
            return obj["/EF"]["/F"].get_data()

    raise NoPdfAttachmentError()
