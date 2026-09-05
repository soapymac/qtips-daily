import type { Metadata, Viewport } from "next";
import "./globals.css";
import { business, siteUrl } from "@/lib/site";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { JsonLd } from "@/components/JsonLd";
import { Analytics } from "@/components/Analytics";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: {
    default: `${business.name} | Commercial grass cutting and grounds care, St Austell`,
    template: `%s | ${business.name}`,
  },
  description: business.shortDescription,
  applicationName: business.name,
  keywords: [
    "commercial grass cutting St Austell",
    "grounds maintenance Cornwall",
    "holiday park grounds maintenance",
    "hedge trimming St Austell",
    "landscaping St Austell",
    "grounds contractor Cornwall",
  ],
  openGraph: {
    type: "website",
    locale: "en_GB",
    siteName: business.name,
    title: `${business.name} | Commercial grass cutting and grounds care, St Austell`,
    description: business.shortDescription,
    url: "/",
  },
  twitter: {
    card: "summary_large_image",
    title: `${business.name} | Commercial grounds care, St Austell`,
    description: business.shortDescription,
  },
  robots: { index: true, follow: true },
  alternates: { canonical: "/" },
};

export const viewport: Viewport = {
  themeColor: "#0f2a1c",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-GB">
      <body className="flex min-h-dvh flex-col antialiased">
        <Header />
        <main id="main" className="flex-1">
          {children}
        </main>
        <Footer />
        <JsonLd />
        <Analytics />
      </body>
    </html>
  );
}
