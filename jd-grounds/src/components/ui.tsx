import Link from "next/link";
import type { ReactNode } from "react";

export function Container({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`mx-auto w-full max-w-6xl px-5 sm:px-8 ${className}`}>{children}</div>;
}

type ButtonProps = {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "light";
  size?: "md" | "lg";
  className?: string;
};

const base =
  "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-earth-400/60";
const variants = {
  primary: "bg-green-800 text-cream-50 hover:bg-green-900 active:bg-green-950",
  secondary: "bg-earth-400 text-green-950 hover:bg-[#d9b283] active:bg-[#bd9260]",
  ghost: "border-2 border-green-800 text-green-900 hover:bg-green-100",
  light: "bg-cream-100 text-green-950 hover:bg-white",
};
const sizes = { md: "px-5 py-2.5 text-sm sm:text-[15px]", lg: "px-7 py-3.5 text-base" };

export function Button({ href, children, variant = "primary", size = "md", className = "" }: ButtonProps) {
  const cls = `${base} ${variants[variant]} ${sizes[size]} ${className}`;
  if (href.startsWith("mailto:") || href.startsWith("tel:")) {
    return (
      <a href={href} className={cls}>
        {children}
      </a>
    );
  }
  return (
    <Link href={href} className={cls}>
      {children}
    </Link>
  );
}

export function Eyebrow({ children, tone = "dark" }: { children: ReactNode; tone?: "dark" | "light" }) {
  return (
    <p className={`text-xs font-bold uppercase tracking-[0.18em] ${tone === "light" ? "text-green-200" : "text-green-700"}`}>
      {children}
    </p>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  intro,
  tone = "dark",
  align = "left",
}: {
  eyebrow?: string;
  title: string;
  intro?: string;
  tone?: "dark" | "light";
  align?: "left" | "center";
}) {
  const alignCls = align === "center" ? "mx-auto text-center" : "";
  return (
    <div className={`max-w-2xl ${alignCls}`}>
      {eyebrow && <Eyebrow tone={tone}>{eyebrow}</Eyebrow>}
      <h2 className={`mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl ${tone === "light" ? "text-cream-50" : "text-green-950"}`}>
        {title}
      </h2>
      {intro && <p className={`mt-4 text-lg leading-relaxed ${tone === "light" ? "text-green-100" : "text-muted"}`}>{intro}</p>}
    </div>
  );
}

export function PageHero({ eyebrow, title, intro, children }: { eyebrow: string; title: string; intro: string; children?: ReactNode }) {
  return (
    <section className="relative overflow-hidden bg-green-950 text-cream-50">
      <div aria-hidden className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgb(42_107_69_/_0.55),transparent_60%)]" />
      <Container className="relative py-16 sm:py-24">
        <Eyebrow tone="light">{eyebrow}</Eyebrow>
        <h1 className="mt-3 max-w-3xl text-4xl font-extrabold tracking-tight sm:text-5xl">{title}</h1>
        <p className="mt-5 max-w-2xl text-lg leading-relaxed text-green-100 sm:text-xl">{intro}</p>
        {children}
      </Container>
      <GroundLine />
    </section>
  );
}

/** Decorative rolling ground line used to end dark sections. */
export function GroundLine({ fill = "#f7f3ea" }: { fill?: string }) {
  return (
    <svg aria-hidden className="block w-full" viewBox="0 0 1440 40" preserveAspectRatio="none" height="40">
      <path d="M0 40V22C240 6 480 6 720 20s480 14 720 0v20H0z" fill={fill} />
    </svg>
  );
}

export function Check({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 20 20" fill="none" className={className}>
      <circle cx="10" cy="10" r="10" fill="currentColor" opacity="0.15" />
      <path d="M6 10.5l2.6 2.5L14 7.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
