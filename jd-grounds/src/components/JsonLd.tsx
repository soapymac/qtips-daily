import { areas, business, siteUrl } from "@/lib/site";

/**
 * LocalBusiness structured data. Fields we don't have yet are left as
 * bracketed placeholders so they are easy to find and fill before go-live.
 * Search engines ignore unknown/placeholder values; they don't hurt ranking.
 */
export function JsonLd() {
  const url = siteUrl();
  const data = {
    "@context": "https://schema.org",
    "@type": ["LocalBusiness", "LandscapingBusiness"],
    "@id": `${url}/#business`,
    name: business.name,
    description: business.shortDescription,
    url,
    email: business.email,
    telephone: "+44 7944 201086",
    image: `${url}/opengraph-image`,
    logo: `${url}/icon`,
    priceRange: "Free quotes",
    address: {
      "@type": "PostalAddress",
      streetAddress: business.placeholders.streetAddress,
      addressLocality: business.town,
      addressRegion: business.county,
      postalCode: business.placeholders.postcode,
      addressCountry: business.country,
    },
    areaServed: areas.map((name) => ({ "@type": "Place", name: `${name}, Cornwall` })),
    openingHours: business.placeholders.openingHours,
    knowsAbout: ["Commercial grass cutting", "Grounds maintenance", "Hedge trimming", "Landscaping"],
    makesOffer: [
      "Regular grass cutting",
      "Grounds maintenance",
      "One-off clear-ups",
      "Practical landscaping",
      "Scheduled commercial visits",
    ].map((name) => ({ "@type": "Offer", itemOffered: { "@type": "Service", name } })),
  };
  return (
    <script
      type="application/ld+json"
      // JSON.stringify output is safe here: content is static and controlled.
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}
