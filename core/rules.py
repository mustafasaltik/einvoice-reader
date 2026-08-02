from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class Severity(str, Enum):
    FATAL = "fatal"    # BR-* rules: invoice is invalid
    WARNING = "warning"  # PEPPOL-EN16931-R* advisory rules


@dataclass(frozen=True)
class Rule:
    id: str                        # e.g. "BR-01", "BR-CO-15"
    severity: Severity
    bt_ids: tuple[str, ...]        # BT numbers involved, e.g. ("BT-1",)
    message: dict[str, str]        # locale → plain-language explanation
    # slug is derived from id for URL generation
    @property
    def slug(self) -> str:
        return self.id.lower()


@dataclass
class ValidationResult:
    rule: Rule
    passed: bool
    detail: str | None = None      # computed value or offending field, never raw XPath


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

RULES: list[Rule] = [
    Rule(
        id="BR-01",
        severity=Severity.FATAL,
        bt_ids=("BT-1",),
        message={
            "en": "The invoice must have an invoice number (BT-1).",
            "de": "Die Rechnung muss eine Rechnungsnummer enthalten (BT-1).",
        },
    ),
    Rule(
        id="BR-02",
        severity=Severity.FATAL,
        bt_ids=("BT-2",),
        message={
            "en": "The invoice must have an issue date (BT-2).",
            "de": "Die Rechnung muss ein Ausstellungsdatum enthalten (BT-2).",
        },
    ),
    Rule(
        id="BR-04",
        severity=Severity.FATAL,
        bt_ids=("BT-5",),
        message={
            "en": "The invoice must specify a currency code (BT-5).",
            "de": "Die Rechnung muss einen Währungscode enthalten (BT-5).",
        },
    ),
    Rule(
        id="BR-06",
        severity=Severity.FATAL,
        bt_ids=("BT-27",),
        message={
            "en": "The seller must have a name (BT-27).",
            "de": "Der Verkäufer muss einen Namen enthalten (BT-27).",
        },
    ),
    Rule(
        id="BR-07",
        severity=Severity.FATAL,
        bt_ids=("BT-44",),
        message={
            "en": "The buyer must have a name (BT-44).",
            "de": "Der Käufer muss einen Namen enthalten (BT-44).",
        },
    ),
    Rule(
        id="BR-CO-15",
        severity=Severity.FATAL,
        bt_ids=("BT-112", "BT-109", "BT-110"),
        message={
            "en": (
                "Invoice total without VAT (BT-112) must equal "
                "the sum of line net amounts (BT-106) minus allowances (BT-107) "
                "plus charges (BT-108)."
            ),
            "de": (
                "Rechnungsbetrag ohne MwSt. (BT-112) muss gleich der Summe der "
                "Nettobeiträge der Rechnungspositionen (BT-106) abzüglich "
                "Nachlässe (BT-107) plus Abgaben (BT-108) sein."
            ),
        },
    ),
    Rule(
        id="BR-CO-16",
        severity=Severity.FATAL,
        bt_ids=("BT-112", "BT-115", "BT-110"),
        message={
            "en": (
                "Invoice total with VAT (BT-115) must equal "
                "invoice total without VAT (BT-112) plus total VAT amount (BT-110)."
            ),
            "de": (
                "Rechnungsbetrag mit MwSt. (BT-115) muss gleich dem "
                "Rechnungsbetrag ohne MwSt. (BT-112) plus Gesamtbetrag der "
                "MwSt. (BT-110) sein."
            ),
        },
    ),
]

RULES_BY_ID: dict[str, Rule] = {r.id: r for r in RULES}


def validate(invoice: "Invoice") -> list[ValidationResult]:  # noqa: F821
    """Run all rules against *invoice* and return a list of results."""
    from core.model import Invoice  # local import avoids circular at module level

    results: list[ValidationResult] = []

    for rule in RULES:
        result = _run(rule, invoice)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Per-rule check implementations
# ---------------------------------------------------------------------------

def _run(rule: Rule, inv: object) -> ValidationResult:
    fn = _CHECKS.get(rule.id)
    if fn is None:
        # Rule defined but check not yet implemented — treat as passed
        return ValidationResult(rule=rule, passed=True, detail="(check not yet implemented)")
    try:
        detail = fn(inv)
        return ValidationResult(rule=rule, passed=detail is None, detail=detail)
    except Exception as exc:
        return ValidationResult(rule=rule, passed=False, detail=str(exc))


def _check_br01(inv) -> str | None:
    return None if inv.number and inv.number.strip() else "Invoice number is missing or blank."


def _check_br02(inv) -> str | None:
    return None if inv.issue_date else "Issue date is missing."


def _check_br04(inv) -> str | None:
    return None if inv.currency and inv.currency.strip() else "Currency code is missing."


def _check_br06(inv) -> str | None:
    return None if inv.seller.name and inv.seller.name.strip() else "Seller name is missing."


def _check_br07(inv) -> str | None:
    return None if inv.buyer.name and inv.buyer.name.strip() else "Buyer name is missing."


def _check_br_co_15(inv) -> str | None:
    if inv.totals is None:
        return "Totals are missing."
    t = inv.totals
    expected = t.line_net_total - t.allowances + t.charges
    if expected != t.tax_exclusive:
        return (
            f"Expected BT-112 = {expected}; actual = {t.tax_exclusive}. "
            f"(BT-106={t.line_net_total}, BT-107={t.allowances}, BT-108={t.charges})"
        )
    return None


def _check_br_co_16(inv) -> str | None:
    if inv.totals is None:
        return "Totals are missing."
    t = inv.totals
    expected = t.tax_exclusive + t.tax_amount
    if expected != t.tax_inclusive:
        return (
            f"Expected BT-115 = {expected}; actual = {t.tax_inclusive}. "
            f"(BT-112={t.tax_exclusive}, BT-110={t.tax_amount})"
        )
    return None


_CHECKS: dict[str, object] = {
    "BR-01": _check_br01,
    "BR-02": _check_br02,
    "BR-04": _check_br04,
    "BR-06": _check_br06,
    "BR-07": _check_br07,
    "BR-CO-15": _check_br_co_15,
    "BR-CO-16": _check_br_co_16,
}
