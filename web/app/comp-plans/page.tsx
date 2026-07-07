import { ApiOffline } from "@/components/ApiOffline";
import { CompPlanComparator } from "@/components/CompPlanComparator";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CompPlansPage() {
  try {
    const [plans, meta] = await Promise.all([api.getCompPlans(), api.getCompPlansMeta()]);

    return (
      <div className="space-y-8">
        <header>
          <p className="text-sm uppercase tracking-[0.25em] text-road-amber">Pay decisions</p>
          <h2 className="mt-2 text-4xl font-semibold text-white">Comp Plan Comparator</h2>
          <p className="mt-3 max-w-3xl text-sm text-road-muted">
            Compare W-2, 1099, lease-on, and owner-op offers on estimated weekly net, annual net,
            net per mile, net per on-duty hour, and risk — not headline gross alone.
          </p>
        </header>

        <CompPlanComparator initialPlans={plans} disclaimer={meta.disclaimer} />
      </div>
    );
  } catch {
    return (
      <div className="space-y-8">
        <header>
          <h2 className="text-4xl font-semibold text-white">Comp Plan Comparator</h2>
        </header>
        <ApiOffline />
      </div>
    );
  }
}