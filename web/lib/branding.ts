export const COMPANY_SHORT = "STWL";
export const COMPANY_LEGAL = "Susquehanna Timberwolf Lines LLC";
export const BRAND = "Road Hammer";
export const PRODUCT = "Road Hawk";
export const PACKAGE_VERSION = "0.1.0";
export const TAGLINE = "Built by a trucker, for truckers.";
export const COPYRIGHT_YEAR = 2026;
export const COPYRIGHT_NOTICE = `© ${COPYRIGHT_YEAR} ${COMPANY_LEGAL}. All rights reserved.`;
export const PRODUCT_LINE = `${PRODUCT}™ — a ${BRAND}™ product.`;

export const CONTACT_ORGANIZATIONS =
  "Susquehanna Timberwolf Lines, LLC / That Dam BBS!, Inc.";
export const CONTACT_LOCATION = "Montrose, PA — USA";
export const CONTACT_TIMEZONE = "America/New_York";
export const CONTACT_TIMEZONE_LABEL = "UTC-04:00";
export const CONTACT_EMAIL = "office@thatdambbs.com";
export const CONTACT_PHONE = "570-442-0273";
export const CONTACT_PHONE_URL = "tel:+15704420273";
export const CONTACT_HOURS =
  "11am to 8pm Eastern, Monday to Friday. Closed weekends and federal holidays.";

export type ContactLink = {
  label: string;
  url: string;
  display: string;
};

export const CONTACT_LINKS: ContactLink[] = [
  { label: "Website", url: "https://www.thatdambbs.com", display: "www.thatdambbs.com" },
  { label: "Email", url: "mailto:office@thatdambbs.com", display: CONTACT_EMAIL },
  { label: "Phone", url: CONTACT_PHONE_URL, display: CONTACT_PHONE },
  { label: "GitHub", url: "https://github.com/Road-Hammer", display: "github.com/Road-Hammer" },
  { label: "Telegram", url: "https://t.me/NEPA_BBS", display: "t.me/NEPA_BBS" },
  {
    label: "LinkedIn",
    url: "https://www.linkedin.com/in/roadhammer",
    display: "in/roadhammer",
  },
  {
    label: "Facebook",
    url: "https://www.facebook.com/profile.php?id=61578962531585",
    display: "Facebook",
  },
  { label: "YouTube", url: "https://www.youtube.com/@1stRoadhammer", display: "YouTube" },
  { label: "X", url: "https://x.com/1stRoadhammer", display: "X" },
];

export const TRADEMARK_FOOTER_SHORT = `${COPYRIGHT_NOTICE}
${PRODUCT}™ and ${BRAND}™ are trademarks/service marks claimed by ${COMPANY_LEGAL}.`;

export const COPYRIGHT_TRADEMARK_NOTICE = `${COPYRIGHT_NOTICE}

${PRODUCT}™ is a ${BRAND}™ product developed for ${COMPANY_SHORT} operations.

${PRODUCT}™ and ${BRAND}™ are trademarks and/or service marks claimed by ${COMPANY_LEGAL}. Unauthorized use is prohibited.`;

export const COPYRIGHT_TRADEMARK_NOTICE_LEGAL = `${COPYRIGHT_NOTICE}

${PRODUCT}™ is a ${BRAND}™ product developed for ${COMPANY_SHORT} operations.

${PRODUCT}™ and ${BRAND}™ are trademarks and/or service marks claimed by ${COMPANY_LEGAL}. No permission is granted to copy, reuse, sell, sublicense, distribute, or commercially exploit STWL software, branding, documentation, workflows, logos, names, or related materials unless expressly authorized in writing by ${COMPANY_LEGAL}.

No public license is currently granted.`;

export const PRIVACY_STATEMENT_STWL = `STWL does not sell user data.

${COMPANY_LEGAL} does not sell, rent, trade, or broker user, driver, customer, vendor, or operational data to third parties. Data collected through STWL systems, including ${PRODUCT}, is used only for authorized business, operational, compliance, safety, support, recordkeeping, and service-improvement purposes.

STWL does not use user data for third-party advertising markets, data-broker resale, or unrelated commercial profiling.

Any sharing of information is limited to what is necessary to provide services, comply with law, protect the business, support authorized operations, or fulfill user-approved requests.`;

export const PRIVACY_FOOTER_SHORT =
  "STWL does not sell, rent, trade, or broker user data. Data is used only for authorized operations, support, compliance, safety, recordkeeping, and service improvement.";

export const PRIVACY_NOTICE_ROAD_HAWK_TITLE = `${PRODUCT} / ${COMPANY_SHORT} Privacy Notice`;

export const PRIVACY_NOTICE_ROAD_HAWK_BODY = `${PRODUCT} is built for driver and fleet operations. ${COMPANY_SHORT} does not sell, rent, trade, or broker driver data, document data, trip data, vehicle data, or uploaded records. Uploaded documents and extracted fields are used only to support the driver's workflow, recordkeeping, compliance, and authorized business operations.

OCR and document parsing are tools to help organize paperwork. STWL does not turn driver paperwork into a data product for resale.`;

/** Canonical STWL brand vault on D: */
export const BRAND_ASSETS_SOURCE = "D:\\STWL\\STWL\\SCREENSHOTS";
export const LOGO_PATH = "/brand/stwl-logo.png";
export const LOGO_ALT = `${COMPANY_LEGAL} (${COMPANY_SHORT}) logo`;