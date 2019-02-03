# -*- coding: utf-8 -*-
import logging
import os
import sqlite3

__author__ = 'Rico'


class DBwrapper(object):
    class __DBwrapper(object):
        dir_path = os.path.dirname(os.path.abspath(__file__))

        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.debug("Initializing SQLite")

            current_path = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(current_path, "users.db")

            # Check if the folder path exists
            if not os.path.exists(os.path.dirname(self.db_path)):
                # If not, create the path and the file
                self.logger.info("Creating file for database")
                os.mkdir(os.path.dirname(self.db_path))
                open(self.db_path, "a").close()

            try:
                self.db = sqlite3.connect(self.db_path)
                self.db.text_factory = lambda x: str(x, 'utf-8', "ignore")
                self.cursor = self.db.cursor()
                self._create_tables()
            except Exception as e:
                self.logger.exception("An exception happened when initializing the database: {0}".format(e))
                raise

        def _create_tables(self):
            self.logger.info("Creating db tables!")
            open(self.db_path, "a").close()

            self.cursor.execute("""CREATE TABLE IF NOT EXISTS 'users' (
                                'userID' INTEGER NOT NULL UNIQUE,
                                'languageID' TEXT,
                                'first_name' TEXT,
                                'last_name' TEXT,
                                'username' TEXT,
                                'gender' INTEGER NOT NULL,
                                'age' INTEGER,
                                'registration_date' TEXT,
                                'banned' INTEGER NOT NULL,
                                PRIMARY KEY('userID'))""")
            self.db.commit()

        def get_user(self, user_id):
            self.cursor.execute("SELECT * FROM users WHERE userID=?;", [str(user_id)])

            result = self.cursor.fetchall()
            if len(result) > 0:
                return result[0]
            else:
                return []

        def get_all_users(self):
            self.cursor.execute("SELECT userID FROM users;")
            all_users = self.cursor.fetchall()
            tmp_users = []
            for user in all_users:
                tmp_users.append(user[0])
            return tmp_users

        def add_user(self, user_id, lang_id, first_name, last_name, username):
            self.cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", [str(user_id), str(lang_id), str(first_name), str(last_name), str(username), "0", "0", "0", "0"])
            self.db.commit()

        def insert(self, string_value, value, user_id):
            self.cursor.execute("UPDATE users SET " + str(string_value) + "= ? WHERE userID = ?;", [str(value), str(user_id)])
            self.db.commit()

        def ban(self, user_id):
            self.cursor.execute("UPDATE users SET banned = 1 WHERE userID = ?;", [str(user_id)])
            self.db.commit()

        def unban(self, user_id):
            self.cursor.execute("UPDATE users SET banned = 0 WHERE userID = ?;", [str(user_id)])
            self.db.commit()

        def get_banned_users(self):
            self.cursor.execute("SELECT userID FROM users WHERE banned != 0;")
            users = self.cursor.fetchall()
            banned_users = []
            for user in users:
                banned_users.append(user[0])

            return banned_users

        def check_if_user_saved(self, user_id):
            self.cursor.execute("SELECT rowid, * FROM users WHERE userID=?;", [str(user_id)])

            result = self.cursor.fetchall()
            if len(result) > 0:
                return result[0]
            else:
                return -1

        def user_data_changed(self, user_id, first_name, last_name, username):
            self.cursor.execute("SELECT * FROM users WHERE userID=?;", [str(user_id)])

            result = self.cursor.fetchone()

            if result[2] == first_name and result[3] == last_name and result[4] == username:
                return False
            return True

        def update_user_data(self, user_id, first_name, last_name):
            self.cursor.execute("UPDATE users SET first_name=?, last_name=?, WHERE userID=?;", (str(first_name), str(last_name), str(user_id)))
            self.db.commit()

        def close_conn(self):
            self.db.close()

    instance = None

    def __init__(self):
        if not DBwrapper.instance:
            DBwrapper.instance = DBwrapper.__DBwrapper()

    @staticmethod
    def get_instance() -> __DBwrapper:
        if not DBwrapper.instance:
            DBwrapper.instance = DBwrapper.__DBwrapper()

        return DBwrapper.instance
