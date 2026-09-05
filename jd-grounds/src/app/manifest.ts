import type { MetadataRoute } from "next";
import { business } from "@/lib/site";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: business.name,
    short_name: business.name,
    description: business.shortDescription,
    start_url: "/",
    display: "browser",
    background_color: "#f7f3ea",
    theme_color: "#0f2a1c",
    icons: [{ src: "/icon", sizes: "512x512", type: "image/png" }],
  };
}
