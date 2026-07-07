import Image from "next/image";
import Link from "next/link";
import {
  BRAND,
  COMPANY_SHORT,
  CONTACT_HOURS,
  CONTACT_LINKS,
  CONTACT_LOCATION,
  CONTACT_ORGANIZATIONS,
  CONTACT_TIMEZONE_LABEL,
  LOGO_ALT,
  LOGO_PATH,
  PACKAGE_VERSION,
  PRIVACY_FOOTER_SHORT,
  PRODUCT,
  PRODUCT_LINE,
  TRADEMARK_FOOTER_SHORT,
} from "@/lib/branding";

export function AppFooter() {
  return (
    <footer className="border-t border-road-border px-8 py-4 text-xs text-road-muted">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Image
            src={LOGO_PATH}
            alt={LOGO_ALT}
            width={48}
            height={48}
            className="h-12 w-12 rounded-md border border-road-border object-cover"
          />
          <div>
            <p className="font-medium text-slate-300">{CONTACT_ORGANIZATIONS}</p>
            <p>{PRODUCT_LINE}</p>
            <p className="mt-1 text-[11px] text-road-muted/90">
              {CONTACT_LOCATION} · {CONTACT_TIMEZONE_LABEL}
            </p>
            <p className="mt-1 text-[11px] text-road-muted/80">Hours: {CONTACT_HOURS}</p>
          </div>
        </div>
        <div className="space-y-1 text-right">
          {TRADEMARK_FOOTER_SHORT.split("\n").map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-road-muted/90">
        {CONTACT_LINKS.map((link, index) => (
          <span key={`${link.label}-${link.url}`} className="inline-flex items-center gap-2">
            {index > 0 ? <span aria-hidden="true">·</span> : null}
            <a
              href={link.url}
              target={
                link.url.startsWith("mailto:") || link.url.startsWith("tel:")
                  ? undefined
                  : "_blank"
              }
              rel={
                link.url.startsWith("mailto:") || link.url.startsWith("tel:")
                  ? undefined
                  : "noopener noreferrer"
              }
              className="text-road-amber/90 transition hover:text-road-amber"
            >
              {link.display}
            </a>
          </span>
        ))}
      </div>
      <p className="mt-3 text-[11px] leading-relaxed text-road-muted/90">{PRIVACY_FOOTER_SHORT}</p>
      <p className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-road-muted/80">
        <span>
          {PRODUCT} v{PACKAGE_VERSION} · {COMPANY_SHORT} / {BRAND}
        </span>
        <span aria-hidden="true">·</span>
        <Link href="/privacy" className="text-road-amber/90 transition hover:text-road-amber">
          Privacy notice
        </Link>
      </p>
    </footer>
  );
}