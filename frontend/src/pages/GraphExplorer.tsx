import React, { useEffect, useState } from "react";
import GraphView from "../components/Graph/GraphView";
import { getNodes, getEdges } from "../api/grafo";

export default function GraphExplorer() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  useEffect(() => {
    (async () => {
      try {
        const n = await getNodes();
        const e = await getEdges();
        setNodes(n.nodes ?? []);
        setEdges(e.edges ?? []);
      } catch (err) {
        console.error(err);
      }
    })();
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Explorer — Grafo</h2>
      <div className="bg-slate-800 p-4 rounded shadow">
        <GraphView nodes={nodes} edges={edges} />
      </div>
    </div>
  );
}
