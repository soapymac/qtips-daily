import { ImageResponse } from "next/og";

export const dynamic = "force-static";
export const size = { width: 512, height: 512 };
export const contentType = "image/png";

/** Favicon / app icon: the JD Grounds mark, rendered at build time. */
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#163d28",
          borderRadius: 112,
        }}
      >
        <svg width="420" height="420" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
          <path d="M6 36c8-6 16-6 24 0s10 4 12 2" fill="none" stroke="#c9a06c" strokeWidth="3" strokeLinecap="round" />
          <path d="M15 33c1-8 3-14 8-20" fill="none" stroke="#f7f3ea" strokeWidth="3.2" strokeLinecap="round" />
          <path d="M24 33c-1-7 1-13 6-18" fill="none" stroke="#f7f3ea" strokeWidth="3.2" strokeLinecap="round" />
          <path d="M31 33c0-5 1-9 4-12" fill="none" stroke="#f7f3ea" strokeWidth="3.2" strokeLinecap="round" />
        </svg>
      </div>
    ),
    size,
  );
}
