import React, { useEffect, useState } from "react";
import { getNodes, runDijkstra } from "../../api/grafo";

type Props = { onResult: (r: any) => void };

export default function DijkstraForm({ onResult }: Props) {
  const [nodes, setNodes] = useState<string[]>([]);
  const [origem, setOrigem] = useState("");
  const [destino, setDestino] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const r = await getNodes();
        const list = (r.nodes ?? []).map((n: any) => n.id);
        setNodes(list.sort());
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await runDijkstra(origem, destino);
      onResult(r);
    } catch (err) {
      alert("Erro: " + String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <select
          value={origem}
          onChange={(e) => setOrigem(e.target.value)}
          required
          className="p-2 rounded bg-slate-700 w-full"
        >
          <option value="">Escolha origem</option>
          {nodes.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
        <select
          value={destino}
          onChange={(e) => setDestino(e.target.value)}
          required
          className="p-2 rounded bg-slate-700 w-full"
        >
          <option value="">Escolha destino</option>
          {nodes.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          className="bg-indigo-600 px-4 py-2 rounded"
          disabled={loading}
        >
          {loading ? "Calculando..." : "Calcular"}
        </button>
      </div>
    </form>
  );
}
