# E-Invoice Reader

A free web tool that turns an unreadable electronic invoice into something a human can understand.

Upload an XML invoice (XRechnung, Peppol BIS 3.0, NLCIUS) or a ZUGFeRD / Factur-X PDF and get back:

- A plain-language summary of the invoice (parties, dates, amounts, line items)
- A validation report against EN 16931 rules, with plain-language explanations for every failure
- A downloadable PDF copy of the summary

Available in English, German, and Dutch. No account, no storage, no tracking.

Live at **[einvoice-reader.com](https://einvoice-reader.com)**

---

## How it works

```
Upload / paste XML or PDF
        │
        ▼
  core/detect.py          ← detects UBL vs CII; extracts XML from ZUGFeRD PDFs
        │
        ▼
  core/parsers/ubl.py     ← parses UBL Invoice / CreditNote
  core/parsers/cii.py     ← parses CII CrossIndustryInvoice
        │
        ▼
  core/model.py           ← one Invoice dataclass, BT-annotated fields
        │
        ▼
  core/rules.py           ← validates against EN 16931 rule registry
        │
        ▼
  web/routes.py           ← renders result.html or returns PDF
```

`core/` is web-agnostic: input is `bytes`, output is an `Invoice` dataclass. It never imports FastAPI.

---

## Project structure

```
einvoice-reader/
├── core/
│   ├── model.py          # Invoice dataclass with BT-annotated fields
│   ├── detect.py         # Syntax detection + ZUGFeRD PDF extraction
│   ├── exceptions.py     # Typed exceptions for known failure modes
│   ├── rules.py          # EN 16931 validation rule registry (16 rules)
│   ├── pdf.py            # Invoice → PDF bytes (fpdf2, no system deps)
│   └── parsers/
│       ├── ubl.py        # UBL Invoice + CreditNote parser
│       └── cii.py        # CII CrossIndustryInvoice parser
├── web/
│   ├── app.py            # FastAPI factory
│   ├── routes.py         # HTTP routes
│   ├── i18n.py           # EN / DE / NL translation dict
│   ├── seo.py            # SITE_URL env var
│   ├── templating.py     # Jinja2Templates singleton
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── result.html
│       ├── rules_index.html
│       └── rule.html
├── tests/
│   ├── fixtures/
│   │   ├── ubl_invoice.xml   # XRechnung 3.0 UBL test fixture
│   │   └── cii_invoice.xml   # Same invoice in CII syntax
│   ├── test_parsers.py       # 47 parser tests (UBL, CII, equivalence)
│   └── test_model.py         # 14 validation rule tests
└── deploy/
    ├── einvoice-reader.service   # systemd unit
    ├── nginx.conf                # nginx reverse proxy config
    └── setup.sh                  # one-shot server setup script
```

---

## Running locally

**Requirements:** Python 3.10+

```bash
git clone https://github.com/mustafasaltik/einvoice-reader.git
cd einvoice-reader

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

uvicorn web.app:create_app --factory --reload
```

Open [http://localhost:8000](http://localhost:8000).

### Running tests

```bash
pytest
```

Tests run entirely offline — no network, no server. Fixtures in `tests/fixtures/` are real invoice XML files.

---

## Supported formats

| Format | Syntax | Notes |
|--------|--------|-------|
| XRechnung 3.0 | UBL or CII | German public sector standard |
| Peppol BIS 3.0 | UBL | Pan-European B2B standard |
| NLCIUS | UBL | Dutch public sector profile |
| ZUGFeRD 2.x | CII | XML embedded in PDF |
| Factur-X | CII | XML embedded in PDF (French/German) |

Credit notes (`TypeCode 381`) are supported alongside invoices (`TypeCode 380`).

---

## Validation rules

Rules live in `core/rules.py` as a single registry. Each entry has:

- Rule ID (`BR-01`, `BR-CO-15`, …)
- Severity (`fatal` or `warning`)
- Business Terms involved (BT numbers from EN 16931)
- Plain-language message in EN, DE, and NL

Every rule in the registry automatically gets a public detail page at `/rules/{id}`, which is the SEO strategy for this project.

Currently implemented: BR-01, BR-02, BR-03, BR-04, BR-06, BR-07, BR-08, BR-16, BR-32, BR-33, BR-CO-10, BR-CO-11, BR-CO-13, BR-CO-15, BR-CO-16, BR-CO-17.

### Adding a rule

1. Add a `Rule(...)` entry to the `_REGISTRY` list in `core/rules.py`
2. Write a check function `_check_<id>(invoice) -> str | None` — return `None` if the rule passes, or a short detail string if it fails
3. Add the check to `_CHECKS` dict in the same file
4. Add a test in `tests/test_model.py`

That's it. The rule page appears automatically.

---

## Adding a language

1. Add a new locale dict to `_TRANSLATIONS` in `web/i18n.py` — copy the `"en"` block as a template
2. Add the locale code to `_VALID` in the same file
3. Add detection logic to `get_locale()` (Accept-Language header check)
4. Add a language button to the `{% block lang_switcher %}` in `web/templates/base.html`
5. Add the locale to the language switcher override in `web/templates/result.html`
6. Add a label dict entry to `_LABEL` in `core/pdf.py`
7. Add `hreflang` links and sitemap entries — these are generated automatically from `_VALID` if you wire the new locale into `web/routes.py`'s sitemap builder

---

## Security

- XML is parsed with `resolve_entities=False`, `no_network=True`, `load_dtd=False` — no XXE
- Uploaded files are never written to disk and never persisted — parsed in memory, discarded after the response
- Errors are logged without invoice payloads (invoices contain names, addresses, VAT IDs, bank details)

---

## Deploying to a VPS

The `deploy/` directory contains everything needed for a production setup on Ubuntu 24.04 with nginx + systemd + Let's Encrypt.

### Prerequisites

- Ubuntu 24.04 VPS (Hetzner CX22 or equivalent)
- Domain pointing to the server's IP (A records for `@` and `www`)
- Non-root user `einvoice` created on the server

### First-time setup

```bash
# On the server, as root
apt update && apt upgrade -y
apt install -y python3.12 python3.12-venv python3-pip nginx certbot python3-certbot-nginx git

useradd -m -s /bin/bash einvoice

# As the einvoice user
su - einvoice
git clone https://github.com/mustafasaltik/einvoice-reader.git
cd einvoice-reader
python3.12 -m venv .venv
.venv/bin/pip install -e .
exit

# Back as root — run the setup script
bash /home/einvoice/einvoice-reader/deploy/setup.sh
```

The setup script installs the systemd service, configures nginx, and obtains an SSL certificate via certbot.

### Deploying updates

```bash
# On the server, as root
su - einvoice -c "cd einvoice-reader && git pull && .venv/bin/pip install -e . -q"
systemctl restart einvoice-reader
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SITE_URL` | `https://einvoice-reader.com` | Used in sitemap.xml and canonical URLs |

Set in `deploy/einvoice-reader.service` under `Environment=`.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI |
| ASGI server | uvicorn |
| Templates | Jinja2 (server-rendered) |
| Interactivity | HTMX |
| Styling | Tailwind CSS (CDN, no build step) |
| XML parsing | lxml |
| PDF extraction | pypdf |
| PDF generation | fpdf2 |
| Reverse proxy | nginx |
| Process manager | systemd |
| TLS | Let's Encrypt / certbot |

No database. No JavaScript framework. No background workers. No file storage.
