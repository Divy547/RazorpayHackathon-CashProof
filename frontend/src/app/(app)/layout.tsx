import type { ReactNode } from "react";
import { Nav } from "@/components/Nav";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div
      className="flex min-h-screen flex-col bg-[#F3F0E8] text-[#171816] antialiased selection:bg-[#A47C52]/20 selection:text-[#171816]"
    >
      <Nav />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {children}
      </main>
      <footer className="border-t border-[#D9D5CA] bg-[#F3F0E8] px-4 sm:px-6 lg:px-8 py-4 text-center text-xs text-[#62635C]">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 sm:flex-row">
          <span>
            CashProof &middot; Deterministic software owns financial truth. AI investigates ambiguity.
          </span>
          <span className="font-mono text-[11px] text-[#62635C]">
            Razorpay Buildathon 2026 &middot; Track 4
          </span>
        </div>
      </footer>
    </div>
  );
}
