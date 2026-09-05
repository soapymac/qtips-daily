/**
 * Single source of truth for business details and site content.
 * Real details (phone, email, location) are confirmed by the owner.
 * Anything wrapped in square brackets is a placeholder to fill before go-live.
 */

export const business = {
  name: "JD Grounds",
  tagline: "Commercial grass cutting and grounds care for St Austell and surrounds",
  shortDescription:
    "Commercial grass cutting, grounds maintenance and landscaping for hotels, holiday parks, business parks, schools, care homes and pubs around St Austell, Cornwall.",
  email: "jdouqa@hotmail.co.uk",
  phone: "07944 201086",
  phoneHref: "tel:+447944201086",
  town: "St Austell",
  county: "Cornwall",
  country: "GB",
  region: "St Austell, Cornwall",
  // Fill before go-live — see README. Leave as-is to keep the placeholder visible in JSON-LD only.
  placeholders: {
    streetAddress: "[STREET ADDRESS]",
    postcode: "[POSTCODE]",
    insurance: "[INSURANCE DETAILS]",
    openingHours: "[OPENING HOURS]",
  },
} as const;

export function siteUrl(): string {
  const raw = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (raw) return raw.replace(/\/+$/, "");
  const vercel = process.env.VERCEL_PROJECT_PRODUCTION_URL || process.env.VERCEL_URL;
  if (vercel) return `https://${vercel}`;
  return "http://localhost:3000";
}

export const nav = [
  { href: "/services", label: "Services" },
  { href: "/areas", label: "Areas" },
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
] as const;

export const trustPoints = [
  "Local to St Austell",
  "Reliable, scheduled visits",
  "Clear, written quotes",
  "No obligation",
  "Fully insured",
] as const;

export type Sector = {
  slug: string;
  title: string;
  blurb: string;
  needs: string[];
  icon: "park" | "hotel" | "business" | "school" | "pub" | "golf" | "housing";
};

export const sectors: Sector[] = [
  {
    slug: "holiday-parks",
    title: "Holiday and caravan parks",
    blurb: "Pitches, verges and play areas kept tidy through the season, with visits timed around changeover days.",
    needs: ["Regular cuts in season", "Hedges and boundaries", "Pre-season tidy-up", "End-of-season clear-up"],
    icon: "park",
  },
  {
    slug: "hotels-estates",
    title: "Hotels and estates",
    blurb: "First impressions matter. Lawns, borders and approaches kept sharp so the grounds match the welcome.",
    needs: ["Weekly or fortnightly cuts", "Edging and borders", "Hedge trimming", "Seasonal planting and tidy-ups"],
    icon: "hotel",
  },
  {
    slug: "business-parks",
    title: "Business and industrial parks",
    blurb: "Straightforward, scheduled grounds maintenance for shared areas, car parks, verges and boundaries.",
    needs: ["Scheduled visits", "Verges and car park edges", "Hedges and screening", "Litter and leaf clearance"],
    icon: "business",
  },
  {
    slug: "schools-care",
    title: "Schools and care homes",
    blurb: "Safe, tidy grounds with visits planned around term times, quiet hours and site access.",
    needs: ["Timed visits", "Playing field surrounds", "Hedges and sight lines", "Holiday-period works"],
    icon: "school",
  },
  {
    slug: "pubs-amenity",
    title: "Pubs and gardens",
    blurb: "Beer gardens and frontages ready for the weekend, without you having to think about it.",
    needs: ["Regular cuts", "Borders and pots", "Hedges", "One-off clear-ups"],
    icon: "pub",
  },
  {
    slug: "golf-amenity",
    title: "Golf amenity and overflow",
    blurb: "Support for the areas your greenkeepers don't have time for: surrounds, car parks, hedges and winter works.",
    needs: ["Amenity and overflow areas", "Boundary hedges", "Car park and approach", "Winter works"],
    icon: "golf",
  },
  {
    slug: "housing-estates",
    title: "Housing association estates",
    blurb: "Communal greens, verges and shared spaces maintained on a clear, predictable schedule.",
    needs: ["Communal greens", "Verges and paths", "Hedges", "Seasonal tidy-ups"],
    icon: "housing",
  },
];

export type Service = {
  slug: string;
  title: string;
  summary: string;
  detail: string;
  includes: string[];
  icon: "mower" | "grounds" | "clearup" | "landscape" | "schedule";
};

export const services: Service[] = [
  {
    slug: "grass-cutting",
    title: "Regular grass cutting",
    summary: "Scheduled cuts, edged and cleared, so the site always looks looked-after.",
    detail:
      "Weekly, fortnightly or monthly depending on the site and the season. We agree the frequency, the areas and how the clippings are handled up front, then keep to it. If the weather forces a change we'll let you know rather than leave you guessing.",
    includes: ["Lawns, greens and amenity grass", "Verges and banks", "Strimming around obstacles", "Edging paths and borders", "Clippings collected or mulched, as agreed"],
    icon: "mower",
  },
  {
    slug: "grounds-maintenance",
    title: "Grounds maintenance",
    summary: "Hedges, borders, leaves and general upkeep on a plan that fits the site.",
    detail:
      "Everything beyond the mower that keeps grounds presentable: hedge trimming, border weeding, leaf clearance, pruning, keeping paths and sight lines clear. We shape the plan around what your site actually needs through the year.",
    includes: ["Hedge trimming and shaping", "Border weeding and mulching", "Leaf and debris clearance", "Light pruning", "Paths, signage and sight lines kept clear"],
    icon: "grounds",
  },
  {
    slug: "one-off-clear-ups",
    title: "One-off clear-ups",
    summary: "Overgrown or neglected areas brought back under control in one visit.",
    detail:
      "A handover, a change of manager, a site that's slipped over a busy season: whatever the reason, we can clear it and get it back to a state that's easy to maintain. A good first step before a regular schedule.",
    includes: ["Overgrown grass and brambles", "Neglected borders", "Hedge reduction", "Green waste removed", "Follow-on maintenance plan if wanted"],
    icon: "clearup",
  },
  {
    slug: "landscaping",
    title: "Practical landscaping",
    summary: "Sensible improvements: turfing, planting, beds and tidy boundaries.",
    detail:
      "We keep landscaping realistic and useful: new turf, planting schemes for borders and beds, bark and gravel areas, and tidying boundaries. If a job needs a specialist contractor we'll say so rather than take it on.",
    includes: ["Turfing and re-seeding", "Planting borders and beds", "Bark, gravel and low-maintenance areas", "Boundary tidying", "Honest advice on what's worth doing"],
    icon: "landscape",
  },
  {
    slug: "scheduled-visits",
    title: "Flexible commercial schedules",
    summary: "Visits timed around changeovers, term times, opening hours and quiet periods.",
    detail:
      "Commercial sites have their own rhythm. Holiday parks want the grounds sharp before Friday changeover; schools want work in the holidays; hotels want the front done before check-in. We plan visits around that, and you get one point of contact.",
    includes: ["Agreed visit windows", "Seasonal frequency changes", "One point of contact", "Written scope so everyone knows what's covered"],
    icon: "schedule",
  },
];

export const areas = [
  "St Austell",
  "Charlestown",
  "Carlyon Bay",
  "Pentewan",
  "Mevagissey",
  "Fowey",
  "Bugle",
  "Holmbush",
  "London Apprentice",
  "Gorran",
  "Carthew",
  "Par",
  "St Blazey",
  "Tywardreath",
  "Polgooth",
  "Sticker",
  "Trewoon",
  "Roche",
  "Lostwithiel",
  "Grampound",
] as const;

export const howItWorks = [
  {
    step: "1",
    title: "Get in touch",
    text: "Email, call, or use the quote form. Tell us roughly what the site is and what you need.",
  },
  {
    step: "2",
    title: "We look at the site",
    text: "A quick visit or a chat over the phone to walk through the areas, access and timings.",
  },
  {
    step: "3",
    title: "Clear quote and schedule",
    text: "You get a written quote with the scope spelled out. If it works for you, we agree a start date.",
  },
] as const;

export const siteTypes = [
  "Holiday or caravan park",
  "Hotel or estate",
  "Business or industrial park",
  "School or care home",
  "Pub or restaurant garden",
  "Golf amenity or overflow area",
  "Housing association estate",
  "Other commercial site",
] as const;

export const cadences = [
  "Weekly",
  "Fortnightly",
  "Monthly",
  "Seasonal (spring to autumn)",
  "One-off clear-up",
  "Not sure yet",
] as const;
