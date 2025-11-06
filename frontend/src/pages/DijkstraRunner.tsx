import React, { useEffect, useState } from "react";
import DijkstraForm from "../components/Dijkstra/DijkstraForm";
import PathResult from "../components/Dijkstra/PathResult";

export default function DijkstraRunner() {
  const [result, setResult] = useState<any | null>(null);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Dijkstra — Rota</h2>
      <div className="bg-slate-800 p-4 rounded shadow">
        <DijkstraForm onResult={(r) => setResult(r)} />
      </div>

      {result && (
        <div className="bg-slate-800 p-4 rounded shadow">
          <PathResult result={result} />
        </div>
      )}
    </div>
  );
}
