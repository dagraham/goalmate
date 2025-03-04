import sqlite3
from datetime import datetime
import os
from modules.common import log_msg


class DatabaseManager:
    def __init__(self, db_path: str = "goals.db", reset: bool = False):
        if reset and os.path.exists(db_path):
            os.remove(db_path)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.enable_foreign_keys()  # ✅ Enable foreign keys
        self.setup_database()

    def enable_foreign_keys(self):
        """Ensure SQLite enforces foreign keys (required for ON DELETE CASCADE)."""
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.conn.commit()

    def setup_database(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                time INTEGER DEFAULT 0,
                goal INTEGER DEFAULT 0,
                warn INTEGER DEFAULT 0,
                created INTEGER DEFAULT 0,
                modified INTEGER DEFAULT 0
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Completions (
                completion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                completion INTEGER,
                FOREIGN KEY (goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def add_goal(
        self,
        name: str,
        time: str,
        goal: int,
        warn: int,
        created: int = round(datetime.now().timestamp()),
        modified: int = round(datetime.now().timestamp()),
    ):
        """Add a new goal and return its ID."""
        if isinstance(created, datetime):
            created = round(created.timestamp())
        warn = 0 if goal + warn < 0 else warn
        log_msg(
            f"Adding goal {name} with time {time}, goal {goal}, warn {warn}, created {created}, modified {modified}"
        )
        self.cursor.execute(
            "INSERT INTO goals (name, time, goal, warn, created, modified) VALUES (?, ?, ?, ?, ?, ?)",
            (name, time, goal, warn, created, modified),
        )
        new_goal_id = self.cursor.lastrowid  # Retrieve the new record ID
        self.conn.commit()
        log_msg(f"Finished adding goal {name} with ID {new_goal_id}.")
        return new_goal_id  # Return the ID to the caller

    def remove_goal(self, goal_id):
        log_msg(f"Removing goal {goal_id}")
        self.cursor.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))
        self.conn.commit()

    def record_completion(self, goal_id, completion):
        self.cursor.execute("SELECT goal_id FROM goals WHERE goal_id = ?", (goal_id,))
        goal = self.cursor.fetchone()

        if not goal:
            return

        goal_id = goal[0]

        if isinstance(completion, datetime):
            completion = round(completion.timestamp())
        modified = round(datetime.now().timestamp())

        log_msg(f"*Completing goal {goal_id} at {completion}")

        self.cursor.execute(
            "INSERT INTO Completions (goal_id, completion) VALUES (?, ?)",
            (goal_id, completion),
        )
        self.cursor.execute(
            "UPDATE goals SET modified = ? WHERE goal_id = ?",
            (modified, goal_id),
        )
        self.conn.commit()

    def list_goals(self):
        self.cursor.execute("""
            SELECT goal_id, name, time, goal, warn, created, 
                (SELECT COUNT(*) FROM Completions 
                WHERE goal_id = g.goal_id 
                AND completion >= strftime('%s', 'now') - g.time) AS done
            FROM goals g
            ORDER BY name
        """)
        return self.cursor.fetchall()

    def list_completions(self, goal_id):
        """Retrieve all completions for a given goal_id."""
        self.cursor.execute(
            """
            SELECT completion FROM Completions
            WHERE goal_id = ?
            ORDER BY completion ASC
        """,
            (goal_id,),
        )

        return [row[0] for row in self.cursor.fetchall()]

    def show_goal(self, goal_id):
        self.cursor.execute(
            """
            SELECT goal_id, name, time, goal, warn, created, modified, 
            (SELECT COUNT(*) FROM Completions WHERE Completions.goal_id = goals.goal_id) AS num_completions
            FROM goals WHERE goal_id = ?
        """,
            (goal_id,),
        )
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()

    # def get_goal_progress(self, goal_id):
    #     """Retrieve goal progress: number of completions within the time from now."""
    #
    #     self.cursor.execute(
    #         """
    #         SELECT
    #             g.goal_id,
    #             g.name,
    #             g.goal,
    #             g.time,
    #             g.created,
    #             (SELECT COUNT(*) FROM Completions
    #             WHERE goal_id = g.goal_id
    #             AND completion >= strftime('%s', 'now') - g.time) AS done
    #         FROM goals g
    #         WHERE g.goal_id = ?;
    #     """,
    #         (goal_id,),
    #     )
    #
    #     return self.cursor.fetchone()
