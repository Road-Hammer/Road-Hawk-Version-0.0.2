import {
  CONTACT_HOURS,
  CONTACT_LINKS,
  CONTACT_LOCATION,
  CONTACT_ORGANIZATIONS,
  CONTACT_TIMEZONE_LABEL,
} from "@/lib/branding";

function isInternalContactLink(url: string) {
  return url.startsWith("mailto:") || url.startsWith("tel:");
}

export function ContactBlock() {
  return (
    <section className="panel space-y-4">
      <h3 className="text-lg font-semibold text-white">Contact</h3>
      <div className="space-y-3 text-sm leading-relaxed text-slate-300">
        <p>{CONTACT_ORGANIZATIONS}</p>
        <p>
          {CONTACT_LOCATION} · {CONTACT_TIMEZONE_LABEL}
        </p>
        <p className="text-road-muted">Hours: {CONTACT_HOURS}</p>
        <ul className="space-y-2">
          {CONTACT_LINKS.map((link) => (
            <li key={`${link.label}-${link.url}`}>
              <span className="text-road-muted">{link.label}: </span>
              <a
                href={link.url}
                target={isInternalContactLink(link.url) ? undefined : "_blank"}
                rel={isInternalContactLink(link.url) ? undefined : "noopener noreferrer"}
                className="text-road-amber/90 transition hover:text-road-amber"
              >
                {link.display}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}