import { Button, Container } from "@/components/ui";

export default function NotFound() {
  return (
    <section className="bg-cream-100 py-24">
      <Container className="max-w-xl text-center">
        <p className="text-xs font-bold tracking-[0.18em] text-green-700 uppercase">Page not found</p>
        <h1 className="mt-3 text-4xl font-extrabold tracking-tight text-green-950">That page has been mown over.</h1>
        <p className="mt-4 text-lg text-muted">The link may be old or mistyped. Head back to the home page or get in touch.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Button href="/">Home</Button>
          <Button href="/contact" variant="ghost">
            Contact
          </Button>
        </div>
      </Container>
    </section>
  );
}
