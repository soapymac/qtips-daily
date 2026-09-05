import { ImageResponse } from "next/og";
import { business } from "@/lib/site";

export const dynamic = "force-static";
export const alt = `${business.name}: commercial grass cutting and grounds care, St Austell`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/** Open Graph / social share image, rendered at build time with no external fonts. */
export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 64,
          background: "linear-gradient(135deg, #0f2a1c 0%, #1f5236 100%)",
          color: "#f7f3ea",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: 18,
              background: "#f7f3ea",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg width="56" height="56" viewBox="0 0 48 48">
              <path d="M6 36c8-6 16-6 24 0s10 4 12 2" fill="none" stroke="#c9a06c" strokeWidth="3" strokeLinecap="round" />
              <path d="M15 33c1-8 3-14 8-20" fill="none" stroke="#163d28" strokeWidth="3.2" strokeLinecap="round" />
              <path d="M24 33c-1-7 1-13 6-18" fill="none" stroke="#163d28" strokeWidth="3.2" strokeLinecap="round" />
              <path d="M31 33c0-5 1-9 4-12" fill="none" stroke="#163d28" strokeWidth="3.2" strokeLinecap="round" />
            </svg>
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: 40, fontWeight: 800, letterSpacing: -1 }}>JD Grounds</div>
            <div style={{ fontSize: 18, letterSpacing: 4, color: "#b8d6c3" }}>ST AUSTELL · CORNWALL</div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ fontSize: 60, fontWeight: 800, lineHeight: 1.05, letterSpacing: -1.5, maxWidth: 1000 }}>
            Commercial grass cutting and grounds care
          </div>
          <div style={{ fontSize: 28, color: "#dcebe1" }}>
            Hotels · holiday parks · business parks · schools · care homes · pubs
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 24 }}>
          <div style={{ display: "flex", gap: 28, color: "#f7f3ea" }}>
            <span>{business.phone}</span>
            <span>{business.email}</span>
          </div>
          <div
            style={{
              background: "#c9a06c",
              color: "#0f2a1c",
              padding: "12px 24px",
              borderRadius: 999,
              fontWeight: 700,
            }}
          >
            Free quotes
          </div>
        </div>
      </div>
    ),
    size,
  );
}
