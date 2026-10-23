import datetime as dt
import json

import summary as sm
from universe import BR_BENCH, BR_ORDER, US_BENCH, US_ORDER


def block(dates, series):
    gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
    return {"d0": dates[0].isoformat(), "gaps": gaps, "s": series}


def tab(order, bench, series, dates):
    return {"bench": bench, "order": order, "last": dates[-1].isoformat(), "d": block(dates, series), "stale": False}


DATES = [dt.date(2025, 12, 29), dt.date(2025, 12, 30), dt.date(2026, 1, 2), dt.date(2026, 1, 5), dt.date(2026, 1, 6)]


def test_leader_laggard_day_and_ytd():
    s = {"A": [100, 100, 110, 120, 126], "B": [50, 50, 50, 40, 41], "C": [None, None, 10, 10, 9], "BM": [10, 10, 11, 12, 12]}
    sm.NAMES.update({"A": ("a", "a"), "B": ("b", "b"), "C": ("c", "c")})
    t = sm.tab_summary(tab(["A", "B", "C"], "BM", s, DATES))
    assert t["as_of"] == "2026-01-06" and t["day_base"] == "2026-01-05" and t["ytd_base"] == "2025-12-30"
    assert t["day_leader"]["t"] == "A" and t["day_leader"]["ret"] == 0.05
    assert t["day_laggard"]["t"] == "C" and t["day_laggard"]["ret"] == -0.1
    assert t["ytd_leader"]["t"] == "A" and t["ytd_leader"]["ret"] == 0.26
    assert t["ytd_laggard"]["t"] == "B" and t["ytd_laggard"]["ret"] == -0.18
    c = next(r for r in t["sectors"] if r["t"] == "C")
    assert c["ytd"] == -0.1 and c["ytd_since"] == "2026-01-02"  # rebaseado na 1ª data disponível
    assert t["ytd_bench"] == 0.2


def test_tie_breaks_by_ticker():
    s = {"A": [1, 1, 1, 1, 2], "B": [1, 1, 1, 1, 2], "BM": [1, 1, 1, 1, 1]}
    t = sm.tab_summary(tab(["B", "A"], "BM", s, DATES))
    assert t["day_leader"]["t"] == "A" and t["day_laggard"]["t"] == "B"


def test_full_universe_summary_is_small():
    import random

    random.seed(1)
    days = [dt.date(2024, 9, 2) + dt.timedelta(days=i) for i in range(800) if (dt.date(2024, 9, 2) + dt.timedelta(days=i)).weekday() < 5]

    def tb(order, bench):
        return tab(order, bench, {k: [100 + random.random() for _ in days] for k in order + [bench]}, days)

    out = sm.build_summary({"generated_at": "2026-10-22T22:30:00Z", "us": tb(US_ORDER, US_BENCH), "br": tb(BR_ORDER, BR_BENCH)})
    raw = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    assert len(raw.encode()) < 20_000
    assert out["us"]["ytd_leader"] and out["br"]["day_laggard"] and out["project"] == "setores"


def test_intraday_flag_and_timestamps():
    s = {"A": [100, 100, 110, 120, 126], "BM": [10, 10, 11, 12, 12]}
    sm.NAMES.update({"A": ("a", "a")})
    us = {**tab(["A"], "BM", s, DATES), "intraday": True, "as_of_ts": "2026-01-06T17:21:00Z"}
    br = tab(["A"], "BM", s, DATES[:-1])
    out = sm.build_summary({"generated_at": "2026-01-06T17:40:00Z", "us": us, "br": br})
    assert out["us"]["intraday"] is True and out["us"]["as_of_ts"] == "2026-01-06T17:21:00Z"
    assert out["br"]["intraday"] is False and out["br"]["as_of_ts"] is None
    assert out["as_of"] == "2026-01-06" and out["as_of_ts"] == "2026-01-06T17:21:00Z" and out["intraday"] is True
    closes = sm.build_summary({"generated_at": "x", "us": br, "br": br})
    assert closes["intraday"] is False and closes["as_of_ts"] is None
