"""
Комплексные unit тесты для DBoperations.py

Тестирует все функции работы с базой данных с использованием моков psycopg2
"""

import pytest
from unittest.mock import MagicMock, call
import json
from datetime import datetime, date
import DBoperations


class TestUserAuthentication:
    """Тесты функций аутентификации пользователей"""
    
    def test_checkUserEmail_found(self):
        """Проверка поиска пользователя по email"""
        email = "test@example.com"
        expected_user = {"player_id": 1, "email": email}
        DBoperations.cursor.fetchone.return_value = expected_user
        
        result = DBoperations.checkUserEmail(email)
        
        DBoperations.cursor.execute.assert_called_with(
            "SELECT * FROM registered_players WHERE email = %s", (email,)
        )
        assert result == expected_user
    
    def test_checkUserEmail_not_found(self):
        """Проверка отсутствия пользователя по email"""
        DBoperations.cursor.fetchone.return_value = None
        
        result = DBoperations.checkUserEmail("nonexistent@example.com")
        
        assert result is None
    
    def test_checkUserName_found(self):
        """Проверка поиска пользователя по имени"""
        username = "testuser"
        expected_user = {"player_id": 1, "player_name": username}
        DBoperations.cursor.fetchone.return_value = expected_user
        
        result = DBoperations.checkUserName(username)
        
        DBoperations.cursor.execute.assert_called_with(
            "SELECT * FROM registered_players WHERE player_name = %s", (username,)
        )
        assert result == expected_user
    
    def test_checkUserName_not_found(self):
        """Проверка отсутствия пользователя по имени"""
        DBoperations.cursor.fetchone.return_value = None
        
        result = DBoperations.checkUserName("nonexistent")
        
        assert result is None
    
    def test_addNewUser(self):
        """Проверка добавления нового пользователя"""
        username = "newuser"
        email = "new@example.com"
        password_hash = b"hashed_password"
        
        DBoperations.addNewUser(username, email, password_hash)
        
        # Проверяем, что execute был вызван с INSERT
        args, _ = DBoperations.cursor.execute.call_args
        assert "INSERT INTO registered_players" in args[0]
        assert args[1] == (username, "hashed_password", email)
        DBoperations.conn.commit.assert_called()
    
    def test_loginUser_success(self, monkeypatch):
        """Проверка успешного входа пользователя"""
        import bcrypt
        
        username = "testuser"
        password = "testpassword"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        mock_user = {
            'player_id': 1,
            'player_name': username,
            'player_password': hashed.decode('utf-8')
        }
        DBoperations.cursor.fetchone.return_value = mock_user
        
        result = DBoperations.loginUser(username, password)
        
        assert result == mock_user
    
    def test_loginUser_wrong_password(self):
        """Проверка входа с неправильным паролем"""
        import bcrypt
        
        username = "testuser"
        hashed = bcrypt.hashpw("correctpass".encode(), bcrypt.gensalt())
        
        mock_user = {
            'player_id': 1,
            'player_name': username,
            'player_password': hashed.decode('utf-8')
        }
        DBoperations.cursor.fetchone.return_value = mock_user
        
        result = DBoperations.loginUser(username, "wrongpass")
        
        assert result is None
    
    def test_loginUser_user_not_found(self):
        """Проверка входа несуществующего пользователя"""
        DBoperations.cursor.fetchone.return_value = None
        
        result = DBoperations.loginUser("nonexistent", "password")
        
        assert result is None


class TestAdminOperations:
    """Тесты функций администратора"""
    
    def test_isAdmin_true(self):
        """Проверка что пользователь является администратором"""
        player_id = 1
        DBoperations.cursor.fetchone.return_value = {"player_id": player_id, "is_admin": True}
        
        result = DBoperations.isAdmin(player_id)
        
        DBoperations.cursor.execute.assert_called_with(
            "SELECT * FROM registered_players WHERE player_id = %s AND is_admin = true", 
            (player_id,)
        )
        assert result is not None
    
    def test_isAdmin_false(self):
        """Проверка что пользователь не является администратором"""
        DBoperations.cursor.fetchone.return_value = None
        
        result = DBoperations.isAdmin(2)
        
        assert result is None


class TestTaskOperations:
    """Тесты операций с заданиями"""
    
    def test_getTasks(self):
        """Проверка получения всех заданий"""
        expected_tasks = [
            (1, "Math", "Easy", "Algebra", "Task1", "2023-01-01", 1, "2023-01-01", 1, '{}'),
            (2, "Physics", "Hard", "Thermodynamics", "Task2", "2023-01-01", 1, "2023-01-01", 1, '{}')
        ]
        DBoperations.cursor.fetchall.return_value = expected_tasks
        
        result = DBoperations.getTasks()
        
        DBoperations.cursor.execute.assert_called_with("SELECT * FROM tasks ORDER BY id")
        assert result == expected_tasks
    
    def test_getTask(self):
        """Проверка получения одного задания"""
        taskid = 1
        expected_task = {
            'id': taskid, 
            'subject': 'Math',
            'name': 'Task1'
        }
        DBoperations.cursor.fetchone.return_value = expected_task
        
        result = DBoperations.getTask(taskid)
        
        DBoperations.cursor.execute.assert_called_with(
            "SELECT * FROM tasks WHERE id = %s", (taskid,)
        )
        assert result == expected_task
    
    def test_addNewTask(self):
        """Проверка добавления нового задания"""
        task_name = "NewTask"
        subject = "Math"
        complexity = "Easy"
        theme = "Algebra"
        description = "Task description"
        answer = "42"
        hint = "Think about it"
        userid = 1
        
        DBoperations.addNewTask(task_name, subject, complexity, theme, description, answer, hint, userid)
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "INSERT INTO tasks" in args[0]
        assert args[1][0] == subject
        assert args[1][1] == complexity
        assert args[1][2] == theme
        assert args[1][3] == task_name
        DBoperations.conn.commit.assert_called()
    
    def test_updateTask(self):
        """Проверка обновления задания"""
        taskid = 1
        task_name = "Updated"
        subject = "Physics"
        complexity = "Medium"
        theme = "Mechanics"
        description = "New desc"
        answer = "100"
        hint = "New hint"
        
        DBoperations.updateTask(taskid, task_name, subject, complexity, theme, description, answer, hint)
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "UPDATE tasks SET" in args[0]
        DBoperations.conn.commit.assert_called()
    
    def test_deleteTask(self):
        """Проверка удаления задания"""
        taskid = 1
        
        DBoperations.deleteTask(taskid)
        
        DBoperations.cursor.execute.assert_called_with(
            "DELETE FROM tasks WHERE id = %s", (taskid,)
        )
        DBoperations.conn.commit.assert_called()


class TestTaskSolving:
    """Тесты функций решения заданий"""
    
    def test_getSolvation(self):
        """Проверка получения правильного ответа"""
        taskid = 1
        task_json = json.dumps({"answer": "42", "hint": "test"})
        DBoperations.cursor.fetchone.return_value = (task_json,)
        
        result = DBoperations.getSolvation(taskid)
        
        assert result == "42"
    
    def test_setSolvation(self):
        """Проверка сохранения решения"""
        taskid = 1
        userid = 1
        isright = True
        
        DBoperations.setSolvation(taskid, userid, isright)
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "INSERT INTO solved_tasks" in args[0]
        assert args[1] == (userid, taskid, isright)
        DBoperations.conn.commit.assert_called()
    
    def test_solvedTasksBy_true(self):
        """Проверка что задание решено пользователем"""
        DBoperations.cursor.fetchone.return_value = {"user_id": 1, "task_id": 1}
        
        result = DBoperations.solvedTasksBy(1, 1)
        
        assert result is True
    
    def test_solvedTasksBy_false(self):
        """Проверка что задание не решено пользователем"""
        DBoperations.cursor.fetchone.return_value = None
        
        result = DBoperations.solvedTasksBy(1, 1)
        
        assert result is False
    
    def test_howSolved(self):
        """Проверка как решено задание"""
        DBoperations.cursor.fetchone.return_value = (True,)
        
        result = DBoperations.howSolved(1, 1)
        
        assert result is True
    
    def test_isSolved_true(self):
        """Проверка решено ли задание"""
        DBoperations.cursor.fetchone.return_value = {"task_id": 1}
        
        result = DBoperations.isSolved(1, 1)
        
        assert result is True
    
    def test_isSolved_false(self):
        """Проверка нерешенного задания"""
        DBoperations.cursor.fetchone.return_value = None
        
        result = DBoperations.isSolved(1, 1)
        
        assert result is False
    
    def test_startSolving(self):
        """Проверка начала решения задания"""
        userid = 1
        taskid = 1
        
        DBoperations.startSolving(userid, taskid)
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "INSERT INTO task_in_process" in args[0]
        assert args[1] == (userid, taskid)
        DBoperations.conn.commit.assert_called()
    
    def test_setSolvationTime(self):
        """Проверка установки времени решения"""
        taskid = 1
        userid = 1
        
        DBoperations.setSolvationTime(taskid, userid)
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "UPDATE task_in_process SET ended_at" in args[0]
        DBoperations.conn.commit.assert_called()
    
    def test_setHintStatus(self):
        """Проверка установки статуса подсказки"""
        taskid = 1
        userid = 1
        
        DBoperations.setHintStatus(taskid, userid)
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "UPDATE task_in_process SET is_hinted = true" in args[0]
        DBoperations.conn.commit.assert_called()


class TestTaskFiltering:
    """Тесты фильтрации и экспорта заданий"""
    
    def test_taskFilter_all_params(self):
        """Проверка фильтрации по всем параметрам"""
        subject = "Math"
        theme = "Algebra"
        complexity = "Easy"
        DBoperations.cursor.fetchall.return_value = [(1,), (2,), (3,)]
        
        result = DBoperations.taskFilter(subject, theme, complexity)
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "WHERE" in args[0]
        assert "subject = %s" in args[0]
        assert "theme = %s" in args[0]
        assert "complexity = %s" in args[0]
        assert result == [1, 2, 3]
    
    def test_taskFilter_no_params(self):
        """Проверка фильтрации без параметров"""
        DBoperations.cursor.fetchall.return_value = [(1,), (2,)]
        
        result = DBoperations.taskFilter("", "", "")
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "WHERE" not in args[0]
        assert result == [1, 2]
    
    def test_listSubjects(self):
        """Проверка получения списка предметов"""
        DBoperations.cursor.fetchall.return_value = [("Math",), ("Physics",)]
        
        result = DBoperations.listSubjects()
        
        DBoperations.cursor.execute.assert_called_with("SELECT DISTINCT subject FROM tasks")
        assert result == ["", "Math", "Physics"]
    
    def test_exportToJSON(self):
        """Проверка экспорта задания в JSON"""
        taskid = 1
        task_data = {
            'subject': 'Math',
            'complexity': 'Easy',
            'theme': 'Algebra',
            'name': 'Task1',
            'task': '{"answer": "42"}'
        }
        DBoperations.cursor.fetchone.return_value = task_data
        
        result = DBoperations.exportToJSON(taskid)
        
        # Проверяем что вернулся JSON
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed['subject'] == 'Math'
    
    def test_importFromJSON(self):
        """Проверка импорта задания из JSON"""
        userid = 1
        task_json = json.dumps({
            'subject': 'Math',
            'complexity': 'Easy',
            'theme': 'Algebra',
            'name': 'ImportedTask',
            'task': '{"desc": "Description", "answer": "42", "hint": "Hint"}'
        })
        
        DBoperations.importFromJSON(userid, task_json)
        
        # Проверяем что вызвалась функция добавления задания
        args, _ = DBoperations.cursor.execute.call_args
        assert "INSERT INTO tasks" in args[0]
        DBoperations.conn.commit.assert_called()


class TestContestOperations:
    """Тесты операций с соревнованиями"""
    
    def test_listContests(self):
        """Проверка получения списка соревнований"""
        expected_contests = [
            (1, "user1", "user2", "Math", "Easy", datetime.now(), datetime.now(), "Завершено"),
            (2, "user3", "user4", "Physics", "Hard", datetime.now(), datetime.now(), "В процессе")
        ]
        DBoperations.cursor.fetchall.return_value = expected_contests
        
        result = DBoperations.listContests()
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "SELECT" in args[0]
        assert "FROM contests" in args[0]
        assert result == expected_contests


class TestScoreTracking:
    """Тесты отслеживания рейтинга"""
    
    def test_daily_score_backup(self):
        """Проверка ежедневного сохранения рейтинга"""
        mock_players = [
            (1, "player1", 1000, "pass", "email1"),
            (2, "player2", 1500, "pass", "email2")
        ]
        DBoperations.cursor.fetchall.return_value = mock_players
        
        DBoperations.daily_score_backup()
        
        # Проверяем что INSERT вызывался для каждого игрока
        assert DBoperations.cursor.execute.call_count >= 1
        DBoperations.conn.commit.assert_called()
    
    def test_takeScorebyDays(self):
        """Проверка получения рейтинга по дням"""
        player_id = 1
        expected_scores = [
            (date(2023, 1, 1), 1000),
            (date(2023, 1, 2), 1050)
        ]
        DBoperations.cursor.fetchall.return_value = expected_scores
        
        result = DBoperations.takeScorebyDays(player_id)
        
        args, _ = DBoperations.cursor.execute.call_args
        assert "SELECT date, player_score FROM score_archive" in args[0]
        assert args[1][0] == player_id
        assert result == expected_scores
