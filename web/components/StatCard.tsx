type StatCardProps = {
  label: string;
  value: string | number;
  hint?: string;
};

export function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <div className="panel">
      <p className="text-sm text-road-muted">{label}</p>
      <p className="stat-value mt-2">{value}</p>
      {hint ? <p className="mt-2 text-xs text-road-muted">{hint}</p> : null}
    </div>
  );
}