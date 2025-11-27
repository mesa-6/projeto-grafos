##  Guia de Reprodução e Execução do Projeto Grafos

---

## Introdução

Este projeto foi desenvolvido por alunos da **CESAR School** para a disciplina de **Teoria dos Grafos**. O objetivo principal é **implementar, explorar e visualizar** diversos algoritmos relacionados à teoria de grafos.

---

## Pré-requisitos

Para executar e reproduzir o ambiente do projeto, você precisará dos seguintes recursos:

* **Python:** Versão **3.8 ou superior** (as versões **3.10** ou **3.11** são recomendadas).
* **Git**

---

## Configuração e Execução (Parte 1: Bairros do Recife)

### 1. Configuração Inicial do Projeto

1.  **Crie e acesse** um diretório local (opcional):
    ```bash
    mkdir grafos
    cd grafos
    ```
2.  **Clone o repositório** e acesse o diretório do projeto:
    ```bash
    git clone [https://github.com/mesa-6/projeto-grafos.git](https://github.com/mesa-6/projeto-grafos.git)
    cd projeto-grafos
    ```
3.  **Instale as dependências** (use `venv` ou outro ambiente virtual):
    ```bash
    pip install -r requirements.txt
    ```
4.  **Execute o projeto** (inicia a API e a aplicação web):
    ```python
    python -m src.cli
    ```

### 2. Acesso à Aplicação e Documentação da API

* **Aplicação Web:** `http://127.0.0.1:3000`
* **Documentação Interativa da API (Swagger UI) utilize :** `http://127.0.0.1:3000/docs#/`

### 3. Preparação e Geração dos Arquivos CSV

1.  **Baixe os Dados de Bairros:**
    * Baixe o CSV e salve-o na pasta **`data`** com o nome `bairros_recife.csv`.
    ```
    https://docs.google.com/spreadsheets/d/12BPdFqzRKWG17c0Fj879zKfN50RBVrhmpTzknlbUVi4/edit?usp=sharing
    ```
2.  **Pré-processamento dos Bairros:**
    * Gera o arquivo `bairros_recife_unique.csv`:
    ```python
    python -c "from src.graphs.io import melt_bairros_csv; melt_bairros_csv('data/bairros_recife.csv')"
    ```
3.  **Geração Inicial de Adjacências (Via Google Colab):**
    * Execute o notebook Colab para gerar o arquivo com todas as ligações de bairro .
    ```
    https://colab.research.google.com/drive/1nDy1f_B4oPnkv6DeThy7h1ynLHhL8WNH#scrollTo=79nSpAw3PUmF
    ```
    >  **Atenção:** O arquivo gerado requer **verificação e correção manual** para garantir adjacências válidas.

### 4. Geração de Relatórios e Visualizações com a API

* **Gerar Todos os Relatórios (Parte 1):**
    * Use o *endpoint* **`/generate/all`** com a *query* **`part1`** na API local.
    * Isso criará diversos relatórios (CSVs, JSONs e HTMLs) dentro da pasta **`out`**.

### 5. Geração de Arquivos HTML Estáticos

* **Criação de Visualizações Estáticas:**
    * Use o *endpoint* **`/export/estatic_html`** na API local.
    * Gera arquivos como `grafo_completo.html` e `microrregiao_1.html` a `microrregiao_6.html` na pasta **`out`**.

---

##  Configuração e Execução (Parte 2: Dados do Spotify)

### 1. Preparação dos Dados

1.  **Baixe o CSV do Kaggle:**
    * Baixe o CSV e coloque-o na pasta **`data`** com o nome `spotify.csv`.
    ```
    https://www.kaggle.com/datasets/alyahmedts13/spotify-songs-for-ml-and-analysis-over-8700-tracks
    ```
2.  **Tratamento e Filtragem dos Dados:**
    * Gera o arquivo `spotify_filtered.csv`:
    ```python
    python -c "from src.graphs.part2_io import prepare_spotify; prepare_spotify('data/spotify.csv')"
    ```
3.  **Construção das Adjacências (Arestas):**
    * Gera o arquivo `parte2_adjacencias.csv`:
    ```python
    python -c "from src.graphs.part2_build import build_edges_from_spotify; build_edges_from_spotify('data/spotify_filtered.csv','data/parte2_adjacencias.csv', verbose=True)"
    ```

### 2. Criação da Visualização Interativa

* **Gerar HTML Interativo:**
    * Cria a visualização `parte2_interactive.html` focada no **maior componente conectado**:
    ```bash
    python -m src.graphs.part2_visualize --csv data/parte2_adjacencias.csv --mode largest_component --max-nodes 90 --max-edges-per-node 1000000 --out out/parte2_interactive.html
    ```

### 3. Execução dos Algoritmos de Busca

* **Gerar Relatório de Benchmarks:**
    * Use o *endpoint* **`/bench`** com a *query* **`part2`** na API local.
    * Executa todos os algoritmos de busca e menor custo e cria o relatório **`parte2_report.json`** na pasta **`out`**.
 
## Para mais informações acesse :
https://docs.google.com/document/d/1oyxn0ng6YvfBBTeYz35koypGY_ZwUqYL/edit?usp=drive_link&ouid=103379078554451168962&rtpof=true&sd=true
