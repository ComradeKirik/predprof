# Инструкция по запуску Unit Тестов

## Предварительные требования

Убедитесь, что установлены все зависимости из `requirements.txt`:

```bash
# Активируйте виртуальное окружение (если используется)
# Затем установите зависимости
py -m pip install -r requirements.txt
```

## Запуск тестов

### Запуск всех тестов

```bash
# Из директории проекта predprof
py -m pytest tests/ -v
```

### Запуск конкретного файла тестов

```bash
# Тесты операций с базой данных
py -m pytest tests/test_db_operations.py -v

# Тесты маршрутов Flask
py -m pytest tests/test_app.py -v

# Тесты WebSocket
py -m pytest tests/test_websocket.py -v
```

### Запуск с отчетом о покрытии кода

```bash
# Запуск с coverage
py -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Просмотр HTML отчета
# Откройте файл htmlcov/index.html в браузере
```

### Запуск конкретного теста

```bash
# Запуск конкретного класса тестов
py -m pytest tests/test_db_operations.py::TestUserAuthentication -v

# Запуск конкретного теста
py -m pytest tests/test_db_operations.py::TestUserAuthentication::test_checkUserEmail_found -v
```

## Структура тестов

- **tests/conftest.py** - Конфигурация pytest и фикстуры
- **tests/test_db_operations.py** - Тесты для DBoperations.py (45+ тестов)
  - TestUserAuthentication - Аутентификация пользователей
  - TestAdminOperations - Операции администратора
  - TestTaskOperations - CRUD операции с заданиями
  - TestTaskSolving - Решение заданий
  - TestTaskFiltering - Фильтрация и экспорт/импорт
  - TestContestOperations - Операции с соревнованиями
  - TestScoreTracking - Отслеживание рейтинга
  
- **tests/test_app.py** - Тесты для маршрутов Flask (30+ тестов)
  - TestAuthenticationRoutes - Маршруты аутентификации
  - TestDashboardRoute - Dashboard
  - TestTaskManagementRoutes - Управление заданиями
  - TestTaskSolvingRoutes - Решение заданий
  - TestFileOperations - Файловые операции
  - TestContestRoutes - Маршруты соревнований
  - TestErrorHandlers - Обработчики ошибок
  - TestHelperFunctions - Вспомогательные функции
  
- **tests/test_websocket.py** - Тесты WebSocket обработчиков (3 теста)

## Возможные проблемы

### ModuleNotFoundError: No module named 'pytest'

Установите pytest:
```bash
py -m pip install pytest pytest-mock pytest-flask coverage
```

### Проблемы с импортом psycopg2

Тесты мокируют psycopg2, поэтому реальное подключение к базе данных не требуется.
Если возникают проблемы, убедитесь что conftest.py загружается первым.

### Проблемы с путями

Запускайте тесты из корневой директории проекта (`predprof`), а не из директории `tests`.

## Ожидаемые результаты

- Все тесты должны пройти успешно (PASSED)
- Покрытие кода должно быть >70% для основных модулей
- Некоторые тесты могут быть пропущены (SKIPPED) в зависимости от окружения

## Примеры вывода

```bash
PS D:\Разное\Dev\predprof> py -m pytest tests/ -v
============================== test session starts ==============================
collected 78 items

tests/test_app.py::TestAuthenticationRoutes::test_login_page_get PASSED    [  1%]
tests/test_app.py::TestAuthenticationRoutes::test_login_post_success PASSED [  2%]
...
tests/test_websocket.py::TestWebSocketHandlers::test_socket_message PASSED [ 100%]

============================== 78 passed in 2.5s ================================
```
