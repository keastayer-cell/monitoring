# Uptime Monitor

Отдельный сервис для мониторинга доступности приложений и сервисов.

## Структура

- `monitor_health.py` - Основной скрипт мониторинга
- `monitor_targets.example.json` - Пример конфигурации целей для мониторинга
- `.env.monitor.example` - Пример файла переменных окружения

## Использование локально

```bash
cp .env.monitor.example .env.monitor
cp monitor_targets.example.json monitor_targets.json
# Отредактируй .env.monitor и monitor_targets.json с нужными значениями
python3 monitor_health.py
```

## На сервере

- Расположение: `/opt/uptime-monitor/`
- Расписание: `uptime-monitor.timer` запускает проверку каждый час
- Ручной запуск: `systemctl start uptime-monitor.service`
- Последние результаты: `journalctl -u uptime-monitor.service -n 100 --no-pager`

Deploy в `main` устанавливает service и timer, включает расписание на сервере и сразу
выполняет одну проверку. Deploy завершается ошибкой и выводит журнал сервиса, если
серверная конфигурация отсутствует или критичная цель недоступна.

Проверить расписание на сервере:

```bash
systemctl status uptime-monitor.timer
systemctl list-timers uptime-monitor.timer --no-pager
```

## Поддерживаемые типы проверок

- `url` - HTTP проверка доступности
- `systemd` - Проверка статуса systemd сервиса
- `telegram_getme` - Проверка доступности Telegram Bot API

## Telegram retry

Проверка `telegram_getme` делает несколько попыток, чтобы одиночный сетевой таймаут Telegram не давал ложный DOWN.

Настройки в `.env.monitor`:

```bash
TELEGRAM_CHECK_ATTEMPTS=3
TELEGRAM_CHECK_RETRY_DELAY=2
```

## Необязательные цели

Если цель должна оставаться в мониторинге и алертах, но не должна валить `uptime-monitor.service`,
добавьте в `monitor_targets.json` поле:

```json
{
	"affects_exit_code": false
}
```

Такую цель монитор все равно отметит как `FAIL` и включит в уведомления,
но сам oneshot-сервис завершится успешно, если только остальные критичные цели в порядке.
