# CLAUDE.md

Project context for Claude Code. Read this before proposing changes.

---

## What this is

A free web tool that takes an unreadable electronic invoice (XML or a
ZUGFeRD/Factur-X PDF) and returns two things:

1. A **human-readable summary** of the invoice.
2. A **plain-language validation report** — not raw Schematron output.

Target user: a small business owner in Germany, Belgium or the Netherlands who
received an `.xml` file from a supplier and cannot open it. They are not
technical. They do not know what UBL is. They should never see a stack trace,
an XPath, or a bare rule code without an explanation next to it.

Distribution is SEO. That is the whole go-to-market. Every decision that trades
page-load speed or crawlability for client-side cleverness is the wrong call.

---

## Non-negotiable architecture rules

### 1. `core/` must not know that a web server exists

`core/` never imports FastAPI, never sees a `Request`, never returns a
`Response`. Input is `bytes`, output is an `Invoice` dataclass.

**Why:** the same parsing logic will later be called from an email intake
worker, a batch job, a public API and a CLI. If web types leak into `core/`,
every one of those becomes a rewrite. This rule is the difference between one
product and four codebases.

If you need something from the request (locale, filename), pass it as a plain
argument.

### 2. UBL and CII are two syntaxes for one semantic model

EN 16931 defines the *semantics*. UBL (Peppol BIS 3.0, XRechnung-UBL, NLCIUS)
and CII (ZUGFeRD, Factur-X, XRechnung-CII) are two *syntaxes* that carry it.

There are two parsers. There is **one** `Invoice` model. Everything downstream
— validation, rendering, PDF output, future API — operates on the model and
never touches XML again.

**Why:** if validation branches on syntax, every business rule gets written
twice and they drift. One model means one implementation of every rule.

**Never** add a syntax-specific field to `Invoice`. If UBL has something CII
doesn't, either it maps to an existing Business Term or it doesn't belong in
the model.

### 3. Model fields carry their Business Term (BT) number

Every field in `core/model.py` is annotated with its EN 16931 BT id
(`number` → BT-1, `totals.tax_inclusive` → BT-112, and so on).

**Why:** BT numbers are the shared vocabulary across the model, the validation
rules, the user-facing error messages, and the public rule pages that will
carry our SEO. When a rule says "BT-112 must equal BT-109 + BT-110", it must be
trivially obvious which fields that is.

Keep the annotations in sync. If you add a field, find its BT number first. If
it has no BT number, question whether it belongs.

### 4. Validation rules live in a registry, not scattered in code

`core/rules.py` holds a single registry of rules. Each entry carries: rule id
(`BR-CO-15`), severity, the BT ids involved, and a plain-language explanation
per locale.

**Why:** this registry is not only the validation engine — it is also the
content source for the generated rule pages, which are the SEO strategy. One
rule added = one validation check + one indexable page, automatically.

Never hardcode an error message at a call site.

---

## v1 scope — what NOT to build

This list exists because scope creep is the most likely way this project dies.
The budget is roughly 40 hours of build. Do not propose anything below.

- ❌ User accounts, login, sessions
- ❌ Database of any kind
- ❌ Storing uploaded files
- ❌ Batch / multi-file upload
- ❌ Public API
- ❌ Sending invoices (Peppol, email dispatch)
- ❌ Archiving
- ❌ Payments or billing
- ❌ Background workers, queues, Celery
- ❌ A JavaScript framework

If a task seems to need one of these, the task is out of scope. Say so instead
of building it.

**In scope for v1:** upload/paste → detect syntax → parse → render summary →
validate → explain errors → download PDF. German and English UI. Nothing else.

---

## Domain notes you cannot infer from the code

- **CustomizationID (BT-24)** identifies which ruleset applies (XRechnung,
  Peppol BIS, NLCIUS, Factur-X profile). It is how a receiver knows what they
  are looking at. Always surface it.
- **CII dates** are not ISO. They come with a UNTDID 2379 format code, almost
  always `102` = `YYYYMMDD`. Do not assume `fromisoformat` works.
- **Credit notes** in UBL use different element names (`CreditNoteLine`,
  `CreditedQuantity`, `CreditNoteTypeCode`) and a different root namespace.
  Handle them; do not crash on them.
- **VAT breakdown (BG-23)** is per category+rate combination, not per line. A
  three-line invoice with two VAT rates has two breakdown groups.
- **Type code 380** = commercial invoice, **381** = credit note. These come
  from UNTDID 1001.
- **A PDF is not an e-invoice.** ZUGFeRD/Factur-X are PDFs with XML embedded as
  an attachment — we extract the XML and parse that. The PDF's visual content
  is never the source of truth.
- Amounts must be handled as `Decimal`, never `float`. Rounding differences are
  exactly what the arithmetic rules (BR-CO-*) detect, so introducing float
  error would produce false validation failures.

---

## Conventions

- Python 3.11+, standard library plus: `fastapi`, `uvicorn`, `jinja2`,
  `python-multipart`, `lxml`, `pypdf`.
- **Ask before adding any dependency.** Small dependency surface is deliberate:
  this runs on one small VPS and must stay easy to reason about.
- Type hints everywhere in `core/`. `from __future__ import annotations` at the
  top of each module.
- Dataclasses for the model. No ORM, no pydantic in `core/` (pydantic is fine
  at the FastAPI boundary if genuinely useful).
- Server-rendered Jinja2 templates. HTMX for interactivity. Tailwind for
  styling. No React, no build step.
- Tests for `core/` are non-negotiable and must run without a network or a
  server. Fixtures live in `tests/fixtures/` as real invoice XML.

---

## Security rules

- **XML is untrusted input.** Users paste files that arrived from strangers.
  The parser must always run with entity resolution off, DTD loading off, and
  network access off. Never relax this "just for debugging".
- **Uploaded files are never written to disk and never persisted.** Parse in
  memory, return the result, discard. This is both a privacy promise made on
  the landing page and the reason we carry almost no GDPR burden. Do not add
  logging that writes invoice contents.
- Log errors without payloads. An invoice contains names, addresses, VAT ids
  and bank details.
- No secrets in the repo. `.env` is gitignored. If you ever see a key in a
  file, stop and flag it.

---

## How to work with me

- **Do not expand scope.** If you think something is missing, say it in one
  sentence and let me decide. Do not implement it speculatively.
- Prefer the boring solution. This project is maintained one hour a day;
  cleverness I have to re-learn later is a liability.
- When a change spans several files, show the plan before writing code.
- If a decision in this file seems wrong given something you have found in the
  code, say so explicitly rather than silently working around it.
- I am a data engineer. Assume fluency in Python, SQL, data modelling and XML.
  Do not explain those. Do explain FastAPI, Jinja and frontend conventions.
