# timecapsule-opener

Lambda-функция `timecapsule-dev-opener` приложения [TimeCapsule](https://github.com/sta5on-cloud/timecapsule)
(ЛР7). Раз в минуту (EventBridge Scheduler `timecapsule-dev-open-capsules`) открывает капсулы, время которых
наступило. Раньше это делал `UPDATE` в начале каждого веб-запроса.

## Как устроено

- Один `UPDATE capsules SET opened_at = now() WHERE opened_at IS NULL AND open_at <= now() RETURNING id`.
  Условие `opened_at IS NULL` гарантирует, что два пересекающихся запуска не сообщат об одной капсуле дважды.
- Функция **не публикует** в SNS сама. Она возвращает
  `{"type": "capsules.opened", "count": N, "capsule_ids": [...], "opened_at": "..."}`. Служба Lambda
  отправляет запись о вызове в тему `timecapsule-dev-events` (назначение для успешных асинхронных вызовов).
  Поэтому функции в VPC не нужен выход в интернет.
- Таймаут подключения к базе 5 секунд. База останавливается на ночь, и тогда функция быстро завершается
  ошибкой. Повторов асинхронного вызова 0: следующий запуск через минуту всё равно откроет пропущенное.

Формат записи о вызове: [docs/events.md](https://github.com/sta5on-cloud/timecapsule/blob/main/docs/events.md).

## Переменные окружения

`DB_HOST` (endpoint RDS), `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

## Сборка и выкладка

```bash
./build.sh
aws lambda update-function-code --function-name timecapsule-dev-opener --zip-file fileb://function.zip
```

Среда выполнения `python3.12`, обработчик `lambda_function.lambda_handler`, приватные подсети VPC приложения,
Security Group `timecapsule-dev-lambda-sg`.
