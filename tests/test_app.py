"""
Комплексные unit тесты для Flask маршрутов в app.py

Тестирует все маршруты с использованием моков для DBoperations
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import json
import os
from io import BytesIO
import DBoperations


class MockUser(list):
    """Класс для мокирования результатов DictCursor"""
    def __getitem__(self, key):
        if isinstance(key, str):
            mappings = {
                'player_password': self[2] if len(self) > 2 else 'pass',
                'player_name': self[1] if len(self) > 1 else 'user',
                'email': self[4] if len(self) > 4 else 'email@test.com',
                'player_id': self[0] if len(self) > 0 else 1
            }
            return mappings.get(key, super().__getitem__(key))
        return super().__getitem__(key)


class TestAuthenticationRoutes:
    """Тесты маршрутов аутентификации"""
    
    def test_mainpage(self, client):
        """Проверка главной страницы"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_login_page_get(self, client):
        """Проверка GET запроса на страницу входа"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b"login" in response.data.lower()
    
    def test_login_post_success(self, client, monkeypatch):
        """Проверка успешного входа"""
        import bcrypt
        password = "testpassword"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        user_data = MockUser([1, "testuser", hashed.decode('utf-8'), "score", "test@example.com"])
        
        monkeypatch.setattr(DBoperations, "loginUser", MagicMock(return_value=user_data))
        monkeypatch.setattr(DBoperations, "isAdmin", MagicMock(return_value=False))
        monkeypatch.setattr("os.path.exists", MagicMock(return_value=False))
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': password
        })
        
        assert response.status_code == 302
        assert "/dashboard" in response.location
        
        with client.session_transaction() as sess:
            assert sess['loggedin'] == True
            assert sess['username'] == "testuser"
    
    def test_login_post_failure(self, client, monkeypatch):
        """Проверка неудачного входа"""
        monkeypatch.setattr(DBoperations, "loginUser", MagicMock(return_value=None))
        
        response = client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 200
        assert "Аккаунта не существует".encode('utf-8') in response.data
    
    def test_logout(self, client):
        """Проверка выхода из системы"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
            sess['username'] = 'testuser'
        
        response = client.get('/logout')
        
        assert response.status_code == 302
        assert "/login" in response.location
        
        with client.session_transaction() as sess:
            assert 'loggedin' not in sess
    
    def test_register_get(self, client):
        """Проверка GET запроса на страницу регистрации"""
        response = client.get('/register')
        assert response.status_code == 200
    
    def test_register_post_success(self, client, monkeypatch):
        """Проверка успешной регистрации"""
        monkeypatch.setattr(DBoperations, "checkUserEmail", MagicMock(return_value=None))
        monkeypatch.setattr(DBoperations, "checkUserName", MagicMock(return_value=None))
        monkeypatch.setattr(DBoperations, "addNewUser", MagicMock())
        
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 302
        assert "/dashboard" in response.location
    
    def test_register_duplicate_email(self, client, monkeypatch):
        """Проверка регистрации с существующим email"""
        monkeypatch.setattr(DBoperations, "checkUserEmail", MagicMock(return_value={"email": "exists"}))
        
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'exists@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert "зарегистрирована".encode('utf-8') in response.data
    
    def test_register_duplicate_username(self, client, monkeypatch):
        """Проверка регистрации с существующим именем"""
        monkeypatch.setattr(DBoperations, "checkUserEmail", MagicMock(return_value=None))
        monkeypatch.setattr(DBoperations, "checkUserName", MagicMock(return_value={"username": "exists"}))
        
        response = client.post('/register', data={
            'username': 'exists',
            'email': 'new@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert "используется".encode('utf-8') in response.data
    
    def test_register_short_password(self, client, monkeypatch):
        """Проверка регистрации с коротким паролем"""
        monkeypatch.setattr(DBoperations, "checkUserEmail", MagicMock(return_value=None))
        monkeypatch.setattr(DBoperations, "checkUserName", MagicMock(return_value=None))
        
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'short'
        })
        
        assert response.status_code == 200
        assert "8 и более".encode('utf-8') in response.data


class TestDashboardRoute:
    """Тесты маршрута dashboard"""
    
    def test_dashboard_not_logged_in(self, client):
        """Проверка dashboard без авторизации"""
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert "/login" in response.location
    
    def test_dashboard_logged_in(self, client, monkeypatch):
        """Проверка dashboard с авторизацией"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
            sess['username'] = 'testuser'
        
        from datetime import date
        mock_scores = [
            (date(2023, 1, 1), 1000),
            (date(2023, 1, 2), 1050)
        ]
        monkeypatch.setattr(DBoperations, "takeScorebyDays", MagicMock(return_value=mock_scores))
        
        response = client.get('/dashboard')
        assert response.status_code == 200


class TestTaskManagementRoutes:
    """Тесты маршрутов управления заданиями"""
    
    def test_tasks_not_admin(self, client, monkeypatch):
        """Проверка доступа к заданиям для не-администратора"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 2
        
        monkeypatch.setattr(DBoperations, "isAdmin", MagicMock(return_value=None))
        
        response = client.get('/tasks')
        assert response.status_code == 200
        assert b"404" in response.data
    
    def test_tasks_admin(self, client, monkeypatch):
        """Проверка доступа к заданиям для администратора"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        monkeypatch.setattr(DBoperations, "isAdmin", MagicMock(return_value={'is_admin': True}))
        mock_tasks = [(1, "Math", "Easy", "Algebra", "Task1", "2023-01-01", 1, "2023-01-01", 1, '{}')]
        monkeypatch.setattr(DBoperations, "getTasks", MagicMock(return_value=mock_tasks))
        
        response = client.get('/tasks')
        assert response.status_code == 200
    
    def test_task_detail(self, client, monkeypatch):
        """Проверка просмотра деталей задания"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        monkeypatch.setattr(DBoperations, "isAdmin", MagicMock(return_value={'is_admin': True}))
        
        task_data = {
            'id': 1,
            'name': 'Task1',
            'subject': 'Math',
            'complexity': 'Easy',
            'theme': 'Algebra',
            9: '{"desc": "Description", "answer": "42", "hint": "Hint"}'
        }
        monkeypatch.setattr(DBoperations, "getTask", MagicMock(return_value=task_data))
        
        response = client.get('/task/1')
        assert response.status_code == 200
    
    def test_new_task_get(self, client, monkeypatch):
        """Проверка GET запроса на создание задания"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        monkeypatch.setattr(DBoperations, "isAdmin", MagicMock(return_value={'is_admin': True}))
        
        response = client.get('/new_task')
        assert response.status_code == 200
    
    def test_post_new_task(self, client, monkeypatch):
        """Проверка POST запроса создания задания"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        monkeypatch.setattr(DBoperations, "isAdmin", MagicMock(return_value={'is_admin': True}))
        monkeypatch.setattr(DBoperations, "addNewTask", MagicMock())
        
        response = client.post('/post_new_task', data={
            'task_name': 'NewTask',
            'subject': 'Math',
            'complexity': 'Easy',
            'theme': 'Algebra',
            'description': 'Desc',
            'answer': '42',
            'hint': 'Hint'
        })
        
        assert response.status_code == 302
        assert "/tasks" in response.location


class TestTaskSolvingRoutes:
    """Тесты маршрутов решения заданий"""
    
    def test_choose_task(self, client, monkeypatch):
        """Проверка страницы выбора задания"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        mock_tasks = [(1, "Math", "Easy", "Algebra", "Task1", "2023-01-01", 1, "2023-01-01", 1, '{}')]
        monkeypatch.setattr(DBoperations, "getTasks", MagicMock(return_value=mock_tasks))
        monkeypatch.setattr(DBoperations, "taskFilter", MagicMock(return_value=[1]))
        monkeypatch.setattr(DBoperations, "solvedTasksBy", MagicMock(return_value=False))
        monkeypatch.setattr(DBoperations, "listSubjects", MagicMock(return_value=["", "Math"]))
        
        response = client.get('/choose_task')
        assert response.status_code == 200
    
    def test_solve_task_get(self, client, monkeypatch):
        """Проверка GET запроса решения задания"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        task_data = {
            'id': 1,
            4: 'Task1',
            2: 'Easy',
            3: 'Algebra',
            9: '{"desc": "Description", "answer": "42", "hint": "Hint"}'
        }
        monkeypatch.setattr(DBoperations, "getTask", MagicMock(return_value=task_data))
        monkeypatch.setattr(DBoperations, "startSolving", MagicMock())
        monkeypatch.setattr(DBoperations, "isSolved", MagicMock(return_value=False))
        monkeypatch.setattr(DBoperations, "getSolvation", MagicMock(return_value="42"))
        
        response = client.get('/solve_task/1')
        assert response.status_code == 200
    
    def test_solve_task_post_correct(self, client, monkeypatch):
        """Проверка POST правильного ответа"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        task_data = {
            'id': 1,
            4: 'Task1',
            2: 'Easy',
            3: 'Algebra',
            9: '{"desc": "Description", "answer": "42", "hint": "Hint"}'
        }
        monkeypatch.setattr(DBoperations, "getTask", MagicMock(return_value=task_data))
        monkeypatch.setattr(DBoperations, "startSolving", MagicMock())
        monkeypatch.setattr(DBoperations, "isSolved", MagicMock(return_value=False))
        monkeypatch.setattr(DBoperations, "getSolvation", MagicMock(return_value="42"))
        monkeypatch.setattr(DBoperations, "setSolvationTime", MagicMock())
        monkeypatch.setattr(DBoperations, "setSolvation", MagicMock())
        monkeypatch.setattr(DBoperations, "howSolved", MagicMock(return_value=True))
        
        response = client.post('/solve_task/1', data={'answer': '42'})
        assert response.status_code == 200
        assert "верно".encode('utf-8') in response.data


class TestFileOperations:
    """Тесты файловых операций"""
    
    def test_upload_avatar(self, client, monkeypatch):
        """Проверка загрузки аватара"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        monkeypatch.setattr("os.path.exists", MagicMock(return_value=True))
        monkeypatch.setattr("os.makedirs", MagicMock())
        
        # Мокируем сохранение файла
        data = {
            'file': (BytesIO(b"fake image data"), 'test.jpg')
        }
        
        with patch('builtins.open', mock_open()):
            response = client.post('/upload_avatar', 
                                  data=data,
                                  content_type='multipart/form-data')
        
        # Может быть редирект на /account или /dashboard
        assert response.status_code in [200, 302]
    
    def test_download_task(self, client, monkeypatch):
        """Проверка скачивания задания"""
        task_json = json.dumps({
            'subject': 'Math',
            'complexity': 'Easy',
            'theme': 'Algebra',
            'name': 'Task1',
            'task': '{"answer": "42"}'
        })
        monkeypatch.setattr(DBoperations, "exportToJSON", MagicMock(return_value=task_json))
        
        response = client.get('/download/1')
        assert response.status_code == 200
        assert response.mimetype == 'text/json'
    
    def test_import_task(self, client, monkeypatch):
        """Проверка импорта задания"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        monkeypatch.setattr(DBoperations, "isAdmin", MagicMock(return_value={'is_admin': True}))
        monkeypatch.setattr(DBoperations, "importFromJSON", MagicMock())
        
        task_json = json.dumps({
            'subject': 'Math',
            'complexity': 'Easy',
            'theme': 'Algebra',
            'name': 'ImportedTask',
            'task': '{"desc": "Desc", "answer": "42", "hint": "Hint"}'
        })
        
        data = {
            'file': (BytesIO(task_json.encode()), 'task.json')
        }
        
        response = client.post('/import_task',
                              data=data,
                              content_type='multipart/form-data')
        
        assert response.status_code == 302


class TestContestRoutes:
    """Тесты маршрутов соревнований"""
    
    def test_contests_list(self, client, monkeypatch):
        """Проверка списка соревнований"""
        from datetime import datetime
        mock_contests = [
            (1, "user1", "user2", "Math", "Easy", datetime.now(), datetime.now(), "Завершено")
        ]
        monkeypatch.setattr(DBoperations, "listContests", MagicMock(return_value=mock_contests))
        
        response = client.get('/contests')
        assert response.status_code == 200
    
    def test_contests_empty(self, client, monkeypatch):
        """Проверка пустого списка соревнований"""
        monkeypatch.setattr(DBoperations, "listContests", MagicMock(return_value=[]))
        
        response = client.get('/contests')
        assert response.status_code == 200
        # Проверяем что в ответе есть текст о соревнованиях (может быть просто структура страницы)
        assert "Соревнования".encode('utf-8') in response.data or b"contests" in response.data.lower()


class TestErrorHandlers:
    """Тесты обработчиков ошибок"""
    
    def test_404_error(self, client):
        """Проверка страницы 404"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404


class TestHelperFunctions:
    """Тесты вспомогательных функций"""
    
    def test_allowed_file_valid(self, app):
        """Проверка разрешенного расширения файла"""
        from app import allowed_file
        
        assert allowed_file('image.jpg', {'jpg', 'png'}) == True
        assert allowed_file('image.png', {'jpg', 'png'}) == True
    
    def test_allowed_file_invalid(self, app):
        """Проверка запрещенного расширения файла"""
        from app import allowed_file
        
        assert allowed_file('file.txt', {'jpg', 'png'}) == False
        assert allowed_file('noextension', {'jpg', 'png'}) == False
    
    def test_account_route(self, client, monkeypatch):
        """Проверка маршрута аккаунта"""
        with client.session_transaction() as sess:
            sess['loggedin'] = True
            sess['id'] = 1
        
        monkeypatch.setattr("os.path.exists", MagicMock(return_value=False))
        
        response = client.get('/account')
        assert response.status_code == 200
