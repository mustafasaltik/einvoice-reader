from __future__ import annotations

import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from core.detect import Syntax, detect_syntax
from core.parsers import ubl, cii
from core.rules import validate

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def ubl_raw() -> bytes:
    return (FIXTURES / "ubl_invoice.xml").read_bytes()


@pytest.fixture(scope="module")
def cii_raw() -> bytes:
    return (FIXTURES / "cii_invoice.xml").read_bytes()


@pytest.fixture(scope="module")
def ubl_invoice(ubl_raw):
    return ubl.parse(ubl_raw)


@pytest.fixture(scope="module")
def cii_invoice(cii_raw):
    return cii.parse(cii_raw)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def test_detect_ubl(ubl_raw):
    assert detect_syntax(ubl_raw) == Syntax.UBL


def test_detect_cii(cii_raw):
    assert detect_syntax(cii_raw) == Syntax.CII


# ---------------------------------------------------------------------------
# UBL parsing
# ---------------------------------------------------------------------------

class TestUBLParsing:
    def test_syntax_tag(self, ubl_invoice):
        assert ubl_invoice.syntax == "UBL"

    def test_number(self, ubl_invoice):
        assert ubl_invoice.number == "RE-2024-001"

    def test_issue_date(self, ubl_invoice):
        assert ubl_invoice.issue_date == datetime.date(2024, 3, 15)

    def test_due_date(self, ubl_invoice):
        assert ubl_invoice.due_date == datetime.date(2024, 4, 14)

    def test_type_code(self, ubl_invoice):
        assert ubl_invoice.type_code == "380"

    def test_currency(self, ubl_invoice):
        assert ubl_invoice.currency == "EUR"

    def test_customization_id(self, ubl_invoice):
        assert "xrechnung_3.0" in ubl_invoice.customization_id

    def test_buyer_reference(self, ubl_invoice):
        assert ubl_invoice.buyer_reference == "BUYER-REF-42"

    def test_purchase_order_ref(self, ubl_invoice):
        assert ubl_invoice.purchase_order_ref == "PO-2024-007"

    def test_seller_name(self, ubl_invoice):
        assert ubl_invoice.seller.name == "Mustermann GmbH"

    def test_seller_vat_id(self, ubl_invoice):
        assert ubl_invoice.seller.vat_id == "DE123456789"

    def test_seller_address(self, ubl_invoice):
        addr = ubl_invoice.seller.address
        assert addr is not None
        assert addr.city == "Berlin"
        assert addr.postcode == "10115"
        assert addr.country == "DE"

    def test_buyer_name(self, ubl_invoice):
        assert ubl_invoice.buyer.name == "Beispiel AG"

    def test_buyer_vat_id(self, ubl_invoice):
        assert ubl_invoice.buyer.vat_id == "DE987654321"

    def test_line_count(self, ubl_invoice):
        assert len(ubl_invoice.lines) == 2

    def test_line1_fields(self, ubl_invoice):
        line = ubl_invoice.lines[0]
        assert line.id == "1"
        assert line.item_name == "Softwareentwicklung"
        assert line.quantity == Decimal("10")
        assert line.unit == "HUR"
        assert line.net_amount == Decimal("500.00")
        assert line.unit_price == Decimal("50.00")
        assert line.vat_category == "S"
        assert line.vat_rate == Decimal("19")

    def test_line2_fields(self, ubl_invoice):
        line = ubl_invoice.lines[1]
        assert line.id == "2"
        assert line.quantity == Decimal("5")
        assert line.unit == "EA"
        assert line.net_amount == Decimal("500.00")

    def test_vat_breakdown(self, ubl_invoice):
        assert len(ubl_invoice.vat_breakdown) == 1
        vb = ubl_invoice.vat_breakdown[0]
        assert vb.category_code == "S"
        assert vb.rate == Decimal("19")
        assert vb.taxable_amount == Decimal("1000.00")
        assert vb.tax_amount == Decimal("190.00")

    def test_totals(self, ubl_invoice):
        t = ubl_invoice.totals
        assert t.line_net_total == Decimal("1000.00")
        assert t.tax_exclusive == Decimal("1000.00")
        assert t.tax_amount == Decimal("190.00")
        assert t.tax_inclusive == Decimal("1190.00")
        assert t.due == Decimal("1190.00")

    def test_all_rules_pass(self, ubl_invoice):
        failures = [r for r in validate(ubl_invoice) if not r.passed]
        assert not failures, [(r.rule.id, r.detail) for r in failures]


# ---------------------------------------------------------------------------
# CII parsing
# ---------------------------------------------------------------------------

class TestCIIParsing:
    def test_syntax_tag(self, cii_invoice):
        assert cii_invoice.syntax == "CII"

    def test_number(self, cii_invoice):
        assert cii_invoice.number == "RE-2024-002"

    def test_issue_date(self, cii_invoice):
        assert cii_invoice.issue_date == datetime.date(2024, 3, 15)

    def test_due_date(self, cii_invoice):
        assert cii_invoice.due_date == datetime.date(2024, 4, 14)

    def test_type_code(self, cii_invoice):
        assert cii_invoice.type_code == "380"

    def test_currency(self, cii_invoice):
        assert cii_invoice.currency == "EUR"

    def test_customization_id(self, cii_invoice):
        assert "xrechnung_3.0" in cii_invoice.customization_id

    def test_buyer_reference(self, cii_invoice):
        assert cii_invoice.buyer_reference == "BUYER-REF-42"

    def test_purchase_order_ref(self, cii_invoice):
        assert cii_invoice.purchase_order_ref == "PO-2024-007"

    def test_note(self, cii_invoice):
        assert "30 Tagen" in cii_invoice.note

    def test_seller_name(self, cii_invoice):
        assert cii_invoice.seller.name == "Mustermann GmbH"

    def test_seller_vat_id(self, cii_invoice):
        assert cii_invoice.seller.vat_id == "DE123456789"

    def test_seller_address(self, cii_invoice):
        addr = cii_invoice.seller.address
        assert addr is not None
        assert addr.city == "Berlin"
        assert addr.postcode == "10115"
        assert addr.country == "DE"

    def test_buyer_name(self, cii_invoice):
        assert cii_invoice.buyer.name == "Beispiel AG"

    def test_buyer_vat_id(self, cii_invoice):
        assert cii_invoice.buyer.vat_id == "DE987654321"

    def test_line_count(self, cii_invoice):
        assert len(cii_invoice.lines) == 2

    def test_line1_fields(self, cii_invoice):
        line = cii_invoice.lines[0]
        assert line.id == "1"
        assert line.item_name == "Softwareentwicklung"
        assert line.quantity == Decimal("10")
        assert line.unit == "HUR"
        assert line.net_amount == Decimal("500.00")
        assert line.unit_price == Decimal("50.00")
        assert line.vat_category == "S"
        assert line.vat_rate == Decimal("19")

    def test_line2_fields(self, cii_invoice):
        line = cii_invoice.lines[1]
        assert line.id == "2"
        assert line.quantity == Decimal("5")
        assert line.unit == "EA"
        assert line.net_amount == Decimal("500.00")

    def test_vat_breakdown(self, cii_invoice):
        assert len(cii_invoice.vat_breakdown) == 1
        vb = cii_invoice.vat_breakdown[0]
        assert vb.category_code == "S"
        assert vb.rate == Decimal("19")
        assert vb.taxable_amount == Decimal("1000.00")
        assert vb.tax_amount == Decimal("190.00")

    def test_totals(self, cii_invoice):
        t = cii_invoice.totals
        assert t.line_net_total == Decimal("1000.00")
        assert t.tax_exclusive == Decimal("1000.00")
        assert t.tax_amount == Decimal("190.00")
        assert t.tax_inclusive == Decimal("1190.00")
        assert t.due == Decimal("1190.00")

    def test_all_rules_pass(self, cii_invoice):
        failures = [r for r in validate(cii_invoice) if not r.passed]
        assert not failures, [(r.rule.id, r.detail) for r in failures]


# ---------------------------------------------------------------------------
# Both parsers produce semantically equivalent output for the same invoice
# ---------------------------------------------------------------------------

class TestUBLCIIEquivalence:
    def test_same_number(self, ubl_invoice, cii_invoice):
        # different fixture invoice numbers by design; check shared fields instead
        assert ubl_invoice.type_code == cii_invoice.type_code
        assert ubl_invoice.currency == cii_invoice.currency
        assert ubl_invoice.issue_date == cii_invoice.issue_date
        assert ubl_invoice.due_date == cii_invoice.due_date

    def test_same_seller(self, ubl_invoice, cii_invoice):
        assert ubl_invoice.seller.name == cii_invoice.seller.name
        assert ubl_invoice.seller.vat_id == cii_invoice.seller.vat_id

    def test_same_totals(self, ubl_invoice, cii_invoice):
        assert ubl_invoice.totals.tax_inclusive == cii_invoice.totals.tax_inclusive
        assert ubl_invoice.totals.due == cii_invoice.totals.due

    def test_same_line_count(self, ubl_invoice, cii_invoice):
        assert len(ubl_invoice.lines) == len(cii_invoice.lines)
