import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import GraphExplorer from "./pages/GraphExplorer";
import DijkstraRunner from "./pages/DijkstraRunner";

function App() {
  return (
    <div className="min-h-screen">
      <header className="bg-slate-900 p-3 shadow">
        <div className="container flex items-center justify-between">
          <Link to="/">
            <h1 className="text-2xl font-bold text-white">
              Projeto Grafos — Dashboard
            </h1>
          </Link>
          <nav className="flex gap-4">
            <Link to="/" className="text-slate-200 hover:underline">
              Dashboard
            </Link>
            <Link to="/graph" className="text-slate-200 hover:underline">
              Explorer
            </Link>
            <Link to="/dijkstra" className="text-slate-200 hover:underline">
              Dijkstra
            </Link>
          </nav>
        </div>
      </header>

      <main className="container py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/graph" element={<GraphExplorer />} />
          <Route path="/dijkstra" element={<DijkstraRunner />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
