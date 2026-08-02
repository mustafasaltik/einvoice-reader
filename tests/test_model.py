from __future__ import annotations

from decimal import Decimal

import pytest

from core.model import Address, Invoice, Line, Party, Totals, VatBreakdown
from core.rules import validate


def _make_invoice(**overrides) -> Invoice:
    defaults = dict(
        syntax="UBL",
        customization_id="urn:cen.eu:en16931:2017#compliant#urn:xoev-de:kosit:standard:xrechnung_3.0",
        profile_id=None,
        number="INV-001",
        issue_date=__import__("datetime").date(2024, 1, 15),
        type_code="380",
        currency="EUR",
        due_date=None,
        buyer_reference="buyer-ref-1",
        purchase_order_ref=None,
        note=None,
        seller=Party(name="Seller GmbH", vat_id="DE123456789", tax_reg_id=None, address=None),
        buyer=Party(name="Buyer GmbH", vat_id="DE987654321", tax_reg_id=None, address=None),
        lines=[
            Line(
                id="1",
                note=None,
                quantity=Decimal("2"),
                unit="EA",
                net_amount=Decimal("200.00"),
                item_name="Widget",
                item_description=None,
                vat_category="S",
                vat_rate=Decimal("19"),
                unit_price=Decimal("100.00"),
                gross_price=None,
                buyer_accounting_ref=None,
            )
        ],
        vat_breakdown=[
            VatBreakdown(
                taxable_amount=Decimal("200.00"),
                tax_amount=Decimal("38.00"),
                category_code="S",
                rate=Decimal("19"),
                exemption_reason=None,
                exemption_reason_code=None,
            )
        ],
        totals=Totals(
            line_net_total=Decimal("200.00"),
            allowances=Decimal("0"),
            charges=Decimal("0"),
            tax_exclusive=Decimal("200.00"),
            tax_amount=Decimal("38.00"),
            tax_inclusive=Decimal("238.00"),
            prepaid=Decimal("0"),
            rounding=Decimal("0"),
            due=Decimal("238.00"),
        ),
    )
    defaults.update(overrides)
    return Invoice(**defaults)


def test_valid_invoice_passes_all_rules():
    invoice = _make_invoice()
    results = validate(invoice)
    failures = [r for r in results if not r.passed]
    assert not failures, [r.detail for r in failures]


def test_missing_number_fails_br01():
    invoice = _make_invoice(number="")
    results = validate(invoice)
    failed_ids = {r.rule.id for r in results if not r.passed}
    assert "BR-01" in failed_ids


def test_missing_seller_name_fails_br06():
    invoice = _make_invoice(
        seller=Party(name="", vat_id=None, tax_reg_id=None, address=None)
    )
    results = validate(invoice)
    failed_ids = {r.rule.id for r in results if not r.passed}
    assert "BR-06" in failed_ids


def test_br_co_15_catches_wrong_tax_exclusive():
    totals = Totals(
        line_net_total=Decimal("200.00"),
        allowances=Decimal("0"),
        charges=Decimal("0"),
        tax_exclusive=Decimal("999.00"),  # wrong
        tax_amount=Decimal("38.00"),
        tax_inclusive=Decimal("238.00"),
        prepaid=Decimal("0"),
        rounding=Decimal("0"),
        due=Decimal("238.00"),
    )
    invoice = _make_invoice(totals=totals)
    results = validate(invoice)
    failed_ids = {r.rule.id for r in results if not r.passed}
    assert "BR-CO-15" in failed_ids


def test_br_co_16_catches_wrong_tax_inclusive():
    totals = Totals(
        line_net_total=Decimal("200.00"),
        allowances=Decimal("0"),
        charges=Decimal("0"),
        tax_exclusive=Decimal("200.00"),
        tax_amount=Decimal("38.00"),
        tax_inclusive=Decimal("999.00"),  # wrong
        prepaid=Decimal("0"),
        rounding=Decimal("0"),
        due=Decimal("238.00"),
    )
    invoice = _make_invoice(totals=totals)
    results = validate(invoice)
    failed_ids = {r.rule.id for r in results if not r.passed}
    assert "BR-CO-16" in failed_ids
