import datetime as dt

import pandas as pd
import pytest

import fetch_data as fd
from net import backoff

BRT = fd.BRT


def frame(days, cols, start="2024-01-01"):
    idx = pd.bdate_range(start, periods=days)
    return pd.DataFrame({c: [100.0 + i * (k + 1) * 0.1 for i in range(days)] for k, c in enumerate(cols)}, index=idx)


def test_backoff_3_9_27():
    assert backoff(4, 3.0, 3.0) == [3.0, 9.0, 27.0]


def test_sig_and_br_number():
    assert fd.sig(123456.789) == 123460
    assert fd.sig(1.234567) == 1.2346
    assert fd.sig(float("nan")) is None
    assert fd.parse_br_number("128.456,78") == 128456.78
    assert fd.parse_br_number("") is None and fd.parse_br_number("abc") is None


def test_parse_b3_year_ignores_invalid_days():
    payload = {
        "results": [{"day": 2, "rateValue1": "1.000,50", "rateValue2": ""}, {"day": 30, "rateValue2": "9,9", "rateValue3": "2.000,00"}]
    }  # 30/fev não existe
    pts = fd.parse_b3_year(payload, 2025)
    assert pts == {dt.date(2025, 1, 2): 1000.5, dt.date(2025, 3, 30): 2000.0}


def test_clean_drops_nan_row_and_intraday_today():
    df = frame(5, ["XLK", "SPY"], start="2026-10-16")  # 16/10 (sex) .. 22/10 (qui)
    df.loc[df.index[-1]] = float("nan")  # Yahoo: hoje só com NaN
    after = dt.datetime(2026, 10, 22, 19, 23, tzinfo=BRT)
    assert fd.clean(df, "SPY", after).index[-1] == pd.Timestamp("2026-10-21")
    df2 = frame(5, ["XLK", "SPY"], start="2026-10-16")
    before = dt.datetime(2026, 10, 22, 15, 0, tzinfo=BRT)
    assert fd.clean(df2, "SPY", before).index[-1] == pd.Timestamp("2026-10-21")
    assert fd.clean(df2, "SPY", after).index[-1] == pd.Timestamp("2026-10-22")


def test_pack_daily_and_weekly_blocks():
    df = frame(800, ["A", "B", "BM"], start="2023-06-01")
    df.loc[df.index[:300], "B"] = float("nan")  # B começa depois
    b = fd.pack(df, ["A", "B"], "BM", {"pt": "x", "en": "y"})
    last = df.index[-1]
    assert b["last"] == last.strftime("%Y-%m-%d")
    assert b["first"]["B"] == df.index[300].strftime("%Y-%m-%d")
    # semanal: última data = último fechamento real (semana parcial), não a sexta futura
    wd = pd.Timestamp(b["w"]["d0"]) + pd.Timedelta(days=sum(b["w"]["gaps"]))
    assert wd == last
    dd = pd.Timestamp(b["d"]["d0"])
    assert last - pd.DateOffset(years=2, months=1) <= dd
    assert len(b["d"]["s"]["A"]) == len(b["d"]["gaps"]) + 1


def test_choose_keeps_previous_on_failure_and_never_invents():
    now = dt.datetime(2026, 10, 22, 19, 23, tzinfo=BRT)
    prev = {"us": {"last": "2026-10-21", "stale": False, "d": {}, "w": {}}}

    def boom():
        raise RuntimeError("Yahoo fora do ar")

    log = []
    got = fd.choose("us", boom, ["A"], "BM", prev, now, log)
    assert got["stale"] is True and got["last"] == "2026-10-21"
    assert prev["us"]["stale"] is False  # não altera o objeto anterior
    assert any("falha" in x for x in log)
    with pytest.raises(SystemExit):
        fd.choose("br", boom, ["A"], "BM", prev, now, [])


def test_choose_rejects_data_older_than_published():
    now = dt.datetime(2026, 10, 22, 19, 23, tzinfo=BRT)
    df = frame(600, ["A", "BM"], start="2024-06-03")  # termina antes de out/2026
    prev = {"us": {"last": "2099-01-01", "stale": False}}
    log = []
    got = fd.choose("us", lambda: df, ["A"], "BM", prev, now, log)
    assert got["stale"] is True and got["last"] == "2099-01-01"


def test_choose_accepts_fresh_data():
    df = frame(600, ["A", "BM"], start="2024-06-03")
    now = dt.datetime.combine(df.index[-1].date(), dt.time(20, 0), BRT)
    got = fd.choose("us", lambda: df, ["A"], "BM", None, now, [])
    assert got["stale"] is False and got["last"] == df.index[-1].strftime("%Y-%m-%d")


def test_in_session_window():
    assert fd.in_session(dt.datetime(2026, 10, 22, 10, 9, tzinfo=BRT))
    assert fd.in_session(dt.datetime(2026, 10, 22, 18, 9, tzinfo=BRT))
    assert not fd.in_session(dt.datetime(2026, 10, 22, 9, 59, tzinfo=BRT))
    assert not fd.in_session(dt.datetime(2026, 10, 22, 19, 23, tzinfo=BRT))
    assert not fd.in_session(dt.datetime(2026, 10, 24, 12, 0, tzinfo=BRT))  # sábado


def test_parse_b3_intraday_only_today():
    today = dt.date(2026, 10, 22)
    pts = [{"closPric": 10.0, "dtTm": "10:00:00"}, {"closPric": 11.5, "dtTm": "14:21:30"}]
    payload = {"TradgFlr": {"date": "2026-10-22", "scty": {"lstQtn": pts}}}
    v, t = fd.parse_b3_intraday(payload, today)
    assert v == 11.5 and t == dt.datetime(2026, 10, 22, 14, 21, 30, tzinfo=BRT)
    assert fd.parse_b3_intraday({**payload, "TradgFlr": {**payload["TradgFlr"], "date": "2026-10-21"}}, today) is None
    assert fd.parse_b3_intraday({"TradgFlr": {"date": "2026-10-22", "scty": {"lstQtn": []}}}, today) is None
    assert fd.parse_b3_intraday(None, today) is None


def test_with_intraday_needs_every_asset_and_uses_oldest_quote():
    df = frame(300, ["A", "BM"], start="2025-08-28")
    today = dt.date(2026, 10, 22)
    t1 = dt.datetime(2026, 10, 22, 14, 20, tzinfo=BRT)
    t2 = dt.datetime(2026, 10, 22, 14, 35, tzinfo=BRT)
    assert fd.with_intraday(df, {"A": (1.0, t1), "BM": None}, today) is None
    out, ts = fd.with_intraday(df, {"A": (1.0, t1), "BM": (2.0, t2)}, today)
    assert out.index[-1] == pd.Timestamp(today) and list(out.iloc[-1]) == [1.0, 2.0]
    assert ts == t1.astimezone(dt.UTC)


def test_choose_marks_intraday_and_clean_keeps_partial_row():
    today = dt.date(2026, 10, 22)
    now = dt.datetime(2026, 10, 22, 14, 39, tzinfo=BRT)
    df = frame(300, ["A", "BM"], start="2025-08-28")
    df = df[df.index < pd.Timestamp(today)]
    t = dt.datetime(2026, 10, 22, 14, 21, tzinfo=BRT)
    got = fd.choose("us", lambda: fd.with_intraday(df, {"A": (1.0, t), "BM": (2.0, t)}, today), ["A"], "BM", None, now, [])
    assert got["intraday"] is True and got["last"] == "2026-10-22"
    assert got["as_of_ts"] == "2026-10-22T17:21:00Z"
    closes = fd.choose("us", lambda: (df, None), ["A"], "BM", None, now, [])
    assert closes["intraday"] is False and closes["as_of_ts"] is None and closes["last"] < "2026-10-22"
