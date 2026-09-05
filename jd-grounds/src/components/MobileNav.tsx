"use client";

import Link from "next/link";
import { useEffect, useId, useState } from "react";
import { usePathname } from "next/navigation";
import { business, nav } from "@/lib/site";
import { MailIcon, PhoneIcon } from "./Icons";

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const panelId = useId();

  // Close on route change and on Escape
  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className="md:hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className="inline-flex h-11 w-11 items-center justify-center rounded-full text-green-950 hover:bg-green-100"
      >
        <span className="sr-only">{open ? "Close menu" : "Open menu"}</span>
        <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
          {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
        </svg>
      </button>

      <div
        id={panelId}
        hidden={!open}
        className="absolute inset-x-0 top-full border-b border-green-900/10 bg-cream-100 shadow-lift"
      >
        <nav aria-label="Mobile" className="flex flex-col px-5 py-3">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-lg px-3 py-3 text-lg font-semibold text-green-950 hover:bg-green-100"
            >
              {item.label}
            </Link>
          ))}
          <div className="mt-2 flex flex-col gap-2 border-t border-green-900/10 pt-4 pb-2">
            <a href={business.phoneHref} className="inline-flex items-center gap-2 px-3 py-2 font-semibold text-green-900">
              <PhoneIcon /> {business.phone}
            </a>
            <a href={`mailto:${business.email}`} className="inline-flex items-center gap-2 px-3 py-2 font-semibold text-green-900 break-all">
              <MailIcon /> {business.email}
            </a>
            <Link
              href="/contact"
              className="mt-1 inline-flex items-center justify-center rounded-full bg-green-800 px-5 py-3 font-semibold text-cream-50 hover:bg-green-900"
            >
              Get a free quote
            </Link>
          </div>
        </nav>
      </div>
    </div>
  );
}
