# Setores · performance setorial EUA e Brasil

Página estática em **[celowiz.github.io/setores](https://celowiz.github.io/setores/)**, publicada pelo GitHub Pages via GitHub Actions. Mostra quais setores estão puxando a bolsa nos EUA e no Brasil, em português e inglês (`?lang=en` ou botão PT/EN).

- **Retorno acumulado:** 13 janelas (1D, 5D, 10D, MTD, 1M, QTD, 3M, 6M, YTD, 1A, 3A, 5A, 10A), absoluto ou relativo ao benchmark (`/SPY` e `/IBOV`).
- **Rotação:** retorno móvel de 1, 3, 6 ou 12 meses, também absoluto ou relativo.
- **Ranking/legenda:** clique isola um setor, duplo clique isola só ele. Há tooltip, heatmap por janela e uma linha sobre o líder do período.
- **RRG:** link para o [Relative Rotation Graph](https://celowiz.github.io/rrg/).

## Fontes

| Aba | Ativos | Fonte | Série |
|---|---|---|---|
| EUA | ETFs SPDR setoriais XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY; benchmark SPY | Yahoo Finance (`yfinance`) | fechamento **ajustado** por dividendos e desdobramentos (retorno total) |
| Brasil | Índices setoriais B3 ICON, IEEX, IFNC, IMAT, IMOB, INDX, UTIL; benchmark IBOV | API pública de estatísticas de índices da B3 (`indexStatisticsProxy/IndexCall/GetPortfolioDay`) | pontos de fechamento (índices de **preço**) |

> **Atenção à comparação entre abas:** os índices setoriais da B3 e o Ibovespa usados aqui são índices de **preço**, sem reinvestir proventos. Já os ETFs americanos usam o fechamento ajustado, que equivale a **retorno total**. Em janelas longas, o retorno do Brasil fica subestimado em relação ao dos EUA pelo valor dos dividendos. Dentro de cada aba a comparação é coerente, porque setores e benchmark seguem o mesmo critério.

## Método

- **Base de cada janela:** é o último fechamento **antes** do início da janela. 1D/5D/10D usam 1/5/10 pregões; MTD, QTD e YTD usam o último fechamento do mês, trimestre ou ano anterior; 1M a 10A voltam meses de calendário a partir da última data.
- **Retorno acumulado:** `P_t / P_base − 1`. No modo relativo usa-se a razão setor ÷ benchmark rebaseada: `(P/B)_t / (P/B)_base − 1`.
- **Rotação:** retorno móvel de *k* pregões (21/63/126/252 no diário; 4/13/26/52 semanas no semanal) do preço ou da razão setor ÷ benchmark.
- **Resolução:** diária nos últimos ~2 anos; semanal (fechamento de sexta, semana corrente pela última data disponível) desde 2015, usada nas janelas 3A/5A/10A e nas rotações longas.
- **Séries que começam depois do início da janela** (XLC em 2018, XLRE em 2015, por exemplo) são rebaseadas na primeira data disponível, e a página indica isso.
- **Pregão de hoje:** só entra depois das 18:30 (Brasília). Linhas vazias do Yahoo e dias sem o benchmark são descartados.
- **Nenhum dado é inventado.** Se uma fonte falha (com novas tentativas após 3, 9 e 27 s), vem incompleta ou é mais antiga que a versão publicada, a aba reaproveita o último `setores.json` publicado e a página mostra o aviso de desatualizado. Sem versão anterior, o build falha e o Pages continua servindo o site anterior.

## Atualização

O workflow `.github/workflows/pages.yml` roda lint e testes, baixa os dados e publica o site:

- **Principal:** dias úteis às **19:23 (Brasília)** (`23 22 * * 1-5` UTC), depois do fechamento da B3 e de Nova York.
- **Reserva:** às **21:23 (Brasília)** (`23 0 * * 2-6` UTC). O job `gate` lê o `data/summary.json` publicado e pula o build se ele foi gerado depois das 19:00 com fechamentos de hoje nas duas abas.
- Também roda em push na `main` e manualmente (`workflow_dispatch`).
- Em pull requests faz tudo, menos o deploy.

`data/` não é versionado: os JSON só existem no artefato publicado.

## Arquivos de dados

- **`data/setores.json`** (~160 KB): é o que a página usa. Para cada aba traz `bench`, `order`, `first`, `last`, `last_by`, `stale`, `src`, além de `d` (diário) e `w` (semanal). Cada bloco tem o formato `{d0, gaps, s}`, ou seja, a primeira data, os intervalos em dias e as séries com 5 algarismos significativos.
- **`data/summary.json`** (< 20 KB, hoje ~2,5 KB): é lido pela página Mercado Hoje do portfólio.

```json
{
  "schema": 1,
  "project": "setores",
  "url": "https://celowiz.github.io/setores/",
  "generated_at": "2026-10-23T01:09:27Z",
  "us": {
    "as_of": "2026-10-21",
    "stale": false,
    "bench": "SPY",
    "day_base": "2026-10-20",
    "ytd_base": "2025-12-31",
    "day_bench": 0.0053,
    "ytd_bench": 0.1425,
    "day_leader": {
      "t": "XLK",
      "pt": "Tecnologia",
      "en": "Technology",
      "ret": 0.0167
    },
    "day_laggard": {
      "t": "XLC",
      "pt": "Comunicação",
      "en": "Communication Services",
      "ret": -0.0111
    },
    "ytd_leader": {
      "t": "XLE",
      "pt": "Energia",
      "en": "Energy",
      "ret": 0.5547
    },
    "ytd_laggard": {
      "t": "XLC",
      "pt": "Comunicação",
      "en": "Communication Services",
      "ret": -0.0659
    },
    "sectors": [
      {
        "t": "XLB",
        "pt": "Materiais",
        "en": "Materials",
        "day": 0.0018,
        "ytd": 0.1462
      },
      "…"
    ]
  },
  "br": "{… mesmo formato, bench IBOV}"
}
```

Exemplo real (rodada local de 22/10/2026; a aba EUA ainda estava sem o fechamento do dia no Yahoo). Os retornos estão em fração com 4 casas, e empates são decididos pelo ticker.

## Rodar localmente

```bash
pip install -r requirements.txt
python scripts/fetch_data.py data            # baixa os dados (~40 s)
python -m http.server 8000                   # abra http://localhost:8000/
ruff check . && ruff format --check .        # lint
python -m pytest -q tests && node --test tests/calc.test.mjs
```

`scripts/make_assets.py` gera `favicon-16.png` (a partir de `favicon-16.svg`, versão simplificada para a aba), `favicon-32.png`, `favicon.ico` (16/32/48), `apple-touch-icon.png` e `og.png` (1200×630, com um print real do gráfico) a partir de `favicon.svg`. Ele precisa do site rodando localmente e do Playwright. Não roda no CI; as imagens são versionadas.

## Ícone

**Linhas divergentes**: três linhas saem do mesmo ponto e se separam, como no retorno acumulado. A linha verde-água sobe, a creme vai de lado e a apagada cai. O ícone usa o mesmo quadrado escuro arredondado dos outros projetos. `favicon.svg` é o desenho principal, e `favicon-16.svg` é a versão simplificada para 16 px. A página usa só PNG e ICO, sem o `<link>` do SVG, para que a aba mostre o desenho simplificado de 16 px, como no Lab e no Mercado Hoje. Os SVG ficam no repositório apenas como fonte de `scripts/make_assets.py` e não são publicados.

## Analytics

GA4 `G-QCBFGR39WG` (o mesmo do portfólio), `content_group` = `setores`.
