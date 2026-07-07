import { ApiOffline } from "@/components/ApiOffline";
import { StatCard } from "@/components/StatCard";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let stats;
  let trips;
  let fuelReport;

  try {
    [stats, trips, fuelReport] = await Promise.all([
      api.getStats(),
      api.getTrips(8),
      api.getFuelReport(),
    ]);
  } catch {
    return (
      <div className="space-y-8">
        <header>
          <h2 className="text-4xl font-semibold text-white">Command Dashboard</h2>
        </header>
        <ApiOffline />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm uppercase tracking-[0.25em] text-road-amber">Operations</p>
        <h2 className="mt-2 text-4xl font-semibold text-white">Command Dashboard</h2>
        <p className="mt-2 max-w-2xl text-road-muted">
          Fleet snapshot, recent runs, and fuel efficiency at a glance.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total trips" value={stats.trip_count} />
        <StatCard label="Fleet avg MPG" value={stats.avg_mpg || "—"} />
        <StatCard label="Drivers / Trucks" value={`${stats.driver_count} / ${stats.truck_count}`} />
        <StatCard
          label="Total miles"
          value={stats.total_miles.toLocaleString()}
          hint={`${stats.total_fuel} gal logged`}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="panel">
          <h3 className="text-lg font-semibold text-white">Recent trips</h3>
          <div className="table-shell mt-4">
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Driver</th>
                  <th>Truck</th>
                  <th>Miles</th>
                  <th>MPG</th>
                </tr>
              </thead>
              <tbody>
                {trips.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-road-muted">
                      No trips logged yet.
                    </td>
                  </tr>
                ) : (
                  trips.map((trip) => (
                    <tr key={trip.id}>
                      <td>{trip.logged_at}</td>
                      <td>{trip.driver_id}</td>
                      <td>{trip.truck_number}</td>
                      <td>{trip.miles_driven}</td>
                      <td>{trip.mpg}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <h3 className="text-lg font-semibold text-white">Fuel efficiency</h3>
          <div className="table-shell mt-4">
            <table>
              <thead>
                <tr>
                  <th>Driver</th>
                  <th>Trips</th>
                  <th>Miles</th>
                  <th>Avg MPG</th>
                </tr>
              </thead>
              <tbody>
                {fuelReport.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-road-muted">
                      No fuel data yet.
                    </td>
                  </tr>
                ) : (
                  fuelReport.map((row) => (
                    <tr key={row.driver_id}>
                      <td>{row.driver_id}</td>
                      <td>{row.trip_count}</td>
                      <td>{row.total_miles}</td>
                      <td>{row.avg_mpg}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}