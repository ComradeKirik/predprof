Это папка с заданиями для олимпиад.
/olympiads/предмет/год/id.png(или иной формат)
Каждый айдишник задания хранится в таблице tasks_[предмет]:
id SERIAL INT PRIMARY KEY
year DATE
olympiad TEXT
difficulty INT
grade INT
answer TEXT
stage INT
UNIQUE(id)

Вроде все?
Чтобы не давать одному и тому же человеку одинаковые задания, будет создана таблица с решениями:
id SERIAL PRIMARY KEY,
task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
user_id INTEGER NOT NULL,
solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
UNIQUE(task_id, user_id)

Потом все додумаю. Сейчас я в зомбоид.