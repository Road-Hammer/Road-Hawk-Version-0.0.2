import { ConnectPanel } from "@/components/ConnectPanel";

export default function ConnectPage() {
  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm uppercase tracking-[0.25em] text-road-amber">Connection</p>
        <h2 className="mt-2 text-4xl font-semibold text-white">Standalone or server</h2>
        <p className="mt-3 max-w-3xl text-sm text-road-muted">
          Choose whether this dashboard runs locally, hosts a fleet server, or connects remotely.
          Remote users sign in here when the server requires authentication.
        </p>
      </header>

      <ConnectPanel />
    </div>
  );
}