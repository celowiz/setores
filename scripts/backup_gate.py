"""Cron reserva: decide se o build pode ser pulado porque o site já foi atualizado hoje depois do cron principal.

Uso: python scripts/backup_gate.py <url do data/summary.json publicado>
Escreve skip=true|false em $GITHUB_OUTPUT. Pula só se o resumo foi gerado depois das 19h BRT de hoje E
as duas abas já têm o fechamento de hoje (o Yahoo às vezes publica o fechamento dos EUA com atraso).
Na dúvida (sem resumo, data ilegível, fechamento antigo, feriado), roda o build: refazer não tem custo.
"""

import datetime as dt
import json
import os
import sys
import urllib.request

BRT = dt.timezone(dt.timedelta(hours=-3))
MAIN_HOUR_BRT = 19  # cron principal: dias úteis por volta das 19h BRT, depois do fechamento


def parse(ts):
    """ISO 8601; sem fuso = UTC (horário do runner do GitHub)."""
    t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.UTC)


def threshold(now):
    """Horário do cron principal mais recente (19h BRT de hoje, ou de ontem se ainda não deu 19h)."""
    n = now.astimezone(BRT)
    day = n.date() if n.hour >= MAIN_HOUR_BRT else n.date() - dt.timedelta(days=1)
    return dt.datetime.combine(day, dt.time(MAIN_HOUR_BRT), BRT)


def should_skip(summary, now):
    if not summary:
        return False
    try:
        if parse(summary.get("generated_at")) < threshold(now):
            return False
        day = threshold(now).date().isoformat()
        return all((summary.get(k) or {}).get("as_of", "") >= day for k in ("us", "br"))
    except (TypeError, ValueError, AttributeError):
        return False


def main(url):
    summ = None
    try:
        with urllib.request.urlopen(url + "?nocache=1", timeout=20) as r:
            summ = json.load(r)
    except Exception as e:
        print(f"resumo publicado indisponível ({type(e).__name__}); segue com o build")
    skip = should_skip(summ, dt.datetime.now(dt.UTC))
    info = {k: (summ or {}).get(k, {}).get("as_of") for k in ("us", "br")} if summ else {}
    print(
        f"generated_at={(summ or {}).get('generated_at')} as_of={info} → "
        + ("pula: já atualizado hoje depois do cron principal" if skip else "roda o build")
    )
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"skip={'true' if skip else 'false'}\n")


if __name__ == "__main__":
    main(sys.argv[1])
