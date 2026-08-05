from __future__ import annotations


class InvoiceReadError(Exception):
    """Base class for all known invoice-reading failures."""


class UnknownFormatError(InvoiceReadError):
    """File is not a recognised e-invoice format."""


class NoPdfAttachmentError(InvoiceReadError):
    """PDF does not contain an embedded XML invoice."""


class MalformedXmlError(InvoiceReadError):
    """XML is syntactically invalid or truncated."""


class ParseError(InvoiceReadError):
    """File has the right format but required fields could not be extracted."""
