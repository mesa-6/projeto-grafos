import { defineConfig } from "vite";

export default defineConfig(async () => {
  // carregamento dinâmico para evitar erro ESM-only em alguns ambientes Windows/Node
  const reactPlugin = (await import("@vitejs/plugin-react")).default;

  return {
    plugins: [reactPlugin()],
    server: {
      port: 5173,
    },
  };
});
