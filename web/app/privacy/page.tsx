import { ContactBlock } from "@/components/ContactBlock";
import {
  COMPANY_LEGAL,
  COMPANY_SHORT,
  COPYRIGHT_TRADEMARK_NOTICE,
  COPYRIGHT_TRADEMARK_NOTICE_LEGAL,
  PRIVACY_NOTICE_ROAD_HAWK_BODY,
  PRIVACY_NOTICE_ROAD_HAWK_TITLE,
  PRIVACY_STATEMENT_STWL,
  PRODUCT,
} from "@/lib/branding";

function PrivacySection({ title, body }: { title: string; body: string }) {
  return (
    <section className="panel space-y-4">
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <div className="space-y-4 text-sm leading-relaxed text-slate-300">
        {body.split("\n\n").map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>
    </section>
  );
}

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header>
        <p className="text-sm uppercase tracking-[0.25em] text-road-amber">Privacy</p>
        <h2 className="mt-2 text-4xl font-semibold text-white">Data use &amp; privacy</h2>
        <p className="mt-3 text-sm text-road-muted">
          {COMPANY_LEGAL} ({COMPANY_SHORT}) — {PRODUCT} operational privacy posture.
        </p>
      </header>

      <PrivacySection title={PRIVACY_NOTICE_ROAD_HAWK_TITLE} body={PRIVACY_NOTICE_ROAD_HAWK_BODY} />

      <PrivacySection title="STWL does not sell user data" body={PRIVACY_STATEMENT_STWL} />

      <PrivacySection title="Copyright and trademark notice" body={COPYRIGHT_TRADEMARK_NOTICE} />

      <PrivacySection title="Legal use and licensing" body={COPYRIGHT_TRADEMARK_NOTICE_LEGAL} />

      <ContactBlock />
    </div>
  );
}