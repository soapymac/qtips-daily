import type { Metadata } from "next";
import { Button, Check, Container, PageHero, SectionHeading } from "@/components/ui";
import { Photo } from "@/components/Photo";
import { CtaBand } from "@/components/CtaBand";

export const metadata: Metadata = {
  title: "About JD Grounds",
  description:
    "JD Grounds is a St Austell based commercial grounds maintenance business: grass cutting, hedges, seasonal tidy-ups and practical landscaping for sites across the surrounding area. Fully insured.",
  alternates: { canonical: "/about" },
  openGraph: { url: "/about", title: "About | JD Grounds" },
};

const values = [
  {
    title: "Local, and staying local",
    text: "We're based in St Austell and work the towns and villages around it. Short travel means we turn up when we say we will, and we know the sites, the lanes and the weather.",
  },
  {
    title: "Reliable, not just available",
    text: "Commercial grounds only look good if the visits actually happen. We agree a schedule and keep to it, and if the weather forces a change we tell you rather than leave you guessing.",
  },
  {
    title: "Clear quotes, in writing",
    text: "Every quote spells out what's included, how often and what happens at the edges of the job. No surprises on the invoice and no £ rates plucked from the air.",
  },
  {
    title: "Work shaped to the site",
    text: "A holiday park, a care home and an industrial estate don't need the same thing. We look at what your grounds actually need and plan around your operation.",
  },
];

export default function AboutPage() {
  return (
    <>
      <PageHero
        eyebrow="About"
        title="A local grounds business built for commercial sites"
        intro="JD Grounds provides grass cutting, grounds maintenance and practical landscaping for businesses around St Austell. Straightforward work, done reliably, with clear communication from first call to final invoice."
      />

      <section className="bg-cream-100 py-14 sm:py-20">
        <Container className="grid gap-10 lg:grid-cols-2 lg:items-center">
          <Photo slot="about" className="aspect-[4/3] rounded-3xl shadow-soft" />
          <div>
            <SectionHeading
              eyebrow="What we're about"
              title="Professional grounds care without the corporate runaround"
              intro="We work with site managers, park owners, facilities teams and landlords who want one reliable contact for the grounds, not a call centre. You deal with the people doing the work."
            />
            <ul className="mt-6 space-y-2.5 text-[15px]">
              {["Fully insured for commercial work", "Written scope and quote for every site", "One point of contact", "Free, no-obligation site visits"].map((t) => (
                <li key={t} className="flex items-start gap-2.5">
                  <Check className="mt-0.5 h-5 w-5 shrink-0 text-green-700" /> {t}
                </li>
              ))}
            </ul>
            <Button href="/contact" className="mt-7" size="lg">
              Get in touch
            </Button>
          </div>
        </Container>
      </section>

      <section className="bg-white py-14 sm:py-20">
        <Container>
          <SectionHeading eyebrow="How we work" title="Four things you can hold us to" />
          <ul className="mt-10 grid gap-5 md:grid-cols-2">
            {values.map((v) => (
              <li key={v.title} className="rounded-2xl border border-green-900/10 bg-cream-50 p-6">
                <h3 className="text-lg font-extrabold text-green-950">{v.title}</h3>
                <p className="mt-2 leading-relaxed text-muted">{v.text}</p>
              </li>
            ))}
          </ul>
        </Container>
      </section>

      <section className="texture bg-cream-100 py-14 sm:py-20">
        <Container className="max-w-3xl">
          <SectionHeading
            eyebrow="Insurance and paperwork"
            title="Insured and happy to show it"
            intro="JD Grounds carries public liability insurance for commercial grounds work. If your procurement process needs a copy of the certificate, a risk assessment or a method statement, ask and we'll send them over."
          />
        </Container>
      </section>

      <CtaBand title="Want to talk it through?" text="A quick call or email is all it takes to get a site visit booked. No obligation, no pressure." />
    </>
  );
}
