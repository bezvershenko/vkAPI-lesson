import sqlite3


class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def select_all(self, table):
        with self.connection:
            return self.cursor.execute(f'SELECT * FROM {table}').fetchall()

    def select_user(self, uid):
        with self.connection:
            return self.cursor.execute(f'SELECT * FROM users WHERE userId=?', (uid,)).fetchall()

    def add_task(self, word, o1, o2, correct):
        self.cursor.execute("INSERT INTO tasks (word, option_1, option_2, correct)"
                            " VALUES (?, ?, ?, ?)", (word, o1, o2, correct))

        self.connection.commit()

    def delete_user(self, uid):
        self.cursor.execute('DELETE FROM users WHERE userId=?', (uid,))
        self.connection.commit()

    def delete_task(self, word):
        self.cursor.execute('DELETE FROM tasks WHERE word=?', (word,))
        self.connection.commit()

    def add_user(self, uid, name, score=0):
        self.cursor.execute("INSERT INTO users (userId, name, value)"
                            " VALUES (?, ?, ?)", (uid, name, score))
        self.connection.commit()

    def change_value_user(self, uid, upd):
        self.cursor.execute(f"UPDATE users SET value = value + {upd} WHERE userId=?", (uid,))
        self.connection.commit()

    def close(self):
        self.connection.close()
