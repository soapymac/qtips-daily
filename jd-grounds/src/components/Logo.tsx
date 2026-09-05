type LogoProps = {
  className?: string;
  /** "light" for use on dark green backgrounds */
  tone?: "dark" | "light";
  showWordmark?: boolean;
};

/**
 * JD Grounds wordmark: a rounded mark with a stylised blade-of-grass "J" and
 * a hill-line "D", set beside the name. Pure SVG, no external assets.
 */
export function Logo({ className = "h-9", tone = "dark", showWordmark = true }: LogoProps) {
  const text = tone === "light" ? "#f7f3ea" : "#0f2a1c";
  const sub = tone === "light" ? "#b8d6c3" : "#2a6b45";
  const markBg = tone === "light" ? "#f7f3ea" : "#163d28";
  const markFg = tone === "light" ? "#163d28" : "#f7f3ea";
  const accent = "#c9a06c";
  return (
    <svg
      className={className}
      viewBox={showWordmark ? "0 0 236 48" : "0 0 48 48"}
      role="img"
      aria-label="JD Grounds"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="0" y="0" width="48" height="48" rx="12" fill={markBg} />
      {/* rolling ground line */}
      <path d="M6 36c8-6 16-6 24 0s10 4 12 2" fill="none" stroke={accent} strokeWidth="3" strokeLinecap="round" />
      {/* grass blades */}
      <path d="M15 33c1-8 3-14 8-20" fill="none" stroke={markFg} strokeWidth="3.2" strokeLinecap="round" />
      <path d="M24 33c-1-7 1-13 6-18" fill="none" stroke={markFg} strokeWidth="3.2" strokeLinecap="round" />
      <path d="M31 33c0-5 1-9 4-12" fill="none" stroke={markFg} strokeWidth="3.2" strokeLinecap="round" />
      {showWordmark && (
        <>
          <text x="60" y="27" fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif" fontWeight="800" fontSize="24" letterSpacing="-0.5" fill={text}>
            JD Grounds
          </text>
          <text x="61" y="41" fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif" fontWeight="600" fontSize="9.5" letterSpacing="1.6" fill={sub}>
            ST AUSTELL · CORNWALL
          </text>
        </>
      )}
    </svg>
  );
}
