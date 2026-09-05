import { photoExists, photos, type PhotoKey } from "@/lib/images";
import { FieldIllustration } from "./FieldIllustration";

/**
 * Renders a photo slot: the real image if /public/images/<file> exists,
 * otherwise the field illustration. Credits render as a small caption when set.
 */
export function Photo({
  slot,
  className = "",
  priority = false,
  sizes = "(min-width: 1024px) 50vw, 100vw",
}: {
  slot: PhotoKey;
  className?: string;
  priority?: boolean;
  sizes?: string;
}) {
  const meta = photos[slot];
  const exists = photoExists(slot);
  return (
    <figure className={`relative overflow-hidden ${className}`}>
      {exists ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={`/images/${meta.file}`}
          alt={meta.alt}
          sizes={sizes}
          loading={priority ? "eager" : "lazy"}
          fetchPriority={priority ? "high" : "auto"}
          decoding="async"
          className="h-full w-full object-cover"
        />
      ) : (
        <FieldIllustration className="h-full w-full" variant={slot === "hero" ? "hero" : "card"} />
      )}
      {exists && meta.credit && (
        <figcaption className="absolute right-2 bottom-2 rounded-full bg-green-950/70 px-2.5 py-1 text-[11px] text-cream-100">
          Photo:{" "}
          {meta.creditUrl ? (
            <a href={meta.creditUrl} className="underline" rel="noopener noreferrer">
              {meta.credit}
            </a>
          ) : (
            meta.credit
          )}
        </figcaption>
      )}
    </figure>
  );
}
