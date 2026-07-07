"use client";

import { ChangeEvent, FormEvent, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type CompPlanSummary = {
  id: number;
  company_name: string;
  position_type: string;
  pay_method: string;
  notes: string | null;
  base_result: {
    weekly_net: number;
    annual_net: number;
    net_per_dispatched_mile: number;
    net_per_hour: number;
    risk_level: string;
  } | null;
};

type RankedResult = {
  rank: number;
  plan_id: number;
  company_name: string;
  position_type: string;
  pay_method: string;
  weekly_net: number;
  monthly_net: number;
  annual_net: number;
  net_per_dispatched_mile: number;
  net_per_hour: number;
  risk_level: string;
  flags: Array<{ level: string; message: string }>;
  notes: string | null;
  calculation_notes: string;
};

const POSITION_LABELS: Record<string, string> = {
  w2: "W-2",
  contractor_1099: "1099",
  lease_on: "Lease-on",
  owner_op: "Owner-op",
};

function money(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function riskClass(level: string) {
  if (level === "high") return "text-red-400";
  if (level === "medium") return "text-amber-300";
  return "text-emerald-400";
}

export function CompPlanComparator({
  initialPlans,
  disclaimer,
}: {
  initialPlans: CompPlanSummary[];
  disclaimer: string;
}) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [plans, setPlans] = useState(initialPlans);
  const [selectedIds, setSelectedIds] = useState<number[]>(initialPlans.map((p) => p.id));
  const [scenario, setScenario] = useState("base");
  const [ranked, setRanked] = useState<RankedResult[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const allSelected = useMemo(
    () => plans.length > 0 && selectedIds.length === plans.length,
    [plans.length, selectedIds.length],
  );

  function togglePlan(planId: number) {
    setSelectedIds((current) =>
      current.includes(planId) ? current.filter((id) => id !== planId) : [...current, planId],
    );
  }

  async function onAddPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy("add");
    setMessage(null);
    setError(null);
    const form = new FormData(event.currentTarget);

    const num = (name: string) => Number(form.get(name) || 0);
    const flagsRaw = String(form.get("flags") || "").trim();
    const flags = flagsRaw
      ? flagsRaw.split("\n").map((line) => {
          const [level, ...rest] = line.split(":");
          return { level: level.trim().toLowerCase(), message: rest.join(":").trim() };
        })
      : [];

    try {
      await api.createCompPlan({
        company_name: String(form.get("company_name")),
        position_type: String(form.get("position_type")),
        pay_method: String(form.get("pay_method")),
        notes: String(form.get("notes") || ""),
        flags,
        scenarios: [
          {
            scenario_type: "base",
            weekly_miles: num("weekly_miles"),
            weekly_hours: num("weekly_hours"),
            loaded_miles: num("loaded_miles"),
            empty_miles: num("empty_miles"),
            gross_pay_weekly: num("gross_pay_weekly"),
            accessorials_weekly: num("accessorials_weekly"),
            bonuses_weekly: num("bonuses_weekly"),
            benefits_value_weekly: num("benefits_value_weekly"),
            payroll_tax_weekly: num("payroll_tax_weekly"),
            income_tax_reserve_weekly: num("income_tax_reserve_weekly"),
            self_employment_tax_weekly: num("self_employment_tax_weekly"),
            health_insurance_weekly: num("health_insurance_weekly"),
            retirement_weekly: num("retirement_weekly"),
            truck_payment_weekly: num("truck_payment_weekly"),
            trailer_rental_weekly: num("trailer_rental_weekly"),
            maintenance_escrow_weekly: num("maintenance_escrow_weekly"),
            performance_escrow_weekly: num("performance_escrow_weekly"),
            insurance_weekly: num("insurance_weekly"),
            fuel_weekly: num("fuel_weekly"),
            tolls_weekly: num("tolls_weekly"),
            admin_fees_weekly: num("admin_fees_weekly"),
            carrier_percentage: num("carrier_percentage"),
            other_deductions_weekly: num("other_deductions_weekly"),
            downtime_reserve_weekly: num("downtime_reserve_weekly"),
          },
        ],
      });
      setMessage("Compensation plan saved.");
      event.currentTarget.reset();
      router.refresh();
      const refreshed = await api.getCompPlans();
      setPlans(refreshed);
      setSelectedIds(refreshed.map((plan) => plan.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save plan");
    } finally {
      setBusy(null);
    }
  }

  async function onCompare() {
    if (selectedIds.length === 0) {
      setError("Select at least one plan to compare.");
      return;
    }
    setBusy("compare");
    setError(null);
    try {
      const result = await api.compareCompPlans(selectedIds, scenario);
      setRanked(result.results);
      setMessage(`Compared ${result.results.length} plan(s) on ${scenario} scenario.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compare failed");
    } finally {
      setBusy(null);
    }
  }

  async function onDelete(planId: number, companyName: string) {
    setBusy("delete");
    setError(null);
    try {
      await api.deleteCompPlan(planId);
      const refreshed = await api.getCompPlans();
      setPlans(refreshed);
      setSelectedIds((current) => current.filter((id) => id !== planId));
      setRanked((current) => current.filter((row) => row.plan_id !== planId));
      setMessage(`Removed ${companyName}.`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setBusy(null);
    }
  }

  async function onExport() {
    setBusy("export");
    setError(null);
    try {
      await api.exportCompPlans();
      setMessage("Comparison export downloaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusy(null);
    }
  }

  async function onImportSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setBusy("import");
    setError(null);
    try {
      const result = await api.importCompPlans(file);
      setMessage(result.message);
      const refreshed = await api.getCompPlans();
      setPlans(refreshed);
      setSelectedIds(refreshed.map((plan) => plan.id));
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-8">
      <section className="panel border-amber-500/20 bg-amber-500/5 text-sm text-road-muted">
        <strong className="text-road-amber">Estimate disclaimer:</strong> {disclaimer}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <form onSubmit={onAddPlan} className="panel space-y-4">
          <h3 className="text-lg font-semibold text-white">Add compensation plan</h3>
          <input className="input" name="company_name" placeholder="Company name" required />
          <div className="grid gap-4 md:grid-cols-2">
            <select className="input" name="position_type" defaultValue="w2" required>
              <option value="w2">W-2</option>
              <option value="contractor_1099">1099 contractor</option>
              <option value="lease_on">Lease-on</option>
              <option value="owner_op">Owner-op</option>
            </select>
            <select className="input" name="pay_method" defaultValue="per_mile">
              <option value="per_mile">Per mile</option>
              <option value="hourly">Hourly</option>
              <option value="percentage">Percentage</option>
              <option value="salary">Salary</option>
              <option value="load_pay">Load pay</option>
              <option value="mixed">Mixed</option>
            </select>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <input className="input" name="weekly_miles" type="number" step="any" placeholder="Weekly miles" />
            <input className="input" name="weekly_hours" type="number" step="any" placeholder="Weekly on-duty hours" />
            <input className="input" name="loaded_miles" type="number" step="any" placeholder="Loaded miles" />
            <input className="input" name="empty_miles" type="number" step="any" placeholder="Empty miles" />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <input className="input" name="gross_pay_weekly" type="number" step="any" placeholder="Gross pay (weekly)" required />
            <input className="input" name="accessorials_weekly" type="number" step="any" placeholder="Accessorials (weekly)" />
            <input className="input" name="bonuses_weekly" type="number" step="any" placeholder="Bonuses (weekly)" />
            <input className="input" name="benefits_value_weekly" type="number" step="any" placeholder="Benefits value (W-2)" />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <input className="input" name="payroll_tax_weekly" type="number" step="any" placeholder="Payroll tax reserve" />
            <input className="input" name="income_tax_reserve_weekly" type="number" step="any" placeholder="Income tax reserve" />
            <input className="input" name="self_employment_tax_weekly" type="number" step="any" placeholder="Self-employment tax reserve" />
            <input className="input" name="health_insurance_weekly" type="number" step="any" placeholder="Health insurance" />
            <input className="input" name="retirement_weekly" type="number" step="any" placeholder="Retirement contribution" />
            <input className="input" name="carrier_percentage" type="number" step="any" placeholder="Carrier % (lease-on)" />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <input className="input" name="truck_payment_weekly" type="number" step="any" placeholder="Truck payment" />
            <input className="input" name="maintenance_escrow_weekly" type="number" step="any" placeholder="Maintenance escrow" />
            <input className="input" name="performance_escrow_weekly" type="number" step="any" placeholder="Performance escrow" />
            <input className="input" name="insurance_weekly" type="number" step="any" placeholder="Insurance" />
            <input className="input" name="fuel_weekly" type="number" step="any" placeholder="Fuel" />
            <input className="input" name="tolls_weekly" type="number" step="any" placeholder="Tolls" />
            <input className="input" name="admin_fees_weekly" type="number" step="any" placeholder="Admin / ELD fees" />
            <input className="input" name="downtime_reserve_weekly" type="number" step="any" placeholder="Downtime reserve" />
            <input className="input" name="other_deductions_weekly" type="number" step="any" placeholder="Other deductions" />
          </div>

          <textarea
            className="input min-h-20"
            name="flags"
            placeholder="Risk flags (one per line): red: excessive escrow"
          />
          <textarea className="input min-h-20" name="notes" placeholder="Notes" />
          <button className="btn-primary" type="submit" disabled={busy !== null}>
            {busy === "add" ? "Saving..." : "Save plan"}
          </button>
        </form>

        <div className="panel space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-lg font-semibold text-white">Saved plans</h3>
            <div className="flex flex-wrap gap-2">
              <button className="btn-secondary" type="button" onClick={onExport} disabled={busy !== null}>
                Export CSV
              </button>
              <button
                className="btn-secondary"
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={busy !== null}
              >
                Import CSV
              </button>
              <input ref={fileInputRef} type="file" accept=".csv" className="hidden" onChange={onImportSelected} />
            </div>
          </div>

          <div className="table-shell">
            <table>
              <thead>
                <tr>
                  <th>
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={() =>
                        setSelectedIds(allSelected ? [] : plans.map((plan) => plan.id))
                      }
                    />
                  </th>
                  <th>Company</th>
                  <th>Type</th>
                  <th>Weekly net</th>
                  <th>Risk</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {plans.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-road-muted">
                      No plans yet. Add W-2, 1099, or lease-on offers to compare true estimated net.
                    </td>
                  </tr>
                ) : (
                  plans.map((plan) => (
                    <tr key={plan.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(plan.id)}
                          onChange={() => togglePlan(plan.id)}
                        />
                      </td>
                      <td>{plan.company_name}</td>
                      <td>{POSITION_LABELS[plan.position_type] ?? plan.position_type}</td>
                      <td>
                        {plan.base_result ? money(plan.base_result.weekly_net) : "—"}
                      </td>
                      <td className={plan.base_result ? riskClass(plan.base_result.risk_level) : ""}>
                        {plan.base_result?.risk_level ?? "—"}
                      </td>
                      <td>
                        <button
                          className="btn-secondary"
                          type="button"
                          onClick={() => onDelete(plan.id, plan.company_name)}
                          disabled={busy !== null}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select className="input max-w-xs" value={scenario} onChange={(e) => setScenario(e.target.value)}>
              <option value="conservative">Conservative scenario</option>
              <option value="base">Base scenario</option>
              <option value="best">Best case scenario</option>
            </select>
            <button className="btn-primary" type="button" onClick={onCompare} disabled={busy !== null}>
              {busy === "compare" ? "Comparing..." : "Compare selected plans"}
            </button>
          </div>
        </div>
      </section>

      <section className="panel">
        <h3 className="text-lg font-semibold text-white">Ranked comparison</h3>
        <p className="mt-2 text-sm text-road-muted">
          Sorted by estimated weekly net — not gross pay. Highest gross is not automatically the winner.
        </p>
        <div className="table-shell mt-4">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Company</th>
                <th>Type</th>
                <th>Weekly net</th>
                <th>Annual net</th>
                <th>Net/mile</th>
                <th>Net/hour</th>
                <th>Risk</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {ranked.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-road-muted">
                    Run a comparison to see ranked estimated net outcomes.
                  </td>
                </tr>
              ) : (
                ranked.map((row) => (
                  <tr key={row.plan_id}>
                    <td>{row.rank}</td>
                    <td>{row.company_name}</td>
                    <td>{POSITION_LABELS[row.position_type] ?? row.position_type}</td>
                    <td>{money(row.weekly_net)}</td>
                    <td>{money(row.annual_net)}</td>
                    <td>${row.net_per_dispatched_mile.toFixed(2)}</td>
                    <td>{row.net_per_hour ? money(row.net_per_hour) : "—"}</td>
                    <td className={riskClass(row.risk_level)}>{row.risk_level}</td>
                    <td className="max-w-xs text-xs text-road-muted">
                      {row.flags?.length
                        ? row.flags.map((flag) => `${flag.level}: ${flag.message}`).join(" · ")
                        : row.calculation_notes || row.notes || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {message ? <p className="text-sm text-emerald-400">{message}</p> : null}
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
    </div>
  );
}