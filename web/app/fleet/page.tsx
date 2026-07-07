import { ApiOffline } from "@/components/ApiOffline";
import { DriverForm, TruckForm } from "@/components/FleetForms";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function FleetPage() {
  let drivers;
  let trucks;
  try {
    [drivers, trucks] = await Promise.all([api.getDrivers(), api.getTrucks()]);
  } catch {
    return (
      <div className="space-y-8">
        <header>
          <h2 className="text-4xl font-semibold text-white">Drivers and trucks</h2>
        </header>
        <ApiOffline />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm uppercase tracking-[0.25em] text-road-amber">Fleet</p>
        <h2 className="mt-2 text-4xl font-semibold text-white">Drivers and trucks</h2>
      </header>

      <section className="grid gap-6 xl:grid-cols-2">
        <DriverForm />
        <TruckForm />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="panel">
          <h3 className="text-lg font-semibold text-white">Drivers</h3>
          <div className="table-shell mt-4">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                </tr>
              </thead>
              <tbody>
                {drivers.length === 0 ? (
                  <tr>
                    <td colSpan={2} className="text-road-muted">
                      No drivers registered.
                    </td>
                  </tr>
                ) : (
                  drivers.map((driver) => (
                    <tr key={driver.driver_id}>
                      <td>{driver.driver_id}</td>
                      <td>{driver.name}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <h3 className="text-lg font-semibold text-white">Trucks</h3>
          <div className="table-shell mt-4">
            <table>
              <thead>
                <tr>
                  <th>Number</th>
                  <th>Make / Model</th>
                  <th>Year</th>
                </tr>
              </thead>
              <tbody>
                {trucks.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="text-road-muted">
                      No trucks registered.
                    </td>
                  </tr>
                ) : (
                  trucks.map((truck) => (
                    <tr key={truck.truck_number}>
                      <td>{truck.truck_number}</td>
                      <td>
                        {[truck.make, truck.model].filter(Boolean).join(" ") || "—"}
                      </td>
                      <td>{truck.year ?? "—"}</td>
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