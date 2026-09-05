"use client";

export function PrintButton() {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className="rounded-full bg-green-800 px-4 py-1.5 font-semibold text-cream-50 hover:bg-green-900"
    >
      Print or save as PDF
    </button>
  );
}
