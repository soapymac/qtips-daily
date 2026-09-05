import Script from "next/script";

/**
 * Optional analytics hook. Nothing renders unless an env var is set:
 *   NEXT_PUBLIC_PLAUSIBLE_DOMAIN  -> Plausible (cookie-free, no banner needed)
 *   NEXT_PUBLIC_GA_MEASUREMENT_ID -> Google Analytics 4 (consider a cookie
 *                                    banner before enabling in the UK)
 */
export function Analytics() {
  const plausible = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN;
  const ga = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

  if (plausible) {
    return <Script defer data-domain={plausible} src="https://plausible.io/js/script.js" strategy="afterInteractive" />;
  }

  if (ga) {
    return (
      <>
        <Script src={`https://www.googletagmanager.com/gtag/js?id=${ga}`} strategy="afterInteractive" />
        <Script id="ga4" strategy="afterInteractive">
          {`window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${ga}',{anonymize_ip:true});`}
        </Script>
      </>
    );
  }

  return null;
}
