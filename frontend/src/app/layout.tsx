import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Nav } from "@/components/Nav";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CashProof | Evidence-First Settlement Control",
  description:
    "Deterministic reconciliation control dashboard: candidate matching, evidence, gate evaluation, and resolution over Phase 2 settlement data.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-[#05070a] text-slate-200">
        <Nav />
        <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">{children}</main>
        <footer className="border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-600">
          CashProof &middot; Deterministic software owns financial truth. AI investigates
          ambiguity.
        </footer>
      </body>
    </html>
  );
}
