# STRIDE - Угрозы и ссылки на NFR

Таблица: Поток/Элемент -> STRIDE категория -> Угроза (кратко) -> Контроль -> Ссылка на NFR

| Поток / Элемент | STRIDE | Угроза | Контроль (меры) | Ссылка на NFR |
|------------------|--------|--------|------------------|---------------|
| F1 (GET /media)  | D (DoS) | Спайк запросов от одного IP -> деградация сервиса | Rate-limiter на gateway, 429 при превышении | NFR-08 |
| F1 (GET /media)  | I (Info) | Информация в ответе содержит PII/чувств. данные | Валидация/фильтрация полей, контракты ответов | NFR-05 |
| F2 (POST/PUT)    | S (Spoofing) | Подмена клиента / фальсификация запроса (owner_id spoof) | Проверка owner привязки, X-Actor-Id парсер; авторизация в будущем | NFR-05 |
| F2 (POST/PUT)    | T (Tampering) | Изменение тела запроса (man-in-the-middle) | HTTPS only; request validation (Pydantic); input sanitization | NFR-05, NFR-04 |
| F3 (Gateway->Svc) | R (Repudiation) | Отсутствие trace-id -> трудно выяснить, кто что сделал | Добавить correlation_id, логирование каждой транзакции | NFR-07 |
| F4 (Svc->DB)      | T (Tampering) | SQL injection / некорректные запросы | ORM (prepared statements), input validation | NFR-05 |
| F4 (Svc->DB)      | D (DoS) | Большое число операций записи -> исчерпание ресурсов | Rate-limits для write; bulk-throttling | NFR-02, NFR-08 |
| F5 (Svc->Logs)    | I (Info) | Логи содержат чувств. данные или секреты | Маскирование PII, отказ от логирования секретов | NFR-07 |
| F6 (Backup)      | I (Info) | Утечка резервных копий | Шифрование экспорта, контролируемый доступ | NFR-06 |
| F7 (CI -> SVC)    | E (Elevation) | Зловредный артефакт в CI/пакете -> внедрение | SCA в CI, разрешения на deploy, review policies | NFR-05 |
| SVC deployment   | E (Elevation) | Контейнер запущен от root -> привилегии | runAsNonRoot, image scanning | NFR-09 |
| Gateway / TLS    | S (Spoofing) | Подмена endpoint (DNS/mitm) | HTTPS, HSTS, secure headers | NFR-01, NFR-02 |
