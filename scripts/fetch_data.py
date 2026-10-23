"""Baixa os fechamentos e grava <out>/setores.json (dados da página) e <out>/summary.json (resumo).

EUA: Yahoo Finance via yfinance, fechamento ajustado (auto_adjust=True, retorno total dos ETFs).
Brasil: API pública de estatísticas de índices da B3 (mesmo endpoint do projeto rrg; índices de preço).

Formato compacto: fechamentos diários dos últimos ~2 anos + fechamentos semanais (sexta) desde 2015.
Robustez: cada chamada externa tem até 4 tentativas (esperas de 3, 9 e 27 s). Se uma aba (EUA ou Brasil)
falhar ou vier incompleta/mais antiga, reaproveita a aba do último setores.json publicado (--prev) e marca
"stale": true. Nada é inventado: sem dado novo e sem dado anterior, o script falha e o deploy não acontece
(o GitHub Pages continua servindo a última versão publicada).

Uso: python scripts/fetch_data.py <pasta de saída> [--prev URL_ou_arquivo]
"""

import argparse
import base64
import datetime as dt
import json
import os
import sys
import urllib.request
from math import floor, log10

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from net import retry  # noqa: E402
from summary import build_summary  # noqa: E402
from universe import BR_BENCH, BR_ORDER, SRC, US_BENCH, US_ORDER  # noqa: E402

START = dt.date(2015, 1, 1)
B3_URL = "https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay/"
BRT = dt.timezone(dt.timedelta(hours=-3))
CLOSE_BRT = (18, 30)  # antes disso, um pregão de hoje ainda pode ser intradiário
DAILY_YEARS = 2


def sig(x, n=5):
    """Arredonda para n algarismos significativos (JSON compacto). NaN/None -> None."""
    if x is None or pd.isna(x):
        return None
    x = float(x)
    if x == 0:
        return 0
    d = n - 1 - floor(log10(abs(x)))
    v = round(x, d)
    return int(v) if d <= 0 else v


def parse_br_number(v):
    """'123.456,78' -> 123456.78; vazio/inválido -> None."""
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def parse_b3_year(payload, year):
    """Converte a resposta GetPortfolioDay (linhas por dia, colunas rateValue1..12 por mês) em {data: pontos}."""
    pts = {}
    for row in (payload or {}).get("results", []) or []:
        for m in range(1, 13):
            v = parse_br_number(row.get(f"rateValue{m}"))
            if v is None:
                continue
            try:
                pts[dt.date(year, m, int(row["day"]))] = v
            except (ValueError, KeyError, TypeError):
                pass
    return pts


def b3_index(code, today, sleep=None):
    import requests

    pts = {}
    for year in range(START.year, today.year + 1):
        q = base64.b64encode(json.dumps({"language": "pt-br", "index": code, "year": str(year)}).encode()).decode()

        def get(q=q):
            r = requests.get(B3_URL + q, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return r.json()

        kw = {"sleep": sleep} if sleep else {}
        pts.update(parse_b3_year(retry(get, f"B3 {code} {year}", **kw), year))
    if len(pts) < 500:
        raise RuntimeError(f"B3 {code}: só {len(pts)} pontos")
    return pd.Series(pts).sort_index()


def fetch_br(today):
    cols = {c: b3_index(c, today) for c in BR_ORDER + [BR_BENCH]}
    df = pd.DataFrame(cols)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def fetch_us():
    import yfinance as yf

    tickers = US_ORDER + [US_BENCH]

    def get():
        df = yf.download(tickers, start=START.isoformat(), auto_adjust=True, progress=False, threads=True)
        close = df["Close"]
        missing = [t for t in tickers if t not in close.columns or close[t].dropna().size < 200]
        if missing:
            raise RuntimeError(f"Yahoo sem dados para {', '.join(missing)}")
        return close[tickers]

    return retry(get, "Yahoo EUA")


def clean(df, bench, now_brt):
    """Remove linhas vazias (o Yahoo às vezes devolve a data de hoje só com NaN), dias sem o índice
    de referência, fins de semana e o pregão de hoje antes do fechamento."""
    df = df.copy()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.dropna(how="all")
    df = df[df[bench].notna()]
    df = df[df.index.dayofweek < 5]
    today = pd.Timestamp(now_brt.date())
    if (now_brt.hour, now_brt.minute) < CLOSE_BRT:
        df = df[df.index < today]
    return df[df.index <= today]


def encode(d):
    dates = list(d.index)
    gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
    return {"d0": dates[0].strftime("%Y-%m-%d"), "gaps": gaps, "s": {c: [sig(v) for v in d[c]] for c in d.columns}}


def pack(df, order, bench, src):
    """Bloco de uma aba: diário (últimos ~2 anos + 1 mês, para cobrir YTD e 1A) e semanal (W-FRI)."""
    df = df[order + [bench]]
    last = df.index[-1]
    daily = df.loc[df.index >= last - pd.DateOffset(years=DAILY_YEARS, months=1)].ffill(limit=5)
    weekly = df.ffill(limit=5).resample("W-FRI").last()
    weekly.index = [min(i, last) for i in weekly.index]  # semana corrente: data real do último fechamento
    weekly = weekly.dropna(how="all")
    first = {c: df[c].first_valid_index().strftime("%Y-%m-%d") for c in df.columns}
    lastv = {c: df[c].last_valid_index().strftime("%Y-%m-%d") for c in df.columns}
    return {
        "bench": bench,
        "order": order,
        "last": last.strftime("%Y-%m-%d"),
        "first": first,
        "last_by": lastv,
        "d": encode(daily),
        "w": encode(weekly),
        "src": src["pt"],
        "src_en": src["en"],
        "stale": False,
    }


def validate(block, now_brt):
    """Problemas que impedem usar a aba nova (aí reaproveita a publicada)."""
    probs = []
    last = dt.date.fromisoformat(block["last"])
    if (now_brt.date() - last).days > 10:
        probs.append(f"último fechamento {last} tem mais de 10 dias")
    for t, d in block["last_by"].items():
        if (last - dt.date.fromisoformat(d)).days > 7:
            probs.append(f"{t} parado em {d}")
    if len(block["d"]["gaps"]) < 250:
        probs.append("histórico diário curto")
    return probs


def load_prev(src):
    if not src:
        return None
    try:
        if src.startswith("http"):
            with urllib.request.urlopen(src + ("&" if "?" in src else "?") + "nocache=1", timeout=30) as r:
                return json.load(r)
        with open(src) as f:
            return json.load(f)
    except Exception as e:
        print(f"setores.json anterior indisponível ({type(e).__name__}: {e})")
        return None


def choose(tab, fetch, order, bench, prev, now_brt, log):
    """Bloco novo se válido e não mais antigo que o publicado; senão, o publicado (stale). Nunca inventa."""
    old = (prev or {}).get(tab)
    try:
        new = pack(clean(fetch(), bench, now_brt), order, bench, SRC[tab])
        probs = validate(new, now_brt)
        if old and new["last"] < old.get("last", ""):
            probs.append(f"dados novos ({new['last']}) mais antigos que os publicados ({old['last']})")
        if not probs:
            return new
        log.append(f"{tab}: " + "; ".join(probs))
    except Exception as e:
        log.append(f"{tab}: falha ao baixar ({type(e).__name__}: {e})")
    if old:
        old = dict(old)
        old["stale"] = True
        log.append(f"{tab}: mantendo os últimos dados válidos publicados (até {old.get('last')})")
        return old
    raise SystemExit(f"{tab}: sem dados novos válidos e sem dados anteriores; nada é publicado")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    ap.add_argument("--prev", default=None, help="setores.json publicado (URL ou arquivo), usado se uma fonte falhar")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    now = dt.datetime.now(dt.UTC)
    now_brt = now.astimezone(BRT)
    prev = load_prev(a.prev)
    log = []
    out = {
        "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "us": choose("us", fetch_us, US_ORDER, US_BENCH, prev, now_brt, log),
        "br": choose("br", lambda: fetch_br(now_brt.date()), BR_ORDER, BR_BENCH, prev, now_brt, log),
        "log": log,
    }
    s = json.dumps(out, separators=(",", ":"), allow_nan=False)
    with open(os.path.join(a.out, "setores.json"), "w") as f:
        f.write(s)
    summ = build_summary(out)
    with open(os.path.join(a.out, "summary.json"), "w") as f:
        json.dump(summ, f, ensure_ascii=False, separators=(",", ":"))
    for k in ("us", "br"):
        b = out[k]
        print(
            f"{k}: até {b['last']}, {len(b['d']['gaps']) + 1} diários, {len(b['w']['gaps']) + 1} semanais"
            + (" (STALE)" if b["stale"] else "")
        )
    print(f"setores.json {len(s) // 1024} KB; summary.json {os.path.getsize(os.path.join(a.out, 'summary.json'))} bytes")
    for line in log:
        print("AVISO:", line)


if __name__ == "__main__":
    main()
