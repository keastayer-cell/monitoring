import monitor_health as monitor

TARGETS = {"api": {"id": "api", "name": "Telegram API", "type": "telegram_getme"}}
START = "2026-10-31T01:00:00+00:00"
END = "2026-10-31T02:00:00+00:00"


def step(path, ok, timestamp):
    current = monitor.update_incidents(
        monitor.load_state(path), {"api": (ok, "ok" if ok else "timeout")}, timestamp
    )
    monitor.notify_incidents(current, TARGETS, path, "test-server", timestamp, "", "")
    return monitor.load_state(path)


def capture(monkeypatch, results):
    messages = []
    responses = iter(results)

    def notify(subject, body, *_args):
        messages.append((subject, body))
        return next(responses)

    monkeypatch.setattr(monitor, "notify", notify)
    return messages


def test_missed_down_alert_gets_explanatory_report_and_no_duplicates(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    messages = capture(monkeypatch, [False, True])
    step(path, False, START)
    step(path, False, "2026-10-31T01:30:00+00:00")
    state = step(path, True, END)
    assert messages[1][0] == "[MISSED ALERT] Telegram API"
    assert "сразу доставить не удалось" in messages[1][1]
    assert "31.10.2026 04:00:00 МСК" in messages[1][1]
    assert "31.10.2026 05:00:00 МСК" in messages[1][1]
    assert "точные начало и конец" in messages[1][1]
    assert state["api"]["incidents"] == []
    step(path, True, "2026-10-31T03:00:00+00:00")
    assert len(messages) == 2


def test_delivered_down_gets_normal_recovery(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    messages = capture(monkeypatch, [True, True])
    step(path, False, START)
    step(path, True, END)
    assert messages[1][0] == "[RECOVERY] Telegram API"
    assert "предупреждение о сбое было отправлено" in messages[1][1]


def test_failed_report_is_retried_with_original_times_after_restart(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    messages = capture(monkeypatch, [False, False, True])
    step(path, False, START)
    state = step(path, True, END)
    assert state["api"]["incidents"][0]["recovered_at"] == END
    step(path, True, "2026-10-31T03:00:00+00:00")
    assert messages[1][1].split("Сбой обнаружен:")[1] == messages[2][1].split("Сбой обнаружен:")[1]


def test_new_outage_does_not_erase_undelivered_report(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    messages = capture(monkeypatch, [False, False, False, True])
    step(path, False, START)
    step(path, True, END)
    state = step(path, False, "2026-10-31T03:00:00+00:00")
    assert len(state["api"]["incidents"]) == 2
    state = step(path, True, "2026-10-31T04:00:00+00:00")
    assert state["api"]["incidents"] == []
    assert messages[-1][1].count("Сбой обнаружен:") == 2


def test_legacy_down_state_does_not_invent_delivery_or_start_time(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    monitor.save_state(path, {"api": {"ok": False, "details": "timeout"}})
    messages = capture(monkeypatch, [True])
    step(path, False, START)
    assert not messages
    step(path, True, END)
    assert "[MISSED ALERT]" in messages[0][0]
    assert "неизвестно" in messages[0][1]
    assert "сведения о доставке предупреждения не сохранены" in messages[0][1]


def test_healthy_initial_state_is_silent(tmp_path, monkeypatch):
    messages = capture(monkeypatch, [])
    step(tmp_path / "state.json", True, START)
    assert not messages


def test_email_failure_does_not_lose_telegram_delivery(monkeypatch):
    monkeypatch.setattr(monitor, "send_telegram", lambda *_args: True)

    def fail_email(*_args):
        raise RuntimeError("SMTP failed")

    monkeypatch.setattr(monitor, "send_email", fail_email)
    assert monitor.notify("test", "body", "", "") is True
