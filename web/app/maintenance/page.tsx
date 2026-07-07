import { ApiOffline } from "@/components/ApiOffline";
import { MaintenanceForm } from "@/components/MaintenanceForm";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function MaintenancePage() {
  let records;
  try {
    records = await api.getMaintenance(30);
  } catch {
    return (
      <div className="space-y-8">
        <header>
          <h2 className="text-4xl font-semibold text-white">Service records</h2>
        </header>
        <ApiOffline />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm uppercase tracking-[0.25em] text-road-amber">Maintenance</p>
        <h2 className="mt-2 text-4xl font-semibold text-white">Service records</h2>
      </header>

      <MaintenanceForm />

      <div className="panel">
        <h3 className="text-lg font-semibold text-white">Recent maintenance</h3>
        <div className="table-shell mt-4">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Truck</th>
                <th>Details</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {records.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-road-muted">
                    No maintenance records yet.
                  </td>
                </tr>
              ) : (
                records.map((record) => (
                  <tr key={record.id}>
                    <td>{record.service_date}</td>
                    <td>{record.truck_number}</td>
                    <td>{record.details}</td>
                    <td>{record.cost ?? "—"}</td>
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