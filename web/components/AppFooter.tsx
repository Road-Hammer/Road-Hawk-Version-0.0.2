import {
  BRAND,
  COMPANY_LEGAL,
  COMPANY_SHORT,
  COPYRIGHT_NOTICE,
  PRODUCT,
  PRODUCT_LINE,
} from "@/lib/branding";

export function AppFooter() {
  return (
    <footer className="border-t border-road-border px-8 py-4 text-xs text-road-muted">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <p>{COPYRIGHT_NOTICE}</p>
        <p>
          {PRODUCT_LINE} · {COMPANY_SHORT} / {BRAND}
        </p>
      </div>
      <p className="mt-1 text-[11px] text-road-muted/80">
        {PRODUCT} is developed by {COMPANY_LEGAL}.
      </p>
    </footer>
  );
}