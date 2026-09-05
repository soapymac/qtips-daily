import type { Sector, Service } from "@/lib/site";

const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" } as const;

export function SectorIcon({ name, className = "h-7 w-7" }: { name: Sector["icon"]; className?: string }) {
  const p = { className, viewBox: "0 0 24 24", "aria-hidden": true, ...stroke };
  switch (name) {
    case "park":
      return (
        <svg {...p}>
          <path d="M3 17h18M5 17V9a3 3 0 0 1 3-3h8a3 3 0 0 1 3 3v8" />
          <path d="M9 17v-4h6v4M3 20h18" />
          <circle cx="7" cy="20" r="1.5" />
          <circle cx="17" cy="20" r="1.5" />
        </svg>
      );
    case "hotel":
      return (
        <svg {...p}>
          <path d="M4 21V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16M2 21h20" />
          <path d="M8 7h2M14 7h2M8 11h2M14 11h2M8 15h2M14 15h2M10 21v-3h4v3" />
        </svg>
      );
    case "business":
      return (
        <svg {...p}>
          <path d="M3 21V9l6-3v15M9 21V12l6-3v12M15 21V14l6-3v10M2 21h20" />
        </svg>
      );
    case "school":
      return (
        <svg {...p}>
          <path d="M3 10l9-5 9 5-9 5-9-5z" />
          <path d="M7 12v5c0 1.5 2.5 3 5 3s5-1.5 5-3v-5M21 10v6" />
        </svg>
      );
    case "pub":
      return (
        <svg {...p}>
          <path d="M6 8h9v10a3 3 0 0 1-3 3H9a3 3 0 0 1-3-3V8z" />
          <path d="M15 10h2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-2M6 8c0-2 1.5-4 4.5-4S15 6 15 8" />
        </svg>
      );
    case "golf":
      return (
        <svg {...p}>
          <path d="M9 21V4l8 3-8 3" />
          <path d="M3 21c2-2 4-3 6-3s4 1 6 3" />
          <circle cx="17" cy="19" r="1.5" />
        </svg>
      );
    case "housing":
      return (
        <svg {...p}>
          <path d="M3 11l5-5 5 5M13 11l4-4 4 4" />
          <path d="M5 10v10h6V10M15 10v10h4V10M2 20h20" />
        </svg>
      );
  }
}

export function ServiceIcon({ name, className = "h-7 w-7" }: { name: Service["icon"]; className?: string }) {
  const p = { className, viewBox: "0 0 24 24", "aria-hidden": true, ...stroke };
  switch (name) {
    case "mower":
      return (
        <svg {...p}>
          <path d="M3 15h10l2-5h4M13 15l-2-8M4 15v3M13 15v3" />
          <circle cx="6" cy="19" r="2" />
          <circle cx="16" cy="19" r="2" />
          <path d="M8 19h6" />
        </svg>
      );
    case "grounds":
      return (
        <svg {...p}>
          <path d="M12 21V11M12 11c-4 0-6-3-6-7 4 0 6 2 6 7zM12 13c0-4 2-6 6-6 0 4-2 6-6 6z" />
          <path d="M4 21h16" />
        </svg>
      );
    case "clearup":
      return (
        <svg {...p}>
          <path d="M4 20l6-6M14 4l6 6-8 8-6-6 8-8zM9 15l-3 5" />
          <path d="M16 6l2 2" />
        </svg>
      );
    case "landscape":
      return (
        <svg {...p}>
          <path d="M3 19c3-4 6-6 9-6s6 2 9 6H3z" />
          <path d="M12 13V7M9 9c0-2 1.5-4 3-4s3 2 3 4" />
          <path d="M6 19c1-2 2-3 4-3" />
        </svg>
      );
    case "schedule":
      return (
        <svg {...p}>
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M3 10h18M8 3v4M16 3v4M8 15l2 2 4-4" />
        </svg>
      );
  }
}

export function MailIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden {...stroke}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 7l9 6 9-6" />
    </svg>
  );
}

export function PhoneIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden {...stroke}>
      <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z" />
    </svg>
  );
}

export function PinIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden {...stroke}>
      <path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}
