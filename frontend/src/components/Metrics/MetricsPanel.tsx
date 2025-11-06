import React, { useEffect, useState } from "react";
import { getNodes } from "../../api/grafo";

export default function MetricsPanel() {
  const [nodes, setNodes] = useState<any[]>([]);
  useEffect(() => {
    (async () => {
      try {
        const r = await getNodes();
        setNodes(r.nodes ?? []);
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  const sample = nodes.slice(0, 8);

  return (
    <div>
      <h3 className="text-sm text-slate-300 mb-2">Amostra de nós</h3>
      <ul className="text-sm space-y-2">
        {sample.map((n: any) => (
          <li key={n.id} className="bg-slate-700 p-2 rounded">
            <div className="flex justify-between">
              <span className="font-medium">{n.id}</span>
              <span className="text-slate-300 text-xs">
                grau: {n.grau ?? "-"}
              </span>
            </div>
            <div className="text-xs text-slate-400">
              microrregião: {String(n.microrregiao ?? "-")}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
