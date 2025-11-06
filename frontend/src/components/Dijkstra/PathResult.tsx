import React from "react";

export default function PathResult({ result }: { result: any }) {
  if (!result) return null;
  return (
    <div className="space-y-3">
      <div>
        <strong>Custo:</strong> {result.custo ?? result.cost ?? "—"}
      </div>
      <div>
        <strong>Caminho:</strong>
        <ol className="list-decimal list-inside ml-4">
          {(result.caminho ?? result.path ?? []).map((p: string, i: number) => (
            <li key={i}>{p}</li>
          ))}
        </ol>
      </div>
      <div>
        <strong>Ruas:</strong>
        <ul className="ml-4 list-disc text-sm text-slate-200">
          {(result.ruas ?? result.ruas_used ?? []).map(
            (r: string, i: number) => (
              <li key={i}>{r}</li>
            )
          )}
        </ul>
      </div>
    </div>
  );
}
