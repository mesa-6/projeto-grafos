import React, { useEffect, useRef } from "react";
import type { EdgeItem } from "../../utils/types";
import { Network } from "vis-network";

type Props = {
  nodes: Array<{ id: string; grau?: number }>;
  edges: Array<EdgeItem>;
};

export default function GraphView({ nodes, edges }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const networkRef = useRef<Network | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // transform nodes/edges to vis format
    const visNodes = (nodes || []).map((n) => ({
      id: n.id,
      label: n.id,
      title: `${n.id}\nGrau: ${n.grau ?? "-"}`,
      value: Math.max(1, n.grau ?? 1),
    }));

    const visEdges = (edges || []).map((e, i) => ({
      id: `edge-${i}`,
      from: e.bairro_origem,
      to: e.bairro_destino,
      title: `${e.logradouro ?? ""}\nPeso: ${e.peso ?? ""}`,
      value: Math.max(1, Number(e.peso ?? 1)),
    }));

    // small options tuned for readability
    const options = {
      physics: {
        barnesHut: {
          gravitationalConstant: -2000,
          springLength: 200,
          springConstant: 0.05,
          avoidOverlap: 0.9,
        },
        stabilization: { iterations: 300 },
      },
      nodes: {
        shape: "dot",
        scaling: { min: 6, max: 36 },
        font: { size: 12 },
      },
      edges: {
        smooth: true,
        scaling: { min: 1, max: 4 },
      },
    };

    // destroy previous
    if (networkRef.current) {
      try {
        // @ts-ignore - cleanup
        (networkRef.current as any).destroy();
      } catch (e) {}
      networkRef.current = null;
    }

    // create
    const net = new Network(
      containerRef.current,
      { nodes: visNodes, edges: visEdges },
      options
    );
    networkRef.current = net;

    // click behavior: highlight neighbors
    net.on("click", function (params: any) {
      if (!params.nodes || params.nodes.length === 0) {
        try {
          // use public API fit()
          (net as any).fit();
        } catch {}
        return;
      }
      const nodeId = params.nodes[0];
      const neighbors = (net as any).getConnectedNodes(nodeId) as string[];
      // get all nodes via dataset API
      const allNodes =
        (net as any).body?.data?.nodes?.get() ?? (net as any).getPositions
          ? Object.keys((net as any).getPositions())
          : [];
      const updates = (allNodes as any[]).map((n: any) => {
        const nid = typeof n === "string" ? n : n.id;
        if (nid === nodeId)
          return { id: nid, color: { background: "#ff6666" }, size: 36 };
        if (neighbors.indexOf(nid) !== -1)
          return { id: nid, color: { background: "#00ff66" }, size: 28 };
        return { id: nid, color: { background: "#777777" }, size: 10 };
      });

      try {
        // apply updates via public dataset API
        (net as any).body?.data?.nodes?.update(updates);
      } catch {
        // fallback: iterate updates and update via API
        updates.forEach((u: any) => {
          try {
            (net as any).body?.data?.nodes?.update(u);
          } catch {}
        });
      }
    });

    return () => {
      try {
        (net as any).destroy();
      } catch {}
    };
  }, [nodes, edges]);

  return <div ref={containerRef} style={{ height: "720px", width: "100%" }} />;
}
