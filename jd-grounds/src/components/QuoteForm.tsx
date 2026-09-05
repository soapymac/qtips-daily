"use client";

import { useState, type FormEvent } from "react";
import { business, cadences, siteTypes } from "@/lib/site";

type Status = "idle" | "sending" | "sent" | "error";

const ENDPOINT = process.env.NEXT_PUBLIC_FORM_ENDPOINT?.trim() || "";

const inputCls =
  "mt-1.5 block w-full rounded-lg border border-green-900/20 bg-white px-3.5 py-2.5 text-ink shadow-[inset_0_1px_2px_rgb(15_42_28_/_0.04)] placeholder:text-muted/70 focus:border-green-700 focus:outline-none focus:ring-4 focus:ring-green-200";
const labelCls = "block text-sm font-semibold text-green-950";

function buildMailto(data: FormData): string {
  const get = (k: string) => String(data.get(k) ?? "").trim();
  const subject = `Quote request: ${get("site") || get("name") || "commercial grounds"}`;
  const lines = [
    `Name: ${get("name")}`,
    `Business / site: ${get("site")}`,
    `Email: ${get("email")}`,
    `Phone: ${get("phone") || "-"}`,
    `Site type: ${get("siteType")}`,
    `Preferred cadence: ${get("cadence")}`,
    "",
    "What do you need?",
    get("message"),
  ];
  return `mailto:${business.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(lines.join("\n"))}`;
}

export function QuoteForm() {
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);

    // Honeypot: bots fill hidden fields; humans don't.
    if (String(data.get("company_website") ?? "").length > 0) {
      setStatus("sent");
      return;
    }

    if (!ENDPOINT) {
      // No endpoint configured: hand off to the visitor's email client, pre-filled.
      window.location.href = buildMailto(data);
      setStatus("sent");
      return;
    }

    setStatus("sending");
    setErrorMsg("");
    try {
      const payload: Record<string, string> = {};
      data.forEach((v, k) => {
        if (k !== "company_website") payload[k] = String(v);
      });
      payload._subject = `JD Grounds quote request: ${payload.site || payload.name}`;
      const res = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      setStatus("sent");
      form.reset();
    } catch (err) {
      setStatus("error");
      setErrorMsg(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  if (status === "sent") {
    return (
      <div role="status" aria-live="polite" className="rounded-2xl border border-green-300 bg-green-50 p-6 sm:p-8">
        <h3 className="text-xl font-extrabold text-green-950">Thanks, that&rsquo;s with us.</h3>
        <p className="mt-2 text-muted">
          {ENDPOINT
            ? "We'll read it and come back to you, usually within a working day."
            : "Your email app should have opened with the details filled in. If it didn't, email us directly and we'll pick it up."}
        </p>
        <p className="mt-4 text-sm">
          <a href={`mailto:${business.email}`} className="font-semibold text-green-800 underline underline-offset-4">
            {business.email}
          </a>{" "}
          ·{" "}
          <a href={business.phoneHref} className="font-semibold text-green-800 underline underline-offset-4">
            {business.phone}
          </a>
        </p>
        <button
          type="button"
          onClick={() => setStatus("idle")}
          className="mt-5 text-sm font-semibold text-green-800 underline underline-offset-4"
        >
          Send another request
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5" noValidate={false}>
      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor="name" className={labelCls}>
            Your name <span aria-hidden className="text-earth-600">*</span>
          </label>
          <input id="name" name="name" type="text" autoComplete="name" required className={inputCls} />
        </div>
        <div>
          <label htmlFor="site" className={labelCls}>
            Business or site name <span aria-hidden className="text-earth-600">*</span>
          </label>
          <input id="site" name="site" type="text" autoComplete="organization" required className={inputCls} placeholder="e.g. Seaview Holiday Park" />
        </div>
        <div>
          <label htmlFor="email" className={labelCls}>
            Email <span aria-hidden className="text-earth-600">*</span>
          </label>
          <input id="email" name="email" type="email" autoComplete="email" required className={inputCls} />
        </div>
        <div>
          <label htmlFor="phone" className={labelCls}>
            Phone <span className="font-normal text-muted">(optional)</span>
          </label>
          <input id="phone" name="phone" type="tel" autoComplete="tel" className={inputCls} />
        </div>
        <div>
          <label htmlFor="siteType" className={labelCls}>
            Type of site <span aria-hidden className="text-earth-600">*</span>
          </label>
          <select id="siteType" name="siteType" required defaultValue="" className={inputCls}>
            <option value="" disabled>
              Choose one
            </option>
            {siteTypes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="cadence" className={labelCls}>
            How often? <span aria-hidden className="text-earth-600">*</span>
          </label>
          <select id="cadence" name="cadence" required defaultValue="" className={inputCls}>
            <option value="" disabled>
              Choose one
            </option>
            {cadences.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="message" className={labelCls}>
          What do you need? <span aria-hidden className="text-earth-600">*</span>
        </label>
        <textarea
          id="message"
          name="message"
          rows={5}
          required
          className={inputCls}
          placeholder="Rough size of the grounds, which areas, any timing constraints (changeover days, term times, opening hours)…"
        />
      </div>

      {/* Honeypot: hidden from people, visible to bots */}
      <div className="absolute -left-[9999px] h-0 w-0 overflow-hidden" aria-hidden>
        <label htmlFor="company_website">Leave this empty</label>
        <input id="company_website" name="company_website" type="text" tabIndex={-1} autoComplete="off" />
      </div>

      <p className="text-sm text-muted">
        We only use these details to reply to your enquiry. See our{" "}
        <a href="/privacy" className="font-semibold text-green-800 underline underline-offset-4">
          privacy notice
        </a>
        .
      </p>

      {status === "error" && (
        <div role="alert" className="rounded-lg border border-earth-600/40 bg-[#fbf1e6] px-4 py-3 text-sm text-earth-800">
          <p className="font-semibold">Sorry, that didn&rsquo;t send.</p>
          <p className="mt-1">
            {errorMsg} Please try again, or email{" "}
            <a href={`mailto:${business.email}`} className="underline underline-offset-4">
              {business.email}
            </a>{" "}
            or call {business.phone}.
          </p>
        </div>
      )}

      <button
        type="submit"
        disabled={status === "sending"}
        className="inline-flex w-full items-center justify-center rounded-full bg-green-800 px-7 py-3.5 text-base font-semibold text-cream-50 hover:bg-green-900 disabled:cursor-wait disabled:opacity-70 sm:w-auto"
      >
        {status === "sending" ? "Sending…" : "Request a free quote"}
      </button>
    </form>
  );
}
