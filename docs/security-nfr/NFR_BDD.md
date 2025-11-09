Feature: Производительность записи
  Scenario: p95 POST/PUT /media удерживается при нагрузке
    Given сервис развернут
    And нагрузка 20 RPS на endpoint POST /media в течение 5 минут
    When выполняется нагрузочный тест
    Then p95 времени ответа для POST/PUT /media <= 500 ms

Feature: Доступность (SLA)
  Scenario: Утв. уровень доступности
    Given сервис работает на production-like окружении
    When собираются метрики доступности за месяц по uptime probe
    Then доступность сервиса >= 99%

Feature: Негативный: rate limit
  Scenario: Защита от большого спайка
    Given gateway настроен лимитом 100 RPS per IP
    When один IP генерирует 500 RPS
    Then gateway выдаёт 429 для превышающих запросов

Feature: SCA - реакция на критические уязвимости
  Scenario: Исправление High/Critical зависимостей
    Given CI обнаружил Critical уязвимость
    When issue создана и назначена
    Then remediation выполнена <= 7 дней
