import React, { useEffect, useState } from "react";
import { getNodes, getEdges, triggerExportHtmls } from "../api/grafo";
import MetricsPanel from "../components/Metrics/MetricsPanel";

export default function Dashboard() {
  const [nodesCount, setNodesCount] = useState<number | null>(null);
  const [edgesCount, setEdgesCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const nodes = await getNodes();
        const edges = await getEdges();
        setNodesCount(nodes.count ?? (nodes.nodes ? nodes.nodes.length : null));
        setEdgesCount(edges.count ?? (edges.edges ? edges.edges.length : null));
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  return (
    <section>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-800 p-4 rounded shadow">
          <h3 className="text-sm text-slate-300">Ordem (nós)</h3>
          <div className="text-2xl font-bold">{nodesCount ?? "—"}</div>
        </div>
        <div className="bg-slate-800 p-4 rounded shadow">
          <h3 className="text-sm text-slate-300">Tamanho (arestas)</h3>
          <div className="text-2xl font-bold">{edgesCount ?? "—"}</div>
        </div>
        <div className="bg-slate-800 p-4 rounded shadow">
          <h3 className="text-sm text-slate-300">Export</h3>
          <button
            className="mt-2 bg-indigo-600 px-3 py-2 rounded"
            onClick={async () => {
              setLoading(true);
              try {
                await triggerExportHtmls();
                alert("HTMLs gerados no backend (ver out/).");
              } catch (e) {
                alert("Erro ao pedir geração: " + e);
              } finally {
                setLoading(false);
              }
            }}
          >
            {loading ? "Gerando..." : "Gerar HTMLs Estáticos"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-800 p-4 rounded shadow">
          <h2 className="text-lg font-semibold mb-2">Métricas</h2>
          <MetricsPanel />
        </div>

        <div className="bg-slate-800 p-4 rounded shadow">
          <h2 className="text-lg font-semibold mb-2">Sobre</h2>
          <p className="text-slate-300 text-sm">
            Painel simples para explorar o grafo. Use o Explorer para visualizar
            a rede e a aba Dijkstra para calcular rotas.
          </p>
        </div>
      </div>
    </section>
  );
}
