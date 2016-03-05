# coding=utf-8
__author__ = 'elmira'

import MySQLdb as mdb


class Database(object):
    """Класс для общения с базой данных MySQL"""
    
    def __init__(self):
        """Создать соединение с базой данных.

        В параметрах соединения указывается хост, логин, пароль, название базы данных, кодировка.
        """
        self._connection = mdb.connect('', 'webcorpo_corpora', 'yedLurt3', 'heritage_corpus', charset='utf8')

    def commit(self):
        self._connection.commit()

    def execute(self, q):
        """Вернуть результат выполнения запроса в виде массива кортежей.

        Каждый кортеж - строка базы данных, сформированная по запросу.
        """
        self.cur = self._connection.cursor()  # mdb.cursors.DictCursor
        self.cur.execute(q)
        res = self.cur.fetchall()
        self.cur.close()
        return res