import api from "./client";

export async function getNodes() {
  const r = await api.get("/nodes");
  return r.data;
}

export async function getEdges() {
  const r = await api.get("/edges");
  return r.data;
}

export async function getMicrorregiao(id: number | string) {
  const r = await api.get(`/microrregiao/${id}`);
  return r.data;
}

export async function getEgo(bairro: string) {
  const r = await api.get(`/ego/${encodeURIComponent(bairro)}`);
  return r.data;
}

export async function runDijkstra(orig: string, dest: string) {
  // endpoint could be /dijkstra?orig=&dest=
  const r = await api.get("/dijkstra", {
    params: { orig, dest },
  });
  return r.data;
}

export async function triggerExportHtmls() {
  const r = await api.post("/export/static-html");
  return r.data;
}
