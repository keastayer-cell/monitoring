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
- Управление: `systemctl status uptime-monitor.service`
- Расписание: `systemctl status uptime-monitor.timer` (каждый час)

## Поддерживаемые типы проверок

- `url` - HTTP проверка доступности
- `systemd` - Проверка статуса systemd сервиса
- `telegram_getme` - Проверка доступности Telegram Bot API

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
