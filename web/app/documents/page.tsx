import Link from "next/link";
import { ApiOffline } from "@/components/ApiOffline";
import { DocumentIntake } from "@/components/DocumentIntake";
import { PRIVACY_FOOTER_SHORT } from "@/lib/branding";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DocumentsPage() {
  try {
    const documents = await api.getDocuments(100);
    return (
      <div className="space-y-8">
        <header>
          <p className="text-sm uppercase tracking-[0.25em] text-road-amber">Coyote Round 2</p>
          <h2 className="mt-2 text-4xl font-semibold text-white">Document intake</h2>
          <p className="mt-3 max-w-3xl text-sm text-road-muted">
            Upload driver paperwork, review machine-extracted fields, and verify before records become
            official. OCR is a fallback — never treated as gospel.
          </p>
          <p className="mt-3 max-w-3xl text-xs leading-relaxed text-road-muted/90">
            {PRIVACY_FOOTER_SHORT}{" "}
            <Link href="/privacy" className="text-road-amber/90 hover:text-road-amber">
              Full privacy notice
            </Link>
          </p>
        </header>
        <DocumentIntake initialDocuments={documents} />
      </div>
    );
  } catch {
    return (
      <div className="space-y-8">
        <header>
          <h2 className="text-4xl font-semibold text-white">Document intake</h2>
        </header>
        <ApiOffline />
      </div>
    );
  }
}