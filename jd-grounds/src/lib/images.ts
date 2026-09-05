/**
 * Photo slots.
 *
 * Stock photos are not bundled with the repo. Drop your chosen images into
 * /public/images with the filenames below and fill in `credit` where the
 * licence requires attribution (see IMAGE_CREDITS.md). Any slot whose file is
 * missing renders a tasteful illustration instead, so the site never shows a
 * broken image.
 *
 * Do not use photos of real named people presented as JD Grounds staff.
 */
import { existsSync } from "node:fs";
import { join } from "node:path";

export type PhotoSlot = {
  file: string;
  alt: string;
  credit?: string;
  creditUrl?: string;
};

export type PhotoKey = "hero" | "services" | "about" | "areas";

export const photos: Record<PhotoKey, PhotoSlot> = {
  hero: {
    file: "hero.jpg",
    alt: "Freshly cut grass on commercial grounds with hedges and trees in the background",
  },
  services: {
    file: "services.jpg",
    alt: "A ride-on mower cutting a wide lawn in neat stripes",
  },
  about: {
    file: "about.jpg",
    alt: "Rolling green fields near the Cornish coast",
  },
  areas: {
    file: "areas.jpg",
    alt: "A harbour village on the south Cornwall coast",
  },
};

/** Resolved at build time on the server: true when the file exists in /public/images. */
export function photoExists(key: PhotoKey): boolean {
  try {
    return existsSync(join(process.cwd(), "public", "images", photos[key].file));
  } catch {
    return false;
  }
}
