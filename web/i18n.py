from __future__ import annotations

from fastapi import Request

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # nav / footer
        "site_name": "E-Invoice Reader",
        "nav_rules": "Validation rules",
        "footer_privacy": "Files are parsed in memory and never stored.",
        "footer_rules": "Validation rules",
        # index
        "index_meta_description": "Free e-invoice reader for XRechnung, Peppol BIS, ZUGFeRD and Factur-X. Upload XML or PDF — get a plain-language summary and validation report instantly, no account needed.",
        "rules_meta_description": "Plain-language explanations of all EN 16931 validation rules used to validate XRechnung, Peppol BIS, ZUGFeRD and Factur-X invoices.",
        "index_title": "Read your e-invoice",
        "index_subtitle": (
            "Upload an XML invoice (XRechnung, Peppol BIS, NLCIUS) or a "
            "ZUGFeRD / Factur-X PDF. You'll get a plain-language summary "
            "and a validation report — instantly, free, no account needed."
        ),
        "index_upload_label": "Upload file",
        "index_no_file": "No file chosen",
        "index_or": "or",
        "index_paste_label": "Paste XML",
        "index_paste_placeholder": '<?xml version="1.0" ...?>',
        "index_submit": "Read invoice",
        # errors
        "error_no_input": "Please upload a file or paste invoice XML.",
        "error_parse_prefix": "Could not read invoice:",
        # result — header
        "result_invoice": "Invoice",
        "result_credit_note": "Credit Note",
        "result_read_another": "← Read another",
        # result — summary fields
        "result_syntax": "Syntax",
        "result_ruleset": "Ruleset (BT-24)",
        "result_issue_date": "Issue date (BT-2)",
        "result_currency": "Currency (BT-5)",
        "result_due_date": "Due date (BT-9)",
        "result_buyer_ref": "Buyer ref (BT-10)",
        "result_seller": "Seller (BT-27)",
        "result_buyer": "Buyer (BT-44)",
        "result_vat_label": "VAT",
        # result — totals table (BT numbers corrected)
        "result_net_total": "Net total (BT-106)",
        "result_allowances": "Allowances (BT-107)",
        "result_charges": "Charges (BT-108)",
        "result_excl_vat": "Total excl. VAT (BT-109)",
        "result_vat_amount": "VAT (BT-110)",
        "result_incl_vat": "Total incl. VAT (BT-112)",
        "result_prepaid": "Prepaid (BT-113)",
        "result_amount_due": "Amount due (BT-115)",
        # result — line items table
        "result_lines_heading": "Line items",
        "result_col_id": "#",
        "result_col_description": "Description",
        "result_col_qty": "Qty",
        "result_col_unit_price": "Unit price",
        "result_col_vat": "VAT",
        "result_col_net": "Net",
        # result — validation report
        "result_validation_heading": "Validation report",
        "result_learn_more": "Learn more about",
        # result — download
        "result_download_pdf": "Download PDF",
        # rules index
        "rules_title": "EN 16931 Validation Rules",
        "rules_subtitle": "Plain-language explanations of the rules used to validate your invoice.",
        # rule detail
        "rule_back": "← All rules",
        "rule_what_it_checks": "What this rule checks",
        "rule_also_in": "Auf Deutsch",
        "rule_bt_involved": "Business Terms involved",
    },
    "de": {
        # nav / footer
        "site_name": "E-Rechnung lesen",
        "nav_rules": "Validierungsregeln",
        "footer_privacy": "Dateien werden im Arbeitsspeicher verarbeitet und nicht gespeichert.",
        "footer_rules": "Validierungsregeln",
        # index
        "index_meta_description": "Kostenloser E-Rechnungsleser für XRechnung, Peppol BIS, ZUGFeRD und Factur-X. XML oder PDF hochladen — sofort eine verständliche Zusammenfassung und einen Validierungsbericht erhalten.",
        "rules_meta_description": "Verständliche Erklärungen aller EN 16931-Validierungsregeln für XRechnung, Peppol BIS, ZUGFeRD und Factur-X.",
        "index_title": "Ihre E-Rechnung lesen",
        "index_subtitle": (
            "Laden Sie eine XML-Rechnung (XRechnung, Peppol BIS, NLCIUS) oder eine "
            "ZUGFeRD / Factur-X-PDF hoch. Sie erhalten eine verständliche "
            "Zusammenfassung und einen Validierungsbericht – sofort, kostenlos, ohne Konto."
        ),
        "index_upload_label": "Datei hochladen",
        "index_no_file": "Keine Datei ausgewählt",
        "index_or": "oder",
        "index_paste_label": "XML einfügen",
        "index_paste_placeholder": '<?xml version="1.0" ...?>',
        "index_submit": "Rechnung lesen",
        # errors
        "error_no_input": "Bitte laden Sie eine Datei hoch oder fügen Sie XML ein.",
        "error_parse_prefix": "Rechnung konnte nicht gelesen werden:",
        # result — header
        "result_invoice": "Rechnung",
        "result_credit_note": "Gutschrift",
        "result_read_another": "← Weitere Rechnung lesen",
        # result — summary fields
        "result_syntax": "Syntax",
        "result_ruleset": "Regelwerk (BT-24)",
        "result_issue_date": "Rechnungsdatum (BT-2)",
        "result_currency": "Währung (BT-5)",
        "result_due_date": "Fälligkeitsdatum (BT-9)",
        "result_buyer_ref": "Käuferreferenz (BT-10)",
        "result_seller": "Verkäufer (BT-27)",
        "result_buyer": "Käufer (BT-44)",
        "result_vat_label": "MwSt.",
        # result — totals table
        "result_net_total": "Nettobetrag (BT-106)",
        "result_allowances": "Nachlässe (BT-107)",
        "result_charges": "Abgaben (BT-108)",
        "result_excl_vat": "Betrag ohne MwSt. (BT-109)",
        "result_vat_amount": "MwSt.-Betrag (BT-110)",
        "result_incl_vat": "Betrag mit MwSt. (BT-112)",
        "result_prepaid": "Bereits gezahlt (BT-113)",
        "result_amount_due": "Fälliger Betrag (BT-115)",
        # result — line items table
        "result_lines_heading": "Rechnungspositionen",
        "result_col_id": "#",
        "result_col_description": "Beschreibung",
        "result_col_qty": "Menge",
        "result_col_unit_price": "Einzelpreis",
        "result_col_vat": "MwSt.",
        "result_col_net": "Netto",
        # result — validation report
        "result_validation_heading": "Validierungsbericht",
        "result_learn_more": "Mehr zu",
        # result — download
        "result_download_pdf": "PDF herunterladen",
        # rules index
        "rules_title": "EN 16931 Validierungsregeln",
        "rules_subtitle": "Verständliche Erklärungen der Regeln zur Validierung Ihrer Rechnung.",
        # rule detail
        "rule_back": "← Alle Regeln",
        "rule_what_it_checks": "Was diese Regel prüft",
        "rule_also_in": "In English",
        "rule_bt_involved": "Beteiligte Geschäftsbegriffe",
    },
    "nl": {
        # nav / footer
        "site_name": "E-Factuurlezer",
        "nav_rules": "Validatieregels",
        "footer_privacy": "Bestanden worden in het geheugen verwerkt en nooit opgeslagen.",
        "footer_rules": "Validatieregels",
        # index
        "index_meta_description": "Gratis e-factuurlezer voor XRechnung, Peppol BIS, ZUGFeRD en Factur-X. Upload XML of PDF — ontvang direct een begrijpelijke samenvatting en validatierapport.",
        "rules_meta_description": "Begrijpelijke uitleg van alle EN 16931 validatieregels voor XRechnung, Peppol BIS, ZUGFeRD en Factur-X.",
        "index_title": "Lees uw e-factuur",
        "index_subtitle": (
            "Upload een XML-factuur (XRechnung, Peppol BIS, NLCIUS) of een "
            "ZUGFeRD / Factur-X PDF. U ontvangt een begrijpelijke samenvatting "
            "en een validatierapport — direct, gratis, zonder account."
        ),
        "index_upload_label": "Bestand uploaden",
        "index_no_file": "Geen bestand gekozen",
        "index_or": "of",
        "index_paste_label": "XML plakken",
        "index_paste_placeholder": '<?xml version="1.0" ...?>',
        "index_submit": "Factuur lezen",
        # errors
        "error_no_input": "Upload een bestand of plak XML in.",
        "error_parse_prefix": "Factuur kon niet worden gelezen:",
        # result — header
        "result_invoice": "Factuur",
        "result_credit_note": "Creditnota",
        "result_read_another": "← Andere factuur lezen",
        # result — summary fields
        "result_syntax": "Syntax",
        "result_ruleset": "Regelset (BT-24)",
        "result_issue_date": "Factuurdatum (BT-2)",
        "result_currency": "Valuta (BT-5)",
        "result_due_date": "Vervaldatum (BT-9)",
        "result_buyer_ref": "Koperreferentie (BT-10)",
        "result_seller": "Verkoper (BT-27)",
        "result_buyer": "Koper (BT-44)",
        "result_vat_label": "BTW",
        # result — totals table
        "result_net_total": "Nettobedrag (BT-106)",
        "result_allowances": "Kortingen (BT-107)",
        "result_charges": "Toeslagen (BT-108)",
        "result_excl_vat": "Totaal excl. BTW (BT-109)",
        "result_vat_amount": "BTW-bedrag (BT-110)",
        "result_incl_vat": "Totaal incl. BTW (BT-112)",
        "result_prepaid": "Reeds betaald (BT-113)",
        "result_amount_due": "Te betalen bedrag (BT-115)",
        # result — line items table
        "result_lines_heading": "Factuurregels",
        "result_col_id": "#",
        "result_col_description": "Omschrijving",
        "result_col_qty": "Aantal",
        "result_col_unit_price": "Eenheidsprijs",
        "result_col_vat": "BTW",
        "result_col_net": "Netto",
        # result — validation report
        "result_validation_heading": "Validatierapport",
        "result_learn_more": "Meer over",
        # result — download
        "result_download_pdf": "PDF downloaden",
        # rules index
        "rules_title": "EN 16931 Validatieregels",
        "rules_subtitle": "Begrijpelijke uitleg van de regels voor het valideren van uw factuur.",
        # rule detail
        "rule_back": "← Alle regels",
        "rule_what_it_checks": "Wat deze regel controleert",
        "rule_also_in": "In English",
        "rule_bt_involved": "Betrokken zakelijke termen",
    },
}

_VALID = {"en", "de", "nl"}


def get_locale(request: Request, override: str | None = None) -> str:
    """Resolve locale: explicit override → cookie → Accept-Language header."""
    if override in _VALID:
        return override
    cookie = request.cookies.get("lang")
    if cookie in _VALID:
        return cookie
    accept = request.headers.get("accept-language", "").lower()
    if accept.startswith("de"):
        return "de"
    if accept.startswith("nl"):
        return "nl"
    return "en"


def get_trans(locale: str) -> dict[str, str]:
    return _TRANSLATIONS.get(locale, _TRANSLATIONS["en"])
