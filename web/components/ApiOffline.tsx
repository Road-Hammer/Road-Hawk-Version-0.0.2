export function ApiOffline() {
  return (
    <div className="panel max-w-2xl">
      <h2 className="text-2xl font-semibold text-white">API offline</h2>
      <p className="mt-3 text-road-muted">
        Start the Road Hawk API first, then refresh this page.
      </p>
      <pre className="mt-4 overflow-x-auto rounded-lg bg-black/30 p-4 text-sm text-road-amber">
        pip install -e .{"\n"}
        road-hawk-api
      </pre>
    </div>
  );
}