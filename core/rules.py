from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


class Severity(str, Enum):
    FATAL = "fatal"      # BR-* rules: invoice is invalid
    WARNING = "warning"  # PEPPOL-EN16931-R* advisory rules


@dataclass(frozen=True)
class Rule:
    id: str                   # e.g. "BR-01", "BR-CO-15"
    severity: Severity
    bt_ids: tuple[str, ...]   # BT numbers involved
    message: dict[str, str]   # locale → plain-language explanation

    @property
    def slug(self) -> str:
        return self.id.lower()


@dataclass
class ValidationResult:
    rule: Rule
    passed: bool
    detail: str | None = None  # computed value or offending field, never raw XPath


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

RULES: list[Rule] = [
    # ── Mandatory fields ────────────────────────────────────────────────
    Rule(
        id="BR-01",
        severity=Severity.FATAL,
        bt_ids=("BT-1",),
        message={
            "en": "The invoice must have an invoice number (BT-1).",
            "de": "Die Rechnung muss eine Rechnungsnummer enthalten (BT-1).",
            "nl": "De factuur moet een factuurnummer bevatten (BT-1).",
        },
    ),
    Rule(
        id="BR-02",
        severity=Severity.FATAL,
        bt_ids=("BT-2",),
        message={
            "en": "The invoice must have an issue date (BT-2).",
            "de": "Die Rechnung muss ein Ausstellungsdatum enthalten (BT-2).",
            "nl": "De factuur moet een factuurdatum bevatten (BT-2).",
        },
    ),
    Rule(
        id="BR-03",
        severity=Severity.FATAL,
        bt_ids=("BT-3",),
        message={
            "en": "The invoice must specify a document type code (BT-3).",
            "de": "Die Rechnung muss einen Dokumenttypcode enthalten (BT-3).",
            "nl": "De factuur moet een documenttypecode bevatten (BT-3).",
        },
    ),
    Rule(
        id="BR-04",
        severity=Severity.FATAL,
        bt_ids=("BT-5",),
        message={
            "en": "The invoice must specify a currency code (BT-5).",
            "de": "Die Rechnung muss einen Währungscode enthalten (BT-5).",
            "nl": "De factuur moet een valutacode bevatten (BT-5).",
        },
    ),
    Rule(
        id="BR-06",
        severity=Severity.FATAL,
        bt_ids=("BT-27",),
        message={
            "en": "The seller must have a name (BT-27).",
            "de": "Der Verkäufer muss einen Namen enthalten (BT-27).",
            "nl": "De verkoper moet een naam bevatten (BT-27).",
        },
    ),
    Rule(
        id="BR-07",
        severity=Severity.FATAL,
        bt_ids=("BT-44",),
        message={
            "en": "The buyer must have a name (BT-44).",
            "de": "Der Käufer muss einen Namen enthalten (BT-44).",
            "nl": "De koper moet een naam bevatten (BT-44).",
        },
    ),
    Rule(
        id="BR-08",
        severity=Severity.FATAL,
        bt_ids=("BT-31", "BT-32"),
        message={
            "en": (
                "The seller must have a VAT identifier (BT-31) "
                "or tax registration identifier (BT-32)."
            ),
            "de": (
                "Der Verkäufer muss eine Umsatzsteuer-Identifikationsnummer (BT-31) "
                "oder Steuerregistrierungsnummer (BT-32) angeben."
            ),
            "nl": (
                "De verkoper moet een BTW-identificatienummer (BT-31) "
                "of fiscaal registratienummer (BT-32) opgeven."
            ),
        },
    ),
    Rule(
        id="BR-16",
        severity=Severity.FATAL,
        bt_ids=("BG-25",),
        message={
            "en": "The invoice must contain at least one invoice line (BG-25).",
            "de": "Die Rechnung muss mindestens eine Rechnungsposition (BG-25) enthalten.",
            "nl": "De factuur moet minimaal één factuurregel (BG-25) bevatten.",
        },
    ),
    # ── Line-level mandatory fields ──────────────────────────────────────
    Rule(
        id="BR-32",
        severity=Severity.FATAL,
        bt_ids=("BT-153",),
        message={
            "en": "Each invoice line must contain an item name (BT-153).",
            "de": "Jede Rechnungsposition muss einen Artikelnamen (BT-153) enthalten.",
            "nl": "Elke factuurregel moet een artikelnaam (BT-153) bevatten.",
        },
    ),
    Rule(
        id="BR-33",
        severity=Severity.FATAL,
        bt_ids=("BT-151",),
        message={
            "en": "Each invoice line must contain a VAT category code (BT-151).",
            "de": "Jede Rechnungsposition muss einen MwSt.-Kategoriecode (BT-151) enthalten.",
            "nl": "Elke factuurregel moet een BTW-categoriecode (BT-151) bevatten.",
        },
    ),
    # ── Document-level arithmetic ────────────────────────────────────────
    Rule(
        id="BR-CO-15",
        severity=Severity.FATAL,
        bt_ids=("BT-109", "BT-106", "BT-107", "BT-108"),
        message={
            "en": (
                "Invoice total without VAT (BT-109) must equal "
                "the sum of line net amounts (BT-106) "
                "minus document allowances (BT-107) "
                "plus document charges (BT-108)."
            ),
            "de": (
                "Rechnungsbetrag ohne MwSt. (BT-109) muss der Summe der "
                "Nettobeiträge der Rechnungspositionen (BT-106) abzüglich "
                "Nachlässe (BT-107) plus Abgaben (BT-108) entsprechen."
            ),
            "nl": (
                "Factuurbedrag exclusief BTW (BT-109) moet gelijk zijn aan "
                "de som van nettobedragen van factuurregels (BT-106) "
                "minus kortingen (BT-107) plus toeslagen (BT-108)."
            ),
        },
    ),
    Rule(
        id="BR-CO-16",
        severity=Severity.FATAL,
        bt_ids=("BT-112", "BT-109", "BT-110"),
        message={
            "en": (
                "Invoice total with VAT (BT-112) must equal "
                "invoice total without VAT (BT-109) "
                "plus total VAT amount (BT-110)."
            ),
            "de": (
                "Rechnungsbetrag mit MwSt. (BT-112) muss dem "
                "Rechnungsbetrag ohne MwSt. (BT-109) plus "
                "Gesamtbetrag der MwSt. (BT-110) entsprechen."
            ),
            "nl": (
                "Factuurbedrag inclusief BTW (BT-112) moet gelijk zijn aan "
                "het factuurbedrag exclusief BTW (BT-109) "
                "plus het totale BTW-bedrag (BT-110)."
            ),
        },
    ),
    Rule(
        id="BR-CO-17",
        severity=Severity.FATAL,
        bt_ids=("BT-115", "BT-112", "BT-113", "BT-114"),
        message={
            "en": (
                "Amount due for payment (BT-115) must equal "
                "invoice total with VAT (BT-112) "
                "minus prepaid amount (BT-113) "
                "plus rounding amount (BT-114)."
            ),
            "de": (
                "Fälliger Betrag (BT-115) muss dem Rechnungsbetrag mit MwSt. "
                "(BT-112) abzüglich Vorauszahlung (BT-113) plus "
                "Rundungsbetrag (BT-114) entsprechen."
            ),
            "nl": (
                "Te betalen bedrag (BT-115) moet gelijk zijn aan "
                "factuurbedrag inclusief BTW (BT-112) "
                "minus vooruitbetaald bedrag (BT-113) "
                "plus afrondingsbedrag (BT-114)."
            ),
        },
    ),
    # ── VAT breakdown arithmetic ─────────────────────────────────────────
    Rule(
        id="BR-CO-10",
        severity=Severity.FATAL,
        bt_ids=("BT-110", "BT-117"),
        message={
            "en": (
                "The sum of all VAT category tax amounts (BT-117) "
                "must equal the invoice total VAT amount (BT-110)."
            ),
            "de": (
                "Die Summe aller MwSt.-Kategoriesteuerbeträge (BT-117) muss "
                "dem Gesamtbetrag der MwSt. der Rechnung (BT-110) entsprechen."
            ),
            "nl": (
                "De som van alle BTW-categoriebedragen (BT-117) "
                "moet gelijk zijn aan het totale BTW-bedrag van de factuur (BT-110)."
            ),
        },
    ),
    Rule(
        id="BR-CO-11",
        severity=Severity.FATAL,
        bt_ids=("BT-109", "BT-116"),
        message={
            "en": (
                "The sum of all VAT category taxable amounts (BT-116) "
                "must equal the invoice total amount without VAT (BT-109)."
            ),
            "de": (
                "Die Summe aller MwSt.-Kategorie-Steuerbemessungsgrundlagen (BT-116) "
                "muss dem Rechnungsgesamtbetrag ohne MwSt. (BT-109) entsprechen."
            ),
            "nl": (
                "De som van alle BTW-categorie belastbare bedragen (BT-116) "
                "moet gelijk zijn aan het factuurbedrag exclusief BTW (BT-109)."
            ),
        },
    ),
    Rule(
        id="BR-CO-13",
        severity=Severity.FATAL,
        bt_ids=("BT-117", "BT-116", "BT-119"),
        message={
            "en": (
                "For a standard-rated VAT category (S), the VAT category tax amount "
                "(BT-117) must equal the taxable amount (BT-116) "
                "multiplied by the VAT rate (BT-119) divided by 100, "
                "rounded to two decimal places."
            ),
            "de": (
                "Für eine MwSt.-Kategorie mit Normalsatz (S) muss der "
                "MwSt.-Kategoriesteuerbetrag (BT-117) dem steuerpflichtigen Betrag "
                "(BT-116) multipliziert mit dem MwSt.-Satz (BT-119) geteilt durch "
                "100, gerundet auf zwei Dezimalstellen, entsprechen."
            ),
            "nl": (
                "Voor een standaard BTW-categorie (S) moet het BTW-categoriebedrag "
                "(BT-117) gelijk zijn aan het belastbare bedrag (BT-116) "
                "vermenigvuldigd met het BTW-tarief (BT-119) gedeeld door 100, "
                "afgerond op twee decimalen."
            ),
        },
    ),
]

RULES_BY_ID: dict[str, Rule] = {r.id: r for r in RULES}


def validate(invoice: object) -> list[ValidationResult]:
    """Run all rules against *invoice* and return a list of results."""
    results: list[ValidationResult] = []
    for rule in RULES:
        results.append(_run(rule, invoice))
    return results


# ---------------------------------------------------------------------------
# Per-rule check implementations
# ---------------------------------------------------------------------------

def _run(rule: Rule, inv: object) -> ValidationResult:
    fn = _CHECKS.get(rule.id)
    if fn is None:
        return ValidationResult(rule=rule, passed=True, detail="(check not yet implemented)")
    try:
        detail = fn(inv)
        return ValidationResult(rule=rule, passed=detail is None, detail=detail)
    except Exception as exc:
        return ValidationResult(rule=rule, passed=False, detail=str(exc))


def _check_br01(inv) -> str | None:
    return None if inv.number and inv.number.strip() else "Invoice number (BT-1) is missing or blank."


def _check_br02(inv) -> str | None:
    return None if inv.issue_date else "Issue date (BT-2) is missing."


def _check_br03(inv) -> str | None:
    return None if inv.type_code and inv.type_code.strip() else "Document type code (BT-3) is missing."


def _check_br04(inv) -> str | None:
    return None if inv.currency and inv.currency.strip() else "Currency code (BT-5) is missing."


def _check_br06(inv) -> str | None:
    return None if inv.seller.name and inv.seller.name.strip() else "Seller name (BT-27) is missing."


def _check_br07(inv) -> str | None:
    return None if inv.buyer.name and inv.buyer.name.strip() else "Buyer name (BT-44) is missing."


def _check_br08(inv) -> str | None:
    if inv.seller.vat_id or inv.seller.tax_reg_id:
        return None
    return "Seller must have a VAT identifier (BT-31) or tax registration identifier (BT-32)."


def _check_br16(inv) -> str | None:
    return None if inv.lines else "Invoice must contain at least one line (BG-25)."


def _check_br32(inv) -> str | None:
    bad = [ln.id for ln in inv.lines if not (ln.item_name and ln.item_name.strip())]
    return f"Lines missing item name (BT-153): {', '.join(bad)}." if bad else None


def _check_br33(inv) -> str | None:
    bad = [ln.id for ln in inv.lines if not (ln.vat_category and ln.vat_category.strip())]
    return f"Lines missing VAT category code (BT-151): {', '.join(bad)}." if bad else None


def _check_br_co_10(inv) -> str | None:
    if inv.totals is None:
        return "Totals are missing."
    total_vat = sum((vb.tax_amount for vb in inv.vat_breakdown), Decimal("0"))
    if total_vat != inv.totals.tax_amount:
        return (
            f"Sum of BT-117 = {total_vat}; BT-110 = {inv.totals.tax_amount}. "
            f"Difference: {total_vat - inv.totals.tax_amount}."
        )
    return None


def _check_br_co_11(inv) -> str | None:
    if inv.totals is None:
        return "Totals are missing."
    total_taxable = sum((vb.taxable_amount for vb in inv.vat_breakdown), Decimal("0"))
    if total_taxable != inv.totals.tax_exclusive:
        return (
            f"Sum of BT-116 = {total_taxable}; BT-109 = {inv.totals.tax_exclusive}. "
            f"Difference: {total_taxable - inv.totals.tax_exclusive}."
        )
    return None


def _check_br_co_13(inv) -> str | None:
    for vb in inv.vat_breakdown:
        if vb.category_code != "S":
            continue
        if vb.rate is None:
            return f"Standard-rated VAT breakdown is missing the rate (BT-119)."
        expected = (vb.taxable_amount * vb.rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if expected != vb.tax_amount:
            return (
                f"BT-117 = {vb.tax_amount} but BT-116 ({vb.taxable_amount}) "
                f"× BT-119 ({vb.rate}%) / 100 = {expected}."
            )
    return None


def _check_br_co_15(inv) -> str | None:
    if inv.totals is None:
        return "Totals are missing."
    t = inv.totals
    expected = t.line_net_total - t.allowances + t.charges
    if expected != t.tax_exclusive:
        return (
            f"Expected BT-109 = {expected}; actual = {t.tax_exclusive}. "
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
            f"Expected BT-112 = {expected}; actual = {t.tax_inclusive}. "
            f"(BT-109={t.tax_exclusive}, BT-110={t.tax_amount})"
        )
    return None


def _check_br_co_17(inv) -> str | None:
    if inv.totals is None:
        return "Totals are missing."
    t = inv.totals
    expected = t.tax_inclusive - t.prepaid + t.rounding
    if expected != t.due:
        return (
            f"Expected BT-115 = {expected}; actual = {t.due}. "
            f"(BT-112={t.tax_inclusive}, BT-113={t.prepaid}, BT-114={t.rounding})"
        )
    return None


_CHECKS: dict[str, object] = {
    "BR-01":    _check_br01,
    "BR-02":    _check_br02,
    "BR-03":    _check_br03,
    "BR-04":    _check_br04,
    "BR-06":    _check_br06,
    "BR-07":    _check_br07,
    "BR-08":    _check_br08,
    "BR-16":    _check_br16,
    "BR-32":    _check_br32,
    "BR-33":    _check_br33,
    "BR-CO-10": _check_br_co_10,
    "BR-CO-11": _check_br_co_11,
    "BR-CO-13": _check_br_co_13,
    "BR-CO-15": _check_br_co_15,
    "BR-CO-16": _check_br_co_16,
    "BR-CO-17": _check_br_co_17,
}
