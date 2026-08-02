from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from lxml import etree

from core.model import Address, Invoice, Line, Party, Totals, VatBreakdown

_NS = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
    "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
}

_PARSER = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    load_dtd=False,
)


def _parse_cii_date(val: str | None, fmt_code: str | None = "102") -> date | None:
    """CII dates use UNTDID 2379 format codes. Code 102 = YYYYMMDD (most common)."""
    if not val:
        return None
    val = val.strip()
    code = (fmt_code or "102").strip()
    if code == "102":
        return datetime.strptime(val, "%Y%m%d").date()
    if code == "101":
        return datetime.strptime(val, "%y%m%d").date()
    # Fall back to ISO for anything else
    return date.fromisoformat(val)


def parse(raw: bytes) -> Invoice:
    """Parse a CII CrossIndustryInvoice XML document into an Invoice."""
    root = etree.fromstring(raw, parser=_PARSER)

    def t(xpath: str) -> str | None:
        nodes = root.xpath(xpath, namespaces=_NS)
        return nodes[0].text.strip() if nodes and nodes[0].text else None

    def d(xpath: str) -> Decimal:
        val = t(xpath)
        return Decimal(val) if val else Decimal("0")

    def parse_date_node(xpath_value: str, xpath_format: str) -> date | None:
        val = t(xpath_value)
        fmt = t(xpath_format)
        return _parse_cii_date(val, fmt)

    def parse_party(xpath_prefix: str) -> Party:
        name = (
            t(f"{xpath_prefix}/ram:Name")
            or t(f"{xpath_prefix}/ram:SpecifiedLegalOrganization/ram:TradingBusinessName")
            or ""
        )
        vat_id = t(f"{xpath_prefix}/ram:SpecifiedTaxRegistration[ram:ID/@schemeID='VA']/ram:ID")
        tax_reg = t(f"{xpath_prefix}/ram:SpecifiedLegalOrganization/ram:ID")
        addr_nodes = root.xpath(f"{xpath_prefix}/ram:PostalTradeAddress", namespaces=_NS)
        address = None
        if addr_nodes:
            a = addr_nodes[0]
            def at(tag: str) -> str | None:
                n = a.xpath(f"ram:{tag}", namespaces=_NS)
                return n[0].text.strip() if n and n[0].text else None
            address = Address(
                street=at("LineOne"),
                city=at("CityName"),
                postcode=at("PostcodeCode"),
                country=at("CountryID") or "",
            )
        return Party(name=name, vat_id=vat_id, tax_reg_id=tax_reg, address=address)

    hdr = "rsm:ExchangedDocumentContext"
    doc = "rsm:ExchangedDocument"
    trx = "rsm:SupplyChainTradeTransaction"
    agr = f"{trx}/ram:ApplicableHeaderTradeAgreement"
    dlv = f"{trx}/ram:ApplicableHeaderTradeDelivery"
    stl = f"{trx}/ram:ApplicableHeaderTradeSettlement"

    lines: list[Line] = []
    for ln in root.xpath(f"{trx}/ram:IncludedSupplyChainTradeLineItem", namespaces=_NS):
        def lt(xpath: str) -> str | None:
            n = ln.xpath(xpath, namespaces=_NS)
            return n[0].text.strip() if n and n[0].text else None
        def ld(xpath: str) -> Decimal:
            v = lt(xpath)
            return Decimal(v) if v else Decimal("0")
        qty_nodes = ln.xpath("ram:SpecifiedLineTradeDelivery/ram:BilledQuantity", namespaces=_NS)
        unit = qty_nodes[0].get("unitCode", "") if qty_nodes else ""
        lines.append(Line(
            id=lt("ram:AssociatedDocumentLineDocument/ram:LineID") or "",
            note=lt("ram:AssociatedDocumentLineDocument/ram:IncludedNote/ram:Content"),
            quantity=ld("ram:SpecifiedLineTradeDelivery/ram:BilledQuantity"),
            unit=unit,
            net_amount=ld("ram:SpecifiedLineTradeSettlement/ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount"),
            item_name=lt("ram:SpecifiedTradeProduct/ram:Name") or "",
            item_description=lt("ram:SpecifiedTradeProduct/ram:Description"),
            vat_category=lt("ram:SpecifiedLineTradeSettlement/ram:ApplicableTradeTax/ram:CategoryCode") or "",
            vat_rate=Decimal(lt("ram:SpecifiedLineTradeSettlement/ram:ApplicableTradeTax/ram:RateApplicablePercent")) if lt("ram:SpecifiedLineTradeSettlement/ram:ApplicableTradeTax/ram:RateApplicablePercent") else None,
            unit_price=Decimal(lt("ram:SpecifiedLineTradeAgreement/ram:NetPriceProductTradePrice/ram:ChargeAmount")) if lt("ram:SpecifiedLineTradeAgreement/ram:NetPriceProductTradePrice/ram:ChargeAmount") else None,
            gross_price=Decimal(lt("ram:SpecifiedLineTradeAgreement/ram:GrossPriceProductTradePrice/ram:ChargeAmount")) if lt("ram:SpecifiedLineTradeAgreement/ram:GrossPriceProductTradePrice/ram:ChargeAmount") else None,
            buyer_accounting_ref=lt("ram:SpecifiedLineTradeSettlement/ram:ReceivableSpecifiedTradeAccountingAccount/ram:ID"),
        ))

    vat_breakdown: list[VatBreakdown] = []
    for vb in root.xpath(f"{stl}/ram:ApplicableTradeTax", namespaces=_NS):
        def vt(xpath: str) -> str | None:
            n = vb.xpath(xpath, namespaces=_NS)
            return n[0].text.strip() if n and n[0].text else None
        vat_breakdown.append(VatBreakdown(
            taxable_amount=Decimal(vt("ram:BasisAmount") or "0"),
            tax_amount=Decimal(vt("ram:CalculatedAmount") or "0"),
            category_code=vt("ram:CategoryCode") or "",
            rate=Decimal(vt("ram:RateApplicablePercent")) if vt("ram:RateApplicablePercent") else None,
            exemption_reason=vt("ram:ExemptionReason"),
            exemption_reason_code=vt("ram:ExemptionReasonCode"),
        ))

    def st(xpath: str) -> Decimal:
        return d(f"{stl}/{xpath}")

    totals = Totals(
        line_net_total=st("ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:LineTotalAmount"),
        allowances=st("ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:AllowanceTotalAmount"),
        charges=st("ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:ChargeTotalAmount"),
        tax_exclusive=st("ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxBasisTotalAmount"),
        tax_amount=st("ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxTotalAmount"),
        tax_inclusive=st("ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount"),
        prepaid=st("ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TotalPrepaidAmount"),
        rounding=st("ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:RoundingAmount"),
        due=st("ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:DuePayableAmount"),
    )

    issue_nodes = root.xpath(f"{doc}/ram:IssueDateTime/udt:DateTimeString", namespaces=_NS)
    if issue_nodes:
        issue_val = issue_nodes[0].text.strip() if issue_nodes[0].text else None
        issue_fmt = issue_nodes[0].get("format") or "102"
    else:
        issue_val = t(f"{doc}/ram:IssueDateTime")
        issue_fmt = "102"

    due_nodes = root.xpath(
        f"{stl}/ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString",
        namespaces=_NS,
    )
    due_val = due_nodes[0].text.strip() if due_nodes and due_nodes[0].text else None
    due_fmt = due_nodes[0].get("format") if due_nodes else "102"

    return Invoice(
        syntax="CII",
        customization_id=t(f"{hdr}/ram:GuidelineSpecifiedDocumentContextParameter/ram:ID") or "",
        profile_id=t(f"{hdr}/ram:BusinessProcessSpecifiedDocumentContextParameter/ram:ID"),
        number=t(f"{doc}/ram:ID") or "",
        issue_date=_parse_cii_date(issue_val, issue_fmt or "102"),
        type_code=t(f"{doc}/ram:TypeCode") or "",
        currency=t(f"{stl}/ram:InvoiceCurrencyCode") or "",
        due_date=_parse_cii_date(due_val, due_fmt or "102"),
        buyer_reference=t(f"{agr}/ram:BuyerReference"),
        purchase_order_ref=t(f"{agr}/ram:BuyerOrderReferencedDocument/ram:IssuerAssignedID"),
        note=t(f"{doc}/ram:IncludedNote/ram:Content"),
        seller=parse_party(f"{agr}/ram:SellerTradeParty"),
        buyer=parse_party(f"{agr}/ram:BuyerTradeParty"),
        lines=lines,
        vat_breakdown=vat_breakdown,
        totals=totals,
    )
