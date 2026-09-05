/**
 * Stylised Cornish grounds scene: rolling fields, hedge lines, mown stripes
 * and a low sun. Used as the hero visual and as the fallback for any photo
 * slot that hasn't been filled yet. Pure inline SVG, so it costs no request
 * and paints immediately.
 */
export function FieldIllustration({ className = "", variant = "hero" }: { className?: string; variant?: "hero" | "card" }) {
  const id = variant === "hero" ? "fi-hero" : "fi-card";
  return (
    <svg
      className={className}
      viewBox="0 0 800 560"
      preserveAspectRatio="xMidYMid slice"
      role="img"
      aria-label="Illustration of neatly cut fields and hedges in the Cornish countryside"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id={`${id}-sky`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#f7f3ea" />
          <stop offset="1" stopColor="#e6e3cf" />
        </linearGradient>
        <linearGradient id={`${id}-far`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#8cbb9e" />
          <stop offset="1" stopColor="#6ca882" />
        </linearGradient>
        <linearGradient id={`${id}-mid`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#4d9a67" />
          <stop offset="1" stopColor="#37804f" />
        </linearGradient>
        <linearGradient id={`${id}-near`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#2f7449" />
          <stop offset="1" stopColor="#1f5236" />
        </linearGradient>
        <pattern id={`${id}-stripes`} width="64" height="64" patternUnits="userSpaceOnUse" patternTransform="rotate(-18)">
          <rect width="32" height="64" fill="rgba(255,255,255,0.07)" />
        </pattern>
      </defs>

      <rect width="800" height="560" fill={`url(#${id}-sky)`} />
      {/* low sun */}
      <circle cx="610" cy="150" r="58" fill="#e8c88f" opacity="0.9" />
      <circle cx="610" cy="150" r="84" fill="#e8c88f" opacity="0.18" />

      {/* far hills */}
      <path d="M0 300C120 250 220 240 340 275s230 40 460-20v305H0z" fill={`url(#${id}-far)`} />
      {/* hedge line far */}
      <path d="M0 302C120 252 220 242 340 277s230 40 460-20" fill="none" stroke="#2a6b45" strokeWidth="6" strokeLinecap="round" opacity="0.55" />
      {/* trees on ridge */}
      {[90, 150, 205, 470, 520, 700, 740].map((x, i) => {
        const y = 300 - Math.sin((x / 800) * Math.PI) * 45 + (i % 2 ? 6 : 0);
        return (
          <g key={x}>
            <rect x={x - 2} y={y - 10} width="4" height="14" fill="#6b4520" />
            <ellipse cx={x} cy={y - 16} rx={14 + (i % 3) * 3} ry={12 + (i % 2) * 3} fill="#1f5236" />
          </g>
        );
      })}

      {/* mid field */}
      <path d="M0 380C160 330 300 350 440 380s260 30 360-10v190H0z" fill={`url(#${id}-mid)`} />
      <path d="M0 380C160 330 300 350 440 380s260 30 360-10v190H0z" fill={`url(#${id}-stripes)`} />
      {/* mid hedge */}
      <path d="M0 382C160 332 300 352 440 382s260 30 360-10" fill="none" stroke="#163d28" strokeWidth="9" strokeLinecap="round" opacity="0.7" />

      {/* near field */}
      <path d="M0 470C200 430 380 450 560 480s180 20 240 0v80H0z" fill={`url(#${id}-near)`} />
      <path d="M0 470C200 430 380 450 560 480s180 20 240 0v80H0z" fill={`url(#${id}-stripes)`} />
      <path d="M0 472C200 432 380 452 560 482s180 20 240 0" fill="none" stroke="#0f2a1c" strokeWidth="10" strokeLinecap="round" opacity="0.75" />

      {/* gate post and fence hint */}
      <g opacity="0.85">
        <rect x="118" y="404" width="6" height="52" rx="2" fill="#8a5a2b" />
        <rect x="178" y="410" width="6" height="46" rx="2" fill="#8a5a2b" />
        <path d="M124 414h54M124 428h54M124 442h54" stroke="#8a5a2b" strokeWidth="4" strokeLinecap="round" />
      </g>

      {/* grass tufts foreground */}
      {[40, 260, 420, 610, 760].map((x) => (
        <g key={x} stroke="#b8d6c3" strokeWidth="3" strokeLinecap="round" fill="none" opacity="0.7">
          <path d={`M${x} 540c2-10 4-16 8-24`} />
          <path d={`M${x + 8} 540c-1-9 1-16 5-22`} />
          <path d={`M${x + 14} 540c0-6 1-11 4-15`} />
        </g>
      ))}
    </svg>
  );
}
