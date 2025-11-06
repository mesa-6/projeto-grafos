export type NodeMeta = {
  id: string;
  grau?: number;
  microrregiao?: string | number | null;
};

export type EdgeItem = {
  bairro_origem: string;
  bairro_destino: string;
  logradouro?: string;
  peso?: number;
};
