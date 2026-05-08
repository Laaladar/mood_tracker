# Диаграмма последовательности (Sequence Diagram)

Этот документ визуализирует взаимодействие между компонентами системы при выполнении ключевых операций.

## Процесс сохранения записи настроения

Ниже показано, как данные проходят путь от нажатия кнопки в браузере до сохранения в файле базы данных.

```mermaid
sequenceDiagram
    autonumber
    actor User as Пользователь
    participant Browser as Browser (JS)
    participant Server as Flask Server
    participant DB as SQLite DB

    User->>Browser: Нажимает "Сохранить"
    
    activate Browser
    Browser->>Browser: Сбор данных из полей формы
    Browser->>Server: POST /api/mood (JSON + Cookie сессии)
    
    activate Server
    Server->>Server: Проверка авторизации (session.get)
    
    alt Не авторизован
        Server-->>Browser: 401 Unauthorized
        Browser-->>User: Показать форму входа
    else Авторизован
        Server->>DB: INSERT INTO logs (user_id, score, word...)
        activate DB
        DB-->>Server: Успешная запись (ID строки)
        deactivate DB
        
        Server-->>Browser: 201 Created (Success)
        deactivate Server
        
        Browser->>Browser: Очистка полей ввода
        Browser->>User: Обновление списка истории на экране
    end
    deactivate Browser
```

## Пояснения к этапам:
1. **Cookie сессии (шаг 3)**: Браузер автоматически прикрепляет куки к запросу, чтобы Flask понял, какой именно пользователь пишет в дневник.
2. **Асинхронность**: Пока Flask общается с базой данных (шаги 6-7), браузер «ждет» ответа (именно поэтому мы используем `await fetch`).
3. **Обработка ошибок**: Если база данных будет занята или недоступна, цепочка прервется на шаге 7, и сервер вернет ошибку 500.
