from __future__ import annotations

from datetime import date
from decimal import Decimal

from lxml import etree

from core.model import Address, Invoice, Line, Party, Totals, VatBreakdown

_NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cn":  "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
}

_PARSER = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    load_dtd=False,
)


def parse(raw: bytes) -> Invoice:
    """Parse a UBL Invoice or CreditNote XML document into an Invoice."""
    root = etree.fromstring(raw, parser=_PARSER)
    tag = etree.QName(root.tag).localname
    is_credit_note = tag == "CreditNote"

    def t(xpath: str) -> str | None:
        nodes = root.xpath(xpath, namespaces=_NS)
        return nodes[0].text.strip() if nodes and nodes[0].text else None

    def d(xpath: str) -> Decimal:
        val = t(xpath)
        return Decimal(val) if val else Decimal("0")

    def parse_date(val: str | None) -> date | None:
        if not val:
            return None
        return date.fromisoformat(val.strip())

    def parse_party(xpath_prefix: str) -> Party:
        name = t(f"{xpath_prefix}/cac:PartyName/cbc:Name") or t(f"{xpath_prefix}/cac:PartyLegalEntity/cbc:RegistrationName") or ""
        vat_id = t(f"{xpath_prefix}/cac:PartyTaxScheme[cac:TaxScheme/cbc:ID='VAT']/cbc:CompanyID")
        tax_reg = t(f"{xpath_prefix}/cac:PartyLegalEntity/cbc:CompanyID")
        addr_nodes = root.xpath(f"{xpath_prefix}/cac:PostalAddress", namespaces=_NS)
        address = None
        if addr_nodes:
            a = addr_nodes[0]
            def at(tag: str) -> str | None:
                n = a.xpath(f"cbc:{tag}", namespaces=_NS)
                return n[0].text.strip() if n and n[0].text else None
            address = Address(
                street=at("StreetName"),
                city=at("CityName"),
                postcode=at("PostalZone"),
                country=(a.xpath("cac:Country/cbc:IdentificationCode", namespaces=_NS) or [None])[0].text if a.xpath("cac:Country/cbc:IdentificationCode", namespaces=_NS) else "",
            )
        return Party(name=name, vat_id=vat_id, tax_reg_id=tax_reg, address=address)

    line_tag = "cac:CreditNoteLine" if is_credit_note else "cac:InvoiceLine"
    qty_tag  = "cbc:CreditedQuantity" if is_credit_note else "cbc:InvoicedQuantity"

    lines: list[Line] = []
    for ln in root.xpath(f"{line_tag}", namespaces=_NS):
        def lt(xpath: str) -> str | None:
            n = ln.xpath(xpath, namespaces=_NS)
            return n[0].text.strip() if n and n[0].text else None
        def ld(xpath: str) -> Decimal:
            v = lt(xpath)
            return Decimal(v) if v else Decimal("0")
        qty_nodes = ln.xpath(f"cbc:{qty_tag.split(':')[1]}", namespaces=_NS)
        unit = qty_nodes[0].get("unitCode", "") if qty_nodes else ""
        lines.append(Line(
            id=lt("cbc:ID") or "",
            note=lt("cbc:Note"),
            quantity=ld(qty_tag),
            unit=unit,
            net_amount=ld("cbc:LineExtensionAmount"),
            item_name=lt("cac:Item/cbc:Name") or "",
            item_description=lt("cac:Item/cbc:Description"),
            vat_category=lt("cac:Item/cac:ClassifiedTaxCategory/cbc:ID") or "",
            vat_rate=Decimal(lt("cac:Item/cac:ClassifiedTaxCategory/cbc:Percent")) if lt("cac:Item/cac:ClassifiedTaxCategory/cbc:Percent") else None,
            unit_price=Decimal(lt("cac:Price/cbc:PriceAmount")) if lt("cac:Price/cbc:PriceAmount") else None,
            gross_price=Decimal(lt("cac:Price/cac:AllowanceCharge/cbc:BaseAmount")) if lt("cac:Price/cac:AllowanceCharge/cbc:BaseAmount") else None,
            buyer_accounting_ref=lt("cbc:AccountingCost"),
        ))

    vat_breakdown: list[VatBreakdown] = []
    for vb in root.xpath("cac:TaxTotal/cac:TaxSubtotal", namespaces=_NS):
        def vt(xpath: str) -> str | None:
            n = vb.xpath(xpath, namespaces=_NS)
            return n[0].text.strip() if n and n[0].text else None
        vat_breakdown.append(VatBreakdown(
            taxable_amount=Decimal(vt("cbc:TaxableAmount") or "0"),
            tax_amount=Decimal(vt("cbc:TaxAmount") or "0"),
            category_code=vt("cac:TaxCategory/cbc:ID") or "",
            rate=Decimal(vt("cac:TaxCategory/cbc:Percent")) if vt("cac:TaxCategory/cbc:Percent") else None,
            exemption_reason=vt("cac:TaxCategory/cbc:TaxExemptionReason"),
            exemption_reason_code=vt("cac:TaxCategory/cbc:TaxExemptionReasonCode"),
        ))

    lmt = root.xpath("cac:LegalMonetaryTotal", namespaces=_NS)
    lmt = lmt[0] if lmt else None
    def mt(tag: str) -> Decimal:
        if lmt is None:
            return Decimal("0")
        n = lmt.xpath(f"cbc:{tag}", namespaces=_NS)
        return Decimal(n[0].text) if n and n[0].text else Decimal("0")

    totals = Totals(
        line_net_total=mt("LineExtensionAmount"),
        allowances=mt("AllowanceTotalAmount"),
        charges=mt("ChargeTotalAmount"),
        tax_exclusive=mt("TaxExclusiveAmount"),
        tax_amount=Decimal(t("cac:TaxTotal/cbc:TaxAmount") or "0"),
        tax_inclusive=mt("TaxInclusiveAmount"),
        prepaid=mt("PrepaidAmount"),
        rounding=mt("PayableRoundingAmount"),
        due=mt("PayableAmount"),
    )

    return Invoice(
        syntax="UBL",
        customization_id=t("cbc:CustomizationID") or "",
        profile_id=t("cbc:ProfileID"),
        number=t("cbc:ID") or "",
        issue_date=parse_date(t("cbc:IssueDate")),
        type_code=t("cbc:InvoiceTypeCode") or t("cbc:CreditNoteTypeCode") or "",
        currency=t("cbc:DocumentCurrencyCode") or "",
        due_date=parse_date(t("cac:PaymentMeans/cbc:PaymentDueDate") or t("cac:PaymentTerms/cbc:Note")),
        buyer_reference=t("cbc:BuyerReference"),
        purchase_order_ref=t("cac:OrderReference/cbc:ID"),
        note=t("cbc:Note"),
        seller=parse_party("cac:AccountingSupplierParty/cac:Party"),
        buyer=parse_party("cac:AccountingCustomerParty/cac:Party"),
        lines=lines,
        vat_breakdown=vat_breakdown,
        totals=totals,
    )
