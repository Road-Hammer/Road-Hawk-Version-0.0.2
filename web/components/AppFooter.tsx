import Image from "next/image";
import {
  BRAND,
  COMPANY_LEGAL,
  COMPANY_SHORT,
  COPYRIGHT_NOTICE,
  LOGO_ALT,
  LOGO_PATH,
  PRODUCT,
  PRODUCT_LINE,
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
            <p className="font-medium text-slate-300">{COMPANY_LEGAL}</p>
            <p>{PRODUCT_LINE}</p>
          </div>
        </div>
        <p className="text-right">{COPYRIGHT_NOTICE}</p>
      </div>
      <p className="mt-2 text-[11px] text-road-muted/80">
        {PRODUCT} · {COMPANY_SHORT} / {BRAND} · Brand assets: D:\STWL
      </p>
    </footer>
  );
}