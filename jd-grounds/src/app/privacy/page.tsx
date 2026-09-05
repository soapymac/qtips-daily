import type { Metadata } from "next";
import { business } from "@/lib/site";
import { Container, PageHero } from "@/components/ui";

export const metadata: Metadata = {
  title: "Privacy notice",
  description: "How JD Grounds handles the details you send through the contact form, by email or by phone.",
  alternates: { canonical: "/privacy" },
  robots: { index: false, follow: true },
};

export default function PrivacyPage() {
  return (
    <>
      <PageHero eyebrow="Privacy" title="Privacy notice" intro="A short, plain-English note on what we do with the details you give us." />
      <section className="bg-cream-100 py-14 sm:py-20">
        <Container className="max-w-3xl">
          <div className="space-y-8 rounded-3xl border border-green-900/10 bg-white p-6 leading-relaxed text-ink sm:p-10">
            <div>
              <h2 className="text-xl font-extrabold text-green-950">Who we are</h2>
              <p className="mt-2 text-muted">
                {business.name}, a grounds maintenance business based in {business.region}, UK. Contact:{" "}
                <a href={`mailto:${business.email}`} className="font-semibold text-green-800 underline underline-offset-4">{business.email}</a>, {business.phone}.
              </p>
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-green-950">What we collect</h2>
              <p className="mt-2 text-muted">
                When you use the quote form, email us or call, we receive the details you choose to give us: typically your name, business or site name, email address, phone number, the type of site and a description of the work.
              </p>
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-green-950">Why we use it</h2>
              <p className="mt-2 text-muted">
                To reply to your enquiry, arrange a site visit and prepare a quote. If you become a customer, to schedule and invoice the work. Our lawful basis is taking steps at your request before entering a contract, and our legitimate interest in running the business.
              </p>
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-green-950">How the form works</h2>
              <p className="mt-2 text-muted">
                Form submissions are delivered to our email inbox. Depending on how the site is configured, this is either directly through your own email app or via a third-party form delivery service that processes the message on our behalf. [FORM PROVIDER AND PRIVACY LINK]
              </p>
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-green-950">Who we share it with</h2>
              <p className="mt-2 text-muted">Nobody, other than the services we use to receive email and, if enabled, deliver form messages. We don&rsquo;t sell or pass on your details.</p>
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-green-950">How long we keep it</h2>
              <p className="mt-2 text-muted">
                Enquiries that don&rsquo;t go ahead are deleted within 12 months. Customer records are kept for as long as needed for the work and for accounting requirements.
              </p>
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-green-950">Cookies and analytics</h2>
              <p className="mt-2 text-muted">
                The site doesn&rsquo;t set cookies for advertising. If we enable privacy-friendly visitor statistics, they don&rsquo;t identify individuals. [UPDATE IF ANALYTICS ENABLED]
              </p>
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-green-950">Your rights</h2>
              <p className="mt-2 text-muted">
                You can ask what we hold about you, ask us to correct or delete it, or object to how we use it. Email{" "}
                <a href={`mailto:${business.email}`} className="font-semibold text-green-800 underline underline-offset-4">{business.email}</a>. You can also complain to the Information Commissioner&rsquo;s Office (ico.org.uk).
              </p>
            </div>
            <p className="text-sm text-muted">Last updated: [DATE]</p>
          </div>
        </Container>
      </section>
    </>
  );
}
