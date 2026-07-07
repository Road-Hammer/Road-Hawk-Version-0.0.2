import type { Metadata } from "next";
import { AppFooter } from "@/components/AppFooter";
import { Sidebar } from "@/components/Sidebar";
import { BRAND, COMPANY_LEGAL, COMPANY_SHORT, PRODUCT, TAGLINE } from "@/lib/branding";
import "./globals.css";

export const metadata: Metadata = {
  title: `${PRODUCT} | ${COMPANY_SHORT}`,
  description: `${PRODUCT} by ${BRAND} — fleet and driver operations for trucking. ${COMPANY_LEGAL}. ${TAGLINE}`,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex min-h-screen flex-1 flex-col">
            <main className="flex-1 overflow-y-auto px-8 py-8">{children}</main>
            <AppFooter />
          </div>
        </div>
      </body>
    </html>
  );
}