import Link from "next/link";
import { areas, business, nav } from "@/lib/site";
import { Logo } from "./Logo";
import { Container } from "./ui";
import { MailIcon, PhoneIcon, PinIcon } from "./Icons";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="print-hidden bg-green-950 text-green-100">
      <Container className="grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div className="sm:col-span-2 lg:col-span-1">
          <Logo tone="light" className="h-10 w-auto" />
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-green-200">
            Commercial grass cutting, grounds maintenance and practical landscaping for sites around St Austell, Cornwall.
          </p>
          <p className="mt-3 text-sm text-green-200">Fully insured. Free, no-obligation quotes.</p>
        </div>

        <div>
          <h2 className="text-xs font-bold tracking-[0.18em] text-cream-100 uppercase">Contact</h2>
          <ul className="mt-4 space-y-3 text-sm">
            <li>
              <a href={`mailto:${business.email}`} className="inline-flex items-start gap-2 break-all hover:text-cream-50">
                <MailIcon className="mt-0.5 h-4 w-4 shrink-0" /> {business.email}
              </a>
            </li>
            <li>
              <a href={business.phoneHref} className="inline-flex items-center gap-2 hover:text-cream-50">
                <PhoneIcon className="h-4 w-4 shrink-0" /> {business.phone}
              </a>
            </li>
            <li className="inline-flex items-start gap-2">
              <PinIcon className="mt-0.5 h-4 w-4 shrink-0" /> {business.region}, UK
            </li>
          </ul>
        </div>

        <div>
          <h2 className="text-xs font-bold tracking-[0.18em] text-cream-100 uppercase">Pages</h2>
          <ul className="mt-4 space-y-2 text-sm">
            <li>
              <Link href="/" className="hover:text-cream-50">Home</Link>
            </li>
            {nav.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="hover:text-cream-50">{item.label}</Link>
              </li>
            ))}
            <li>
              <Link href="/services-sheet" className="hover:text-cream-50">Services sheet (print)</Link>
            </li>
            <li>
              <Link href="/privacy" className="hover:text-cream-50">Privacy</Link>
            </li>
          </ul>
        </div>

        <div>
          <h2 className="text-xs font-bold tracking-[0.18em] text-cream-100 uppercase">Areas covered</h2>
          <p className="mt-4 text-sm leading-relaxed text-green-200">{areas.slice(0, 12).join(" · ")} and surrounds.</p>
          <Link href="/areas" className="mt-3 inline-block text-sm font-semibold text-cream-100 underline-offset-4 hover:underline">
            Full list of areas
          </Link>
        </div>
      </Container>
      <div className="border-t border-green-100/10">
        <Container className="flex flex-col gap-2 py-5 text-xs text-green-300 sm:flex-row sm:items-center sm:justify-between">
          <p>© {year} {business.name}. {business.region}.</p>
          <p>
            <Link href="/privacy" className="hover:text-cream-50">Privacy notice</Link>
          </p>
        </Container>
      </div>
    </footer>
  );
}
