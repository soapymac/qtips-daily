import { business } from "@/lib/site";
import { Button, Container } from "./ui";
import { MailIcon, PhoneIcon } from "./Icons";

export function CtaBand({
  title = "Ready for a clear quote?",
  text = "Tell us about the site and we'll come back to you with a written, no-obligation quote. No £ guesswork, no pressure.",
}: {
  title?: string;
  text?: string;
}) {
  return (
    <section className="print-hidden bg-green-900 text-cream-50">
      <Container className="grid items-center gap-8 py-14 sm:py-16 lg:grid-cols-[1.4fr_1fr]">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">{title}</h2>
          <p className="mt-3 max-w-xl text-lg text-green-100">{text}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button href="/contact" variant="secondary" size="lg">
              Get a free quote
            </Button>
            <Button href={`mailto:${business.email}`} variant="light" size="lg">
              <MailIcon className="h-5 w-5" /> Email us
            </Button>
          </div>
        </div>
        <div className="rounded-2xl border border-green-100/15 bg-green-950/40 p-6">
          <p className="text-xs font-bold tracking-[0.18em] text-green-200 uppercase">Or get in touch directly</p>
          <ul className="mt-4 space-y-3 text-lg font-semibold">
            <li>
              <a href={business.phoneHref} className="inline-flex items-center gap-3 hover:text-earth-400">
                <PhoneIcon className="h-5 w-5" /> {business.phone}
              </a>
            </li>
            <li>
              <a href={`mailto:${business.email}`} className="inline-flex items-center gap-3 break-all hover:text-earth-400">
                <MailIcon className="h-5 w-5" /> {business.email}
              </a>
            </li>
          </ul>
          <p className="mt-4 text-sm text-green-200">Based in St Austell. We cover the surrounding towns and villages.</p>
        </div>
      </Container>
    </section>
  );
}
