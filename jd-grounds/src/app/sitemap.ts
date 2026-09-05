import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/site";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteUrl();
  const now = new Date();
  const pages: Array<[string, number, MetadataRoute.Sitemap[number]["changeFrequency"]]> = [
    ["/", 1, "monthly"],
    ["/services", 0.9, "monthly"],
    ["/areas", 0.8, "monthly"],
    ["/about", 0.7, "yearly"],
    ["/contact", 0.9, "yearly"],
  ];
  return pages.map(([path, priority, changeFrequency]) => ({
    url: `${base}${path}`,
    lastModified: now,
    changeFrequency,
    priority,
  }));
}
