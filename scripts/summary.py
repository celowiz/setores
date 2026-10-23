"""Resumo pequeno (data/summary.json, poucos KB) para a página Mercado Hoje do portfólio.

Por aba (EUA e Brasil): setor líder e lanterna do dia (retorno do último pregão) e do ano (YTD),
retorno do índice de referência nas mesmas janelas e o retorno de todos os setores. Só reorganiza
os fechamentos de setores.json (mesma regra da página: base = último fechamento antes da janela).
Determinístico (empates desempatados pelo ticker).
Pregão em andamento: a aba traz "intraday": true e "as_of_ts" (horário UTC da cotação); os valores do dia
(e o YTD) são parciais até a rodada de fechamento. No topo, "as_of" é a data mais recente entre as abas,
"as_of_ts" o horário de cotação mais recente e "intraday" indica se alguma aba está parcial.

Uso: python scripts/summary.py <pasta com setores.json>  (fetch_data.py já grava o resumo)
"""

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from universe import NAMES  # noqa: E402

SCHEMA = 1
URL = "https://celowiz.github.io/setores/"


def decode(block):
    """{"d0","gaps","s"} -> (lista de datas, {ticker: valores})."""
    d = [dt.date.fromisoformat(block["d0"])]
    for g in block["gaps"]:
        d.append(d[-1] + dt.timedelta(days=g))
    return d, block["s"]


def last_le(dates, day):
    i = -1
    for j, x in enumerate(dates):
        if x <= day:
            i = j
        else:
            break
    return i


def window_return(vals, i0, n):
    """Retorno do último valor sobre a base i0; se o ativo ainda não existia em i0, usa o 1º valor disponível."""
    end = vals[n - 1] if n else None
    if end is None:
        return None, None
    for i in range(max(i0, 0), n):
        if vals[i] is not None:
            return end / vals[i] - 1, i
    return None, None


def r4(x):
    return None if x is None else round(x, 4)


def tab_summary(tab):
    dates, s = decode(tab["d"])
    n = len(dates)
    last = dates[-1]
    bases = {"day": n - 2, "ytd": last_le(dates, dt.date(last.year - 1, 12, 31))}
    out = {
        "as_of": tab["last"],
        "as_of_ts": tab.get("as_of_ts") if tab.get("intraday") else None,
        "intraday": bool(tab.get("intraday")),
        "stale": bool(tab.get("stale")),
        "bench": tab["bench"],
    }
    rows = []
    for t in tab["order"]:
        row = {"t": t, "pt": NAMES[t][0], "en": NAMES[t][1]}
        for k, i0 in bases.items():
            r, bi = window_return(s[t], i0, n)
            row[k] = r4(r)
            if bi is not None and bi > i0:
                row[k + "_since"] = dates[bi].isoformat()
        rows.append(row)
    out["sectors"] = rows
    for k, i0 in bases.items():
        out[k + "_base"] = dates[i0].isoformat() if i0 >= 0 else None
        out[k + "_bench"] = r4(window_return(s[tab["bench"]], i0, n)[0])
        ok = sorted((r for r in rows if r[k] is not None), key=lambda r: (-r[k], r["t"]))
        pick = lambda r, k=k: {"t": r["t"], "pt": r["pt"], "en": r["en"], "ret": r[k]}  # noqa: E731
        out[k + "_leader"] = pick(ok[0]) if ok else None
        out[k + "_laggard"] = pick(ok[-1]) if ok else None
    return out


def build_summary(data):
    tabs = {k: tab_summary(data[k]) for k in ("us", "br")}
    ts = [t["as_of_ts"] for t in tabs.values() if t["as_of_ts"]]
    return {
        "schema": SCHEMA,
        "project": "setores",
        "url": URL,
        "generated_at": data.get("generated_at"),
        "as_of": max(t["as_of"] for t in tabs.values()),
        "as_of_ts": max(ts) if ts else None,
        "intraday": any(t["intraday"] for t in tabs.values()),
        **tabs,
    }


def main(folder):
    with open(os.path.join(folder, "setores.json")) as f:
        data = json.load(f)
    s = build_summary(data)
    path = os.path.join(folder, "summary.json")
    with open(path, "w") as f:
        json.dump(s, f, ensure_ascii=False, separators=(",", ":"))
    print(f"summary.json: {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "data"))
