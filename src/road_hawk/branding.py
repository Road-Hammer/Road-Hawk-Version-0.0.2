"""Road Hawk branding and copyright constants."""

COMPANY_SHORT = "STWL"
COMPANY_LEGAL = "Susquehanna Timberwolf Lines LLC"
BRAND = "Road Hammer"
PRODUCT = "Road Hawk"
TAGLINE = "Built by a trucker, for truckers."
COPYRIGHT_YEAR = 2026
COPYRIGHT_NOTICE = f"© {COPYRIGHT_YEAR} {COMPANY_LEGAL}. All rights reserved."
PRODUCT_LINE = f"{PRODUCT}™ — a {BRAND}™ product."

CONTACT_ORGANIZATIONS = "Susquehanna Timberwolf Lines, LLC / That Dam BBS!, Inc."
CONTACT_LOCATION = "Montrose, PA — USA"
CONTACT_TIMEZONE = "America/New_York"
CONTACT_TIMEZONE_LABEL = "UTC-04:00"
CONTACT_EMAIL = "office@thatdambbs.com"
CONTACT_PHONE = "570-442-0273"
CONTACT_PHONE_URL = "tel:+15704420273"
CONTACT_HOURS = (
    "11am to 8pm Eastern, Monday to Friday. Closed weekends and federal holidays."
)
CONTACT_WEBSITE = "https://www.thatdambbs.com"

CONTACT_LINKS: list[dict[str, str]] = [
    {"label": "Website", "url": CONTACT_WEBSITE, "display": "www.thatdambbs.com"},
    {"label": "Email", "url": f"mailto:{CONTACT_EMAIL}", "display": CONTACT_EMAIL},
    {"label": "Phone", "url": CONTACT_PHONE_URL, "display": CONTACT_PHONE},
    {"label": "GitHub", "url": "https://github.com/Road-Hammer", "display": "github.com/Road-Hammer"},
    {"label": "Telegram", "url": "https://t.me/NEPA_BBS", "display": "t.me/NEPA_BBS"},
    {
        "label": "LinkedIn",
        "url": "https://www.linkedin.com/in/roadhammer",
        "display": "in/roadhammer",
    },
    {
        "label": "Facebook",
        "url": "https://www.facebook.com/profile.php?id=61578962531585",
        "display": "Facebook",
    },
    {
        "label": "YouTube",
        "url": "https://www.youtube.com/@1stRoadhammer",
        "display": "YouTube",
    },
    {"label": "X", "url": "https://x.com/1stRoadhammer", "display": "X"},
]

TRADEMARK_FOOTER_SHORT = (
    f"{COPYRIGHT_NOTICE}\n"
    f"{PRODUCT}™ and {BRAND}™ are trademarks/service marks claimed by {COMPANY_LEGAL}."
)

COPYRIGHT_TRADEMARK_NOTICE = (
    f"{COPYRIGHT_NOTICE}\n\n"
    f"{PRODUCT}™ is a {BRAND}™ product developed for {COMPANY_SHORT} operations.\n\n"
    f"{PRODUCT}™ and {BRAND}™ are trademarks and/or service marks claimed by {COMPANY_LEGAL}. "
    "Unauthorized use is prohibited."
)

COPYRIGHT_TRADEMARK_NOTICE_LEGAL = (
    f"{COPYRIGHT_NOTICE}\n\n"
    f"{PRODUCT}™ is a {BRAND}™ product developed for {COMPANY_SHORT} operations.\n\n"
    f"{PRODUCT}™ and {BRAND}™ are trademarks and/or service marks claimed by {COMPANY_LEGAL}. "
    "No permission is granted to copy, reuse, sell, sublicense, distribute, or commercially exploit "
    "STWL software, branding, documentation, workflows, logos, names, or related materials unless "
    f"expressly authorized in writing by {COMPANY_LEGAL}.\n\n"
    "No public license is currently granted."
)

BRAND_ASSETS_SOURCE = r"D:\STWL\STWL\SCREENSHOTS"
LOGO_FILE = "STWL SQUARE PIC.png"

PRIVACY_STATEMENT_STWL = (
    "STWL does not sell user data.\n\n"
    f"{COMPANY_LEGAL} does not sell, rent, trade, or broker user, driver, customer, "
    "vendor, or operational data to third parties. Data collected through STWL systems, "
    f"including {PRODUCT}, is used only for authorized business, operational, compliance, "
    "safety, support, recordkeeping, and service-improvement purposes.\n\n"
    "STWL does not use user data for third-party advertising markets, data-broker resale, "
    "or unrelated commercial profiling.\n\n"
    "Any sharing of information is limited to what is necessary to provide services, comply "
    "with law, protect the business, support authorized operations, or fulfill user-approved "
    "requests."
)

PRIVACY_FOOTER_SHORT = (
    "STWL does not sell, rent, trade, or broker user data. Data is used only for authorized "
    "operations, support, compliance, safety, recordkeeping, and service improvement."
)

PRIVACY_NOTICE_ROAD_HAWK_TITLE = f"{PRODUCT} / {COMPANY_SHORT} Privacy Notice"

PRIVACY_NOTICE_ROAD_HAWK_BODY = (
    f"{PRODUCT} is built for driver and fleet operations. {COMPANY_SHORT} does not sell, "
    "rent, trade, or broker driver data, document data, trip data, vehicle data, or uploaded "
    "records. Uploaded documents and extracted fields are used only to support the driver's "
    "workflow, recordkeeping, compliance, and authorized business operations.\n\n"
    "OCR and document parsing are tools to help organize paperwork. STWL does not turn driver "
    "paperwork into a data product for resale."
)