import datetime as dt

from backup_gate import should_skip, threshold

UTC = dt.UTC
NOW = dt.datetime(2026, 10, 23, 0, 23, tzinfo=UTC)  # 22/10 21:23 BRT (cron reserva)


def test_threshold_is_today_19h_brt():
    assert threshold(NOW).isoformat() == "2026-10-22T19:00:00-03:00"


def test_skip_only_when_built_after_19h_with_todays_closes():
    ok = {"generated_at": "2026-10-22T22:25:00Z", "us": {"as_of": "2026-10-22"}, "br": {"as_of": "2026-10-22"}}
    assert should_skip(ok, NOW) is True
    assert should_skip({**ok, "generated_at": "2026-10-22T21:50:00Z"}, NOW) is False  # antes das 19h BRT
    assert should_skip({**ok, "us": {"as_of": "2026-10-21"}}, NOW) is False  # Yahoo ainda sem o fechamento
    assert should_skip({**ok, "br": {"as_of": "2026-10-22", "intraday": True}}, NOW) is False  # ainda parcial
    assert should_skip(None, NOW) is False
    assert should_skip({"generated_at": "lixo"}, NOW) is False
