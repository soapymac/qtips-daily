# JD Grounds — website

Marketing site for **JD Grounds**, a commercial grass cutting, grounds
maintenance and landscaping business in St Austell, Cornwall.

Built with Next.js (App Router) + TypeScript + Tailwind CSS. Statically
rendered, Vercel-ready, no database, no external fonts, minimal JavaScript.

> This folder is a standalone project. If it lives inside a larger repository,
> set **Root Directory** to `jd-grounds` when importing into Vercel.

## Pages

| Route             | What it is                                                           |
| ----------------- | -------------------------------------------------------------------- |
| `/`               | Home: hero, trust strip, who we help, services snapshot, how it works, areas, CTA |
| `/services`       | Service detail, "typically includes" lists, pricing explainer, needs by sector |
| `/areas`          | St Austell and surrounding towns/villages, grouped                   |
| `/about`          | Brand-only About (no personal names), values, insurance note         |
| `/contact`        | Email, phone, quote form with success / error states                 |
| `/privacy`        | Short privacy notice for enquiry data                                |
| `/services-sheet` | Print-friendly one-page services sheet (A4)                          |
| `/sitemap.xml`, `/robots.txt`, `/manifest.webmanifest`, `/icon`, `/opengraph-image` | Generated at build |

Business details live in one place: `src/lib/site.ts`. Change the phone,
email, service list, sectors or areas there and every page updates.

## Run locally

```bash
npm install
npm run dev        # http://localhost:3000
```

```bash
npm run build      # production build (must pass before deploying)
npm run start      # serve the production build
npm run typecheck  # TypeScript only
```

Requires Node 20 or newer.

## Deploy to Vercel (free preview URL)

1. Push this folder to a Git repository (GitHub, GitLab or Bitbucket).
2. Go to <https://vercel.com/new>, import the repository.
3. Framework preset: **Next.js** (auto-detected). If the site is in a
   subfolder, set **Root Directory** to `jd-grounds`.
4. Add environment variables (all optional, see below). At minimum set
   `NEXT_PUBLIC_SITE_URL` to the production URL Vercel gives you, e.g.
   `https://jd-grounds.vercel.app`, then redeploy so canonical links,
   `sitemap.xml` and OG tags use it.
5. Deploy. Vercel gives you a free `*.vercel.app` URL. Add a custom domain
   later under Project → Settings → Domains.

Other hosts (Netlify, Cloudflare Pages) also work with the Next.js preset.

## Environment variables

Copy `.env.example` to `.env.local` for local use, or set in the host's
dashboard. Everything is optional; the site builds with none of them.

| Variable                        | Purpose                                                                 |
| ------------------------------- | ----------------------------------------------------------------------- |
| `NEXT_PUBLIC_SITE_URL`          | Canonical base URL (no trailing slash). Falls back to Vercel's URL, then `http://localhost:3000`. |
| `NEXT_PUBLIC_FORM_ENDPOINT`     | Where the quote form POSTs JSON. Unset = mailto fallback (see below).   |
| `NEXT_PUBLIC_PLAUSIBLE_DOMAIN`  | Enables Plausible analytics (cookie-free).                              |
| `NEXT_PUBLIC_GA_MEASUREMENT_ID` | Enables Google Analytics 4 instead. Consider a cookie banner first.     |

## Quote form wiring

The form in `src/components/QuoteForm.tsx` has two modes:

**1. No endpoint configured (default).** Submitting opens the visitor's email
app with a pre-filled message to `jdouqa@hotmail.co.uk` containing all the
fields. Zero setup, works today, but relies on the visitor having a mail app.

**2. Endpoint configured (recommended before outreach ramps up).** Set
`NEXT_PUBLIC_FORM_ENDPOINT` and the form POSTs JSON with
`Accept: application/json`. Works out of the box with:

- **Formspree** (free tier is fine): create a form at <https://formspree.io>,
  set the endpoint to `https://formspree.io/f/<your-id>`, confirm the
  notification address is `jdouqa@hotmail.co.uk`. The `_subject` field is
  already sent so inbox subjects read "JD Grounds quote request: …".
- **Basin, Getform, Web3Forms** or similar: same idea, paste their endpoint.
- **Your own function**: any URL that accepts a JSON POST and returns 2xx.

Fields sent: `name`, `site`, `email`, `phone`, `siteType`, `cadence`,
`message`, `_subject`. A hidden honeypot field (`company_website`) is
dropped client-side; bots that fill it get a fake success.

Success and error states are handled in the component. On error the visitor
is shown the email address and phone number as a fallback.

## Photos

No stock photos are committed. Each photo slot shows a built-in field
illustration until a file is added. To add photos:

1. Save JPEGs to `public/images/` as `hero.jpg`, `services.jpg`,
   `about.jpg`, `areas.jpg` (1600 × 1200 px recommended, under 250 KB).
2. Fill in `credit` / `creditUrl` in `src/lib/images.ts` where the licence
   requires attribution. It renders as a small caption on the photo.
3. Log the source and licence in `IMAGE_CREDITS.md`.

Never present a photo of a real, named person as JD Grounds staff.

## Fill before go-live

Real details already in place: trading name, email `jdouqa@hotmail.co.uk`,
phone `07944 201086`, location St Austell. The following are placeholders
or gaps and should be dealt with before sharing the URL widely:

- [ ] `NEXT_PUBLIC_SITE_URL` set to the live URL (Vercel env var).
- [ ] Quote form endpoint (`NEXT_PUBLIC_FORM_ENDPOINT`) set up and test-submitted, or accept the mailto fallback for now.
- [ ] Photos added to `public/images/` (see above) and credited in `IMAGE_CREDITS.md`.
- [ ] `src/lib/site.ts` → `business.placeholders`:
  - `[STREET ADDRESS]`, `[POSTCODE]` — postal address for JSON-LD LocalBusiness (only shown to search engines; delete the fields if you'd rather not publish an address).
  - `[OPENING HOURS]` — e.g. `Mo-Fr 08:00-17:00`.
  - `[INSURANCE DETAILS]` — not shown on the site; the site says "fully insured" only. Keep the certificate to hand for procurement requests.
- [ ] `src/app/privacy/page.tsx` → `[FORM PROVIDER AND PRIVACY LINK]`, `[UPDATE IF ANALYTICS ENABLED]`, `[DATE]`.
- [ ] Decide on analytics (Plausible recommended: no cookie banner needed).
- [ ] Custom domain, when there is one: add in Vercel and update `NEXT_PUBLIC_SITE_URL`.
- [ ] Optional: Google Business Profile listing pointing at the site.

## Content rules (from the brief)

- No £ rates or day rates anywhere. Free, no-obligation quotes only.
- No invented facts: no years in business, team size, awards, testimonials, registration or VAT numbers, insurance certificate numbers or insurer names.
- "Fully insured" / "public liability insured" is fine.
- About page is brand-only: no personal names.
- Golf and schools: pitch amenity/overflow grass, hedges, surrounds and winter works. No greenkeeping or sports-turf claims.
- Tone: warm, plain, commercial, Cornish-local.

## Project layout

```
jd-grounds/
├─ src/app/            routes (App Router), sitemap, robots, OG image, icon
├─ src/components/     Header, Footer, Logo, QuoteForm, Photo, illustration, icons
├─ src/lib/site.ts     business details, services, sectors, areas, copy
├─ src/lib/images.ts   photo slots and credits
├─ public/images/      drop photos here
├─ IMAGE_CREDITS.md
└─ .env.example
```

## Accessibility and performance notes

- Semantic landmarks, skip link, labelled form fields, visible focus rings,
  keyboard-operable mobile menu with Escape to close.
- Colour pairs (deep green on cream, cream on deep green) meet WCAG AA.
- System font stack: no font downloads, fast first paint.
- Only two small client components (mobile menu, quote form). Everything
  else is server-rendered static HTML.
