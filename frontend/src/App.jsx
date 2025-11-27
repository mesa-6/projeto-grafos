import React, { useEffect, useMemo, useRef, useState } from "react";
import { Routes, Route, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import ForceGraph2D from "react-force-graph-2d";
import { motion } from "framer-motion";
import logo from "./image.png";

const API_BASE = (
  import.meta.env.VITE_API_BASE || "http://localhost:8000"
).replace(/\/+$/, "");
const api = axios.create({ baseURL: API_BASE, timeout: 60_000 });

/* =========================================================
   CONFIGURAÇÃO DE CORES (Personalize o RGB aqui)
   ========================================================= */
// Cor padrão dos nós (Azul) - Alterar este Hex/RGB muda a cor dos bairros
const DEFAULT_NODE_COLOR = "#3b82f6"; // Exemplo RGB: rgb(59, 130, 246)

// Cor das arestas/linhas (Azul claro transparente)
const DEFAULT_LINK_COLOR = "rgba(59, 130, 246, 0.2)";

// Cores de Destaque (Origem, Destino, Caminho)
const HIGHLIGHT_COLOR = "#ff7a18"; // Laranja forte (caminho)
const ORIGIN_COLOR = "#b91c1c"; // Vermelho (origem)
const DEST_COLOR = "#059669"; // Verde (destino)

const GRAPH_HEIGHT = 760;

/* ---------- Header ---------- */
function Header() {
  const navStyle = {
    padding: "6px 10px",
    borderRadius: 6,
    color: "#111827",
    textDecoration: "none",
    fontWeight: 600,
  };

  return (
    <header
      className="app-header"
      style={{
        background: "#ffffff",
        padding: "6px 0",
        borderBottom: "1px solid rgba(0,0,0,0.06)",
      }}
    >
      <div
        className="app-container"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <nav style={{ display: "flex", gap: 8 }}>
          <Link
            to="/"
            style={navStyle}
            className="text-sm px-3 py-1 rounded-md hover:bg-gray-100"
          >
            Início
          </Link>
          <Link
            to="/bairros"
            style={navStyle}
            className="text-sm px-3 py-1 rounded-md hover:bg-gray-100"
          >
            Bairros
          </Link>
          <Link
            to="/musicas"
            style={navStyle}
            className="text-sm px-3 py-1 rounded-md hover:bg-gray-100"
          >
            Músicas
          </Link>
        </nav>

        <div
          className="header-right"
          style={{ display: "flex", alignItems: "center", gap: 10 }}
        >
          <img
            src={logo}
            alt="logo"
            className="header-logo"
            style={{ width: 36, height: 36, objectFit: "contain" }}
          />
          <div
            className="header-title"
            style={{ textAlign: "right", fontWeight: 700 }}
          >
            Mesa 6 - Projeto Grafos
          </div>
        </div>
      </div>
    </header>
  );
}

/* ---------- Footer ---------- */
function Footer() {
  return (
    <footer className="mt-8 py-6">
      <div className="app-container small-muted">Projeto Grafos — Frontend</div>
    </footer>
  );
}

/* ---------- Loading UI ---------- */
function LoadingCard({ text = "Carregando..." }) {
  return (
    <div className="card">
      <div className="animate-pulse">
        <div className="h-4 bg-slate-100 rounded w-1/3 mb-4" />
        <div className="h-3 bg-slate-100 rounded w-full mb-2" />
        <div className="h-3 bg-slate-100 rounded w-full mb-2" />
      </div>
      <div className="mt-3 small-muted">{text}</div>
    </div>
  );
}

/* ---------- GraphBairros component ---------- */
function GraphBairros({
  origin,
  setOrigin,
  dest,
  setDest,
  highlightedNodes,
  highlightedLinks,
  setHighlightedNodes,
  setHighlightedLinks,
  setStatus,
}) {
  const fgRef = useRef();
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hovered, setHovered] = useState(null);
  const [forceDistance, setForceDistance] = useState(140);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      try {
        const nres = await api.get("/nodes", { params: { graph: "part1" } });
        const eres = await api.get("/edges", { params: { graph: "part1" } });
        if (!mounted) return;
        const ndata = (nres.data && nres.data.nodes) || [];
        const edata = (eres.data && eres.data.edges) || [];
        setNodes(
          ndata.map((n) => ({
            id: n.id,
            grau: n.grau,
            microrregiao: n.microrregiao,
          }))
        );
        setLinks(
          edata.map((e) => ({
            source: e.bairro_origem,
            target: e.bairro_destino,
            peso: Number(e.peso || 1),
            logradouro: e.logradouro || "",
          }))
        );
      } catch (err) {
        if (!mounted) return;
        setError(err?.response?.data?.detail || err.message || String(err));
      } finally {
        if (!mounted) return;
        setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  // Centraliza o grafo automaticamente quando os nós carregam
  useEffect(() => {
    if (!loading && nodes.length > 0 && fgRef.current) {
      // Pequeno timeout para garantir que a engine iniciou
      setTimeout(() => {
        fgRef.current.zoomToFit(400, 50); // (duração, padding)
      }, 500);
    }
  }, [loading, nodes]);

  // update link force when spacing changes
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    try {
      const linkForce = fg.d3Force && fg.d3Force("link");
      if (linkForce && typeof linkForce.distance === "function") {
        linkForce.distance(forceDistance);
      }
      if (typeof fg.d3ReheatSimulation === "function") {
        fg.d3ReheatSimulation();
      }
    } catch (_) {}
  }, [forceDistance]);

  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);

  // paint nodes
  const nodePaint = (node, ctx, globalScale) => {
    const deg = Number(node.grau || 1);
    const rBase = 3 + Math.min(4, Math.log2(deg + 1));
    const isOrigin = origin && origin.id === node.id;
    const isDest = dest && dest.id === node.id;
    const isHighlighted = highlightedNodes && highlightedNodes.has(node.id);
    const isHovered = hovered && hovered.id === node.id;
    const radius =
      isOrigin || isDest ? Math.min(14, rBase + 5) : Math.max(3, rBase);

    ctx.beginPath();

    // LÓGICA DE CORES
    if (isOrigin) ctx.fillStyle = ORIGIN_COLOR;
    else if (isDest) ctx.fillStyle = DEST_COLOR;
    else if (isHighlighted) ctx.fillStyle = HIGHLIGHT_COLOR;
    else ctx.fillStyle = isHovered ? "#1e40af" : DEFAULT_NODE_COLOR; // Usa a cor Azul Padrão

    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
    ctx.fill();

    // node border
    if (isOrigin || isDest || isHighlighted) {
      ctx.lineWidth = 2;
      ctx.strokeStyle = "rgba(0,0,0,0.08)";
      ctx.stroke();
    }

    const fontSize = Math.max(10, Math.min(13, 13 - Math.floor(globalScale)));
    ctx.font = `${fontSize}px Inter, sans-serif`;
    ctx.fillStyle = "#0f172a";
    ctx.fillText(node.id, node.x + radius + 8, node.y + fontSize / 3);
  };

  // link color
  const linkColor = (link) => {
    const a = typeof link.source === "object" ? link.source.id : link.source;
    const b = typeof link.target === "object" ? link.target.id : link.target;
    const key = a <= b ? `${a}||${b}` : `${b}||${a}`;
    if (highlightedLinks && highlightedLinks.has(key)) return HIGHLIGHT_COLOR;

    // Usa a cor Azul Claro Transparente definida no topo
    return DEFAULT_LINK_COLOR;
  };

  const linkWidth = (l) => {
    const a = typeof l.source === "object" ? l.source.id : l.source;
    const b = typeof l.target === "object" ? l.target.id : l.target;
    const key = a <= b ? `${a}||${b}` : `${b}||${a}`;
    if (highlightedLinks && highlightedLinks.has(key)) return 3.2;
    return Math.max(0.6, 1.2 - Math.log10((l.peso || 1) + 1));
  };

  if (loading) return <LoadingCard text="Carregando grafo dos bairros..." />;
  if (error)
    return <div className="card text-red-600">Erro: {String(error)}</div>;

  return (
    <div
      className="card relative"
      style={{
        height: GRAPH_HEIGHT,
        overflow: "hidden",
        background: "transparent",
      }}
    >
      <div
        className="absolute left-4 top-4 z-10 p-2 bg-white rounded-md flex gap-2 items-center"
        style={{ border: "1px solid rgba(3,105,161,0.06)" }}
      >
        <label
          className="small-muted"
          style={{ fontSize: 12, color: "#374151" }}
        >
          Spacing
        </label>
        <input
          aria-label="spacing"
          type="range"
          min={30}
          max={260}
          value={forceDistance}
          onChange={(e) => setForceDistance(Number(e.target.value))}
        />
        <div className="small-muted" style={{ fontSize: 12, color: "#374151" }}>
          {forceDistance}px
        </div>
      </div>

      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel={(n) => `${n.id} • grau ${n.grau}`}
        nodeCanvasObject={nodePaint}
        linkWidth={linkWidth}
        linkColor={linkColor}
        backgroundColor="#ffffff" // Fundo branco explícito
        onNodeHover={(node) => setHovered(node)}
        onNodeClick={async (node) => {
          if (!origin) {
            setOrigin(node);
            setStatus(`Origem: ${node.id}`);
            setHighlightedNodes(new Set([node.id]));
            setHighlightedLinks(new Set());
            setDest(null);
            return;
          }
          if (origin && !dest) {
            if (node.id === origin.id) {
              setOrigin(null);
              setHighlightedNodes(new Set());
              setHighlightedLinks(new Set());
              setStatus("Origem removida");
              return;
            }
            setDest(node);
            setStatus(`Destino: ${node.id} — calculando...`);
            try {
              const res = await api.get("/dijkstra", {
                params: { orig: origin.id, dest: node.id, graph: "part1" },
              });
              const caminho = res.data.caminho || [];
              const highlightedN = new Set(caminho);
              const highlightedL = new Set();
              for (let i = 0; i < caminho.length - 1; i++) {
                const a = caminho[i],
                  b = caminho[i + 1];
                const key = a <= b ? `${a}||${b}` : `${b}||${a}`;
                highlightedL.add(key);
              }
              setHighlightedNodes(highlightedN);
              setHighlightedLinks(highlightedL);
              setStatus(`Caminho com ${caminho.length} nós`);
            } catch (err) {
              setStatus(
                err?.response?.data?.detail || err.message || String(err)
              );
            }
            return;
          }
          setOrigin(node);
          setDest(null);
          setHighlightedNodes(new Set([node.id]));
          setHighlightedLinks(new Set());
          setStatus(`Origem redefinida: ${node.id}`);
        }}
        linkDistance={() => forceDistance}
        cooldownTicks={40}
        enableNodeDrag={false}
        autoPauseRedraw={true}
        height={GRAPH_HEIGHT}
      />

      {hovered && (
        <div
          className="absolute right-4 top-4 w-64 p-3 bg-white rounded-lg shadow-md"
          style={{ border: "1px solid rgba(0,0,0,0.06)" }}
        >
          <div className="text-sm kv" style={{ color: "#0f172a" }}>
            {hovered.id}
          </div>
          <div className="small-muted mt-1" style={{ color: "#374151" }}>
            grau: <span className="kv">{hovered.grau}</span>
          </div>
          <div className="small-muted" style={{ color: "#374151" }}>
            microrregião:{" "}
            <span className="kv">{hovered.microrregiao || "—"}</span>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- Bairros Page ---------- */
function BairrosPage() {
  const [nodesList, setNodesList] = useState([]);
  const [origin, setOrigin] = useState(null);
  const [dest, setDest] = useState(null);
  const [highlightedNodes, setHighlightedNodes] = useState(new Set());
  const [highlightedLinks, setHighlightedLinks] = useState(new Set());
  const [status, setStatus] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    api
      .get("/nodes", { params: { graph: "part1" } })
      .then((res) => {
        if (!mounted) return;
        const nodes = (res.data && res.data.nodes) || [];
        const ids = nodes.map((n) => n.id);
        setNodesList(ids);
      })
      .catch(() => {});
    return () => (mounted = false);
  }, []);

  function setFromSelect(val) {
    if (!val) return;
    setOrigin({ id: val });
    setDest(null);
    setHighlightedNodes(new Set([val]));
    setHighlightedLinks(new Set());
    setStatus(`Origem selecionada: ${val}`);
  }

  function setToSelect(val) {
    if (!val) return;
    if (!origin) {
      setStatus("Defina primeiro a origem (clicando no nó ou selecionando).");
      return;
    }
    setDest({ id: val });
    setStatus(`Destino selecionado: ${val} — calculando...`);
    api
      .get("/dijkstra", {
        params: { orig: origin.id, dest: val, graph: "part1" },
      })
      .then((res) => {
        const caminho = res.data.caminho || [];
        const highlightedN = new Set(caminho);
        const highlightedL = new Set();
        for (let i = 0; i < caminho.length - 1; i++) {
          const a = caminho[i],
            b = caminho[i + 1];
          const key = a <= b ? `${a}||${b}` : `${b}||${a}`;
          highlightedL.add(key);
        }
        setHighlightedNodes(highlightedN);
        setHighlightedLinks(highlightedL);
        setStatus(`Caminho com ${caminho.length} nós`);
      })
      .catch((err) =>
        setStatus(err?.response?.data?.detail || err.message || String(err))
      );
  }

  function clearSelection() {
    setOrigin(null);
    setDest(null);
    setHighlightedNodes(new Set());
    setHighlightedLinks(new Set());
    setStatus("Seleção limpa");
  }

  return (
    <main
      className="app-container"
      style={{ maxWidth: 1400, margin: "0 auto", padding: "24px" }}
    >
      <section>
        <div className="mb-4 flex items-center justify-between gap-4">
          <div />
          <div className="flex gap-2 items-center">
            <div
              className="card flex items-center gap-2"
              style={{ background: "transparent", border: "none" }}
            >
              <span className="chip" style={{ color: "#111827" }}>
                Nós: {nodesList.length}
              </span>
            </div>
          </div>
        </div>

        {/* Controls - Espaçamento AUMENTADO (gap: 32px) */}
        <div
          className="card mb-4 flex items-end"
          style={{
            background: "#ffffff",
            border: "1px solid rgba(3,105,161,0.06)",
            display: "flex",
            flexWrap: "nowrap",
            gap: "32px", // <--- ESPAÇAMENTO AUMENTADO AQUI
          }}
        >
          <div style={{ minWidth: 320 }}>
            <div
              className="small-muted"
              style={{ color: "#374151", marginBottom: 6 }}
            >
              Origem
            </div>
            <select
              className="input"
              value={origin ? origin.id : ""}
              onChange={(e) => setFromSelect(e.target.value)}
              style={{
                background: "#ffffff",
                border: "1px solid rgba(3,105,161,0.12)",
                width: "100%",
              }}
            >
              <option value="">-- selecione origem --</option>
              {nodesList.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>

          <div style={{ minWidth: 320 }}>
            <div
              className="small-muted"
              style={{ color: "#374151", marginBottom: 6 }}
            >
              Destino
            </div>
            <select
              className="input"
              value={dest ? dest.id : ""}
              onChange={(e) => setToSelect(e.target.value)}
              style={{
                background: "#ffffff",
                border: "1px solid rgba(3,105,161,0.12)",
                width: "100%",
              }}
            >
              <option value="">-- selecione destino --</option>
              {nodesList.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginLeft: "auto" }}>
            <button
              className="btn secondary"
              onClick={clearSelection}
              style={{
                background: "#ffffff",
                color: "#111827",
                border: "1px solid rgba(15,23,42,0.08)",
                padding: "10px 14px",
                borderRadius: 8,
              }}
            >
              Limpar
            </button>
          </div>
        </div>

        <GraphBairros
          origin={origin}
          setOrigin={setOrigin}
          dest={dest}
          setDest={setDest}
          highlightedNodes={highlightedNodes}
          highlightedLinks={highlightedLinks}
          setHighlightedNodes={setHighlightedNodes}
          setHighlightedLinks={setHighlightedLinks}
          setStatus={setStatus}
        />

        <div className="mt-3 small-muted" style={{ color: "#374151" }}>
          Status: <span className="kv">{status || "—"}</span>
        </div>
      </section>

      <aside className="mt-6">
        <div className="card small-muted">
          <div className="kv">Caminho atual</div>
          <ol className="mt-2 ml-4 list-decimal max-h-52 overflow-auto">
            {Array.from(highlightedNodes).length ? (
              Array.from(highlightedNodes).map((n) => <li key={n}>{n}</li>)
            ) : (
              <li className="placeholder-muted">Nenhum</li>
            )}
          </ol>
        </div>
      </aside>
    </main>
  );
}

/* ---------- Musicas Page ---------- */
function MusicasPage() {
  const [tracks, setTracks] = useState([]);
  const [seed, setSeed] = useState("");
  const [n, setN] = useState(10);
  const [algorithm, setAlgorithm] = useState("bellman-ford");
  const [playlist, setPlaylist] = useState([]);
  const [status, setStatus] = useState("");
  const [loadingTracks, setLoadingTracks] = useState(true);

  useEffect(() => {
    let mounted = true;
    api
      .get("/nodes", { params: { graph: "part2" } })
      .then((res) => {
        if (!mounted) return;
        const list = (res.data && res.data.nodes) || [];
        const normalized = list.map((t) =>
          typeof t === "string" ? t : t.id || t.track_name || JSON.stringify(t)
        );
        setTracks(normalized);
      })
      .catch((err) => setStatus(err?.message || String(err)))
      .finally(() => mounted && setLoadingTracks(false));
    return () => (mounted = false);
  }, []);

  async function generatePlaylist(e) {
    e?.preventDefault();
    if (!seed) {
      setStatus("Escolha uma música seed");
      return;
    }
    setStatus("Gerando playlist...");
    setPlaylist([]);
    try {
      if (algorithm === "bellman-ford") {
        const res = await api.get("/bellman-ford", {
          params: { orig: seed, graph: "part2" },
          timeout: 120000,
        });
        const distMap = res.data.distances || res.data.dist || {};
        const arr = Object.keys(distMap)
          .filter((k) => k !== seed)
          .map((k) => ({ track: k, dist: distMap[k] }));
        arr.sort(
          (a, b) =>
            (a.dist === null ? Infinity : a.dist) -
            (b.dist === null ? Infinity : b.dist)
        );
        const top = arr.slice(0, Math.max(0, n - 1)).map((x) => x.track);
        setPlaylist([seed, ...top]);
        setStatus(`playlist gerada: ${1 + top.length} músicas`);
        return;
      }

      if (algorithm === "dijkstra") {
        const results = [seed];
        const pool = tracks.filter((t) => t !== seed);
        for (let i = 0; i < pool.length && results.length < n; i++) {
          const dest = pool[i];
          try {
            const r = await api.get("/dijkstra", {
              params: { orig: seed, dest, graph: "part2" },
              timeout: 20000,
            });
            if (!r.data.error) results.push(dest);
          } catch (_) {}
        }
        setPlaylist(results.slice(0, n));
        setStatus(`playlist gerada (Dijkstra repetido): ${results.length}`);
        return;
      }

      if (algorithm === "bfs") {
        const r = await api.get("/bfs", {
          params: { source: seed, graph: "part2" },
          timeout: 60000,
        });
        const order = r.data.order || [];
        const unique = [seed, ...order.filter((x) => x !== seed)];
        setPlaylist(unique.slice(0, n));
        setStatus(
          `playlist gerada (BFS) com ${Math.min(n, unique.length)} músicas`
        );
        return;
      }

      if (algorithm === "dfs") {
        const r = await api.get("/dfs", {
          params: { sources: seed, graph: "part2" },
          timeout: 60000,
        });
        const order = r.data.order || [];
        const unique = [seed, ...order.filter((x) => x !== seed)];
        setPlaylist(unique.slice(0, n));
        setStatus(
          `playlist gerada (DFS) com ${Math.min(n, unique.length)} músicas`
        );
        return;
      }
    } catch (err) {
      setStatus(err?.response?.data?.detail || err.message || String(err));
    }
  }

  return (
    <main className="app-container">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2">
          <div className="card mb-4">
            <h2 className="text-xl font-semibold">
              Gerar playlist a partir de uma música seed
            </h2>
            <p className="small-muted mt-1" style={{ marginBottom: 12 }}>
              Selecione a música e o algoritmo.
            </p>

            <form
              onSubmit={generatePlaylist}
              className="mt-2"
              style={{ display: "grid", gap: 14 }}
            >
              <div style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
                <div style={{ flex: 1 }}>
                  <div className="small-muted" style={{ marginBottom: 6 }}>
                    Escolha a música
                  </div>
                  <select
                    className="input"
                    value={seed}
                    onChange={(e) => setSeed(e.target.value)}
                    style={{ width: "100%" }}
                  >
                    <option value="">-- escolha uma música --</option>
                    {loadingTracks ? (
                      <option value="">Carregando...</option>
                    ) : (
                      tracks.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))
                    )}
                  </select>
                </div>

                <div style={{ width: 140 }}>
                  <div className="small-muted" style={{ marginBottom: 6 }}>
                    Tamanho (N)
                  </div>
                  <input
                    className="input"
                    type="number"
                    min={2}
                    value={n}
                    onChange={(e) => setN(Number(e.target.value))}
                    style={{ width: "100%" }}
                  />
                </div>

                <div style={{ width: 180 }}>
                  <div className="small-muted" style={{ marginBottom: 6 }}>
                    Algoritmo
                  </div>
                  <select
                    className="input"
                    value={algorithm}
                    onChange={(e) => setAlgorithm(e.target.value)}
                    style={{ width: "100%" }}
                  >
                    <option value="bellman-ford">Bellman-Ford</option>
                    <option value="dijkstra">Dijkstra (repetido)</option>
                    <option value="bfs">BFS</option>
                    <option value="dfs">DFS</option>
                  </select>
                </div>

                <div>
                  <button
                    type="submit"
                    className="btn"
                    style={{
                      border: "none",
                      cursor: "pointer",
                      padding: "10px 16px",
                      borderRadius: 8,
                      background: "linear-gradient(90deg,#2563eb,#06b6d4)",
                      color: "white",
                      fontWeight: 700,
                      boxShadow: "0 6px 18px rgba(37,99,235,0.18)",
                    }}
                  >
                    Gerar
                  </button>
                </div>
              </div>

              <div className="small-muted">
                Dica: use o campo acima para escolher uma música.
              </div>
            </form>
          </div>

          <div className="card">
            <h3 className="font-semibold">Resultado</h3>
            <div className="mt-3 small-muted">{status}</div>
            <ol className="mt-3 list-decimal ml-6">
              {playlist.map((p, i) => (
                <li key={i} className="py-1">
                  {p}
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Aside vazia (Nota removida) */}
        <aside className="space-y-4"></aside>
      </div>
    </main>
  );
}

/* ---------- Home Page ---------- */
function Home() {
  return (
    <main className="app-container" style={{ padding: 24 }}>
      <div className="card p-8">
        <h1 className="text-3xl font-bold">Projeto Grafos</h1>
        <p className="small-muted mt-2">
          Navegue para visualizar o grafo dos bairros ou gerar playlists a
          partir do grafo de músicas.
        </p>
      </div>
    </main>
  );
}

/* ---------- App root ---------- */
export default function App() {
  return (
    <div className="min-h-screen" style={{ background: "#ffffff" }}>
      <Header />
      <div className="py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/bairros" element={<BairrosPage />} />
          <Route path="/musicas" element={<MusicasPage />} />
        </Routes>
      </div>
      <Footer />
    </div>
  );
}
