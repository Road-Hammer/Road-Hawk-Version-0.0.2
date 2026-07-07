import { ApiOffline } from "@/components/ApiOffline";
import { ExportButton } from "@/components/ExportButton";
import { TripForm } from "@/components/TripForm";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function TripsPage() {
  let trips;
  try {
    trips = await api.getTrips(30);
  } catch {
    return (
      <div className="space-y-8">
        <header>
          <h2 className="text-4xl font-semibold text-white">Trip log</h2>
        </header>
        <ApiOffline />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-road-amber">Trips</p>
          <h2 className="mt-2 text-4xl font-semibold text-white">Trip log</h2>
        </div>
        <ExportButton />
      </header>

      <TripForm />

      <div className="panel">
        <h3 className="text-lg font-semibold text-white">Trip history</h3>
        <div className="table-shell mt-4">
          <table>
            <thead>
              <tr>
                <th>Logged</th>
                <th>Driver</th>
                <th>Truck</th>
                <th>Miles</th>
                <th>Fuel</th>
                <th>MPG</th>
                <th>Cost</th>
                <th>Location</th>
              </tr>
            </thead>
            <tbody>
              {trips.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-road-muted">
                    No trips yet.
                  </td>
                </tr>
              ) : (
                trips.map((trip) => (
                  <tr key={trip.id}>
                    <td>{trip.logged_at}</td>
                    <td>{trip.driver_id}</td>
                    <td>{trip.truck_number}</td>
                    <td>{trip.miles_driven}</td>
                    <td>{trip.fuel_used}</td>
                    <td>{trip.mpg}</td>
                    <td>{trip.fuel_cost ?? "—"}</td>
                    <td>{trip.location ?? "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}