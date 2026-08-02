from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class Address:
    street: str | None       # BT-35 (seller) / BT-50 (buyer)
    city: str | None         # BT-37 (seller) / BT-52 (buyer)
    postcode: str | None     # BT-38 (seller) / BT-53 (buyer)
    country: str             # BT-40 (seller) / BT-55 (buyer)


@dataclass
class Party:
    name: str                # BT-27 (seller) / BT-44 (buyer)
    vat_id: str | None       # BT-31 (seller) / BT-46 (buyer)
    tax_reg_id: str | None   # BT-32 (seller) / BT-47 (buyer)
    address: Address | None


@dataclass
class VatBreakdown:          # BG-23
    taxable_amount: Decimal  # BT-116
    tax_amount: Decimal      # BT-117
    category_code: str       # BT-118
    rate: Decimal | None     # BT-119
    exemption_reason: str | None       # BT-120
    exemption_reason_code: str | None  # BT-121


@dataclass
class Totals:                # BG-22
    line_net_total: Decimal  # BT-106 Sum of line net amounts
    allowances: Decimal      # BT-107 Sum of allowances on document level
    charges: Decimal         # BT-108 Sum of charges on document level
    tax_exclusive: Decimal   # BT-109 Invoice total amount without VAT
    tax_amount: Decimal      # BT-110 Invoice total VAT amount
    tax_inclusive: Decimal   # BT-112 Invoice total amount with VAT
    prepaid: Decimal         # BT-113 Paid amount
    rounding: Decimal        # BT-114 Rounding amount
    due: Decimal             # BT-115 Amount due for payment


@dataclass
class Line:                          # BG-25
    id: str                          # BT-126
    note: str | None                 # BT-127
    quantity: Decimal                # BT-129
    unit: str                        # BT-130
    net_amount: Decimal              # BT-131
    item_name: str                   # BT-153
    item_description: str | None     # BT-154
    vat_category: str                # BT-151
    vat_rate: Decimal | None         # BT-152
    unit_price: Decimal | None       # BT-146
    gross_price: Decimal | None      # BT-148
    buyer_accounting_ref: str | None # BT-133


@dataclass
class Invoice:
    # Administrative
    syntax: str                  # "UBL" | "CII" — not a BT, internal routing only
    customization_id: str        # BT-24 identifies the ruleset (XRechnung, Peppol, NLCIUS, Factur-X)
    profile_id: str | None       # BT-23
    number: str                  # BT-1
    issue_date: date             # BT-2
    type_code: str               # BT-3  380 = invoice, 381 = credit note (UNTDID 1001)
    currency: str                # BT-5
    due_date: date | None        # BT-9
    buyer_reference: str | None  # BT-10
    purchase_order_ref: str | None  # BT-13
    note: str | None             # BT-22

    # Parties
    seller: Party                # BG-4
    buyer: Party                 # BG-7

    # Lines and breakdown
    lines: list[Line] = field(default_factory=list)              # BG-25
    vat_breakdown: list[VatBreakdown] = field(default_factory=list)  # BG-23
    totals: Totals | None = None  # BG-22
