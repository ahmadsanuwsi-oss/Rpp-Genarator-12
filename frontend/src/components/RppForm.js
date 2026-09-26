import React from "react";
import { RPP_IDENTITAS, RPP_SECTIONS } from "@/lib/docTypes";

export default function RppForm({ fields, setField }) {
  return (
    <div className="space-y-6">
      <section className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-base font-bold text-slate-900 mb-4">Identitas</h3>
        <div className="grid sm:grid-cols-2 gap-4">
          {RPP_IDENTITAS.map((f) => (
            <div key={f.key}>
              <label className="block text-xs font-semibold uppercase tracking-wider text-emerald-800 mb-1">{f.label}</label>
              <input
                data-testid={`rpp-input-${f.key}`}
                value={fields[f.key] || ""}
                onChange={(e) => setField(f.key, e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-none text-sm"
              />
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-base font-bold text-slate-900 mb-4">Komponen Pembelajaran</h3>
        <div className="space-y-4">
          {RPP_SECTIONS.map((f) => (
            <div key={f.key}>
              <label className="block text-xs font-semibold uppercase tracking-wider text-emerald-800 mb-1">{f.label}</label>
              <textarea
                data-testid={`rpp-input-${f.key}`}
                value={fields[f.key] || ""}
                onChange={(e) => setField(f.key, e.target.value)}
                rows={f.key === "kegiatanInti" ? 6 : 3}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-none text-sm leading-relaxed resize-y"
              />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
