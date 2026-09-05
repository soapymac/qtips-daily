import Link from "next/link";
import { business, nav } from "@/lib/site";
import { Logo } from "./Logo";
import { Button, Container } from "./ui";
import { MobileNav } from "./MobileNav";
import { PhoneIcon } from "./Icons";

export function Header() {
  return (
    <header className="print-hidden sticky top-0 z-40 border-b border-green-900/10 bg-cream-100/90 backdrop-blur supports-[backdrop-filter]:bg-cream-100/75">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-green-900 focus:px-3 focus:py-2 focus:text-cream-50"
      >
        Skip to content
      </a>
      <Container className="flex h-16 items-center justify-between gap-4 sm:h-20">
        <Link href="/" className="flex shrink-0 items-center" aria-label="JD Grounds home">
          <Logo className="h-9 w-auto sm:h-10" />
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-full px-3.5 py-2 text-[15px] font-semibold text-green-950 hover:bg-green-100"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <a
            href={business.phoneHref}
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-[15px] font-semibold text-green-900 hover:bg-green-100"
          >
            <PhoneIcon className="h-4 w-4" />
            {business.phone}
          </a>
          <Button href="/contact">Get a free quote</Button>
        </div>

        <MobileNav />
      </Container>
    </header>
  );
}
