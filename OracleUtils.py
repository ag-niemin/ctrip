# -*- coding: utf-8 -*-
import datetime
import string
import cx_Oracle
import math
import os

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


class Oracle(object):
    def __init__(self, tns='10.6.0.94:1521/db', user='stg', password='stg123'):
        self.TNS = tns
        self.User = user
        self.Password = password

    def execProc(self, name, parameters=[]):
        try:
            db = cx_Oracle.connect(self.User, self.Password, self.TNS)
            # print db.dsn
            # print db.version
            c = db.cursor()
            c.callproc(name, parameters)
        finally:
            db.close()
        return 0

    def select(self, sql="select * from dual"):
        rs = []
        try:
            db = cx_Oracle.connect(self.User, self.Password, self.TNS)
            # print db.dsn
            # print db.version
            c = db.cursor()
            c.execute(sql)
            for row in c:
                rs.append(row)
        finally:
            db.close()
        return rs

    def execsql(self, sql="select * from dual"):
        try:
            db = cx_Oracle.connect(self.User, self.Password, self.TNS)
            # print db.dsn
            # print db.version
            c = db.cursor()
            c.execute(sql)
        except Exception as e:
            print(str(e))
        finally:
            db.commit()
            db.close()
        return 0

    def execsqls(self, sqls=[]):
        try:
            db = cx_Oracle.connect(self.User, self.Password, self.TNS)
            # print db.dsn
            # print db.version
            c = db.cursor()
            for sql in sqls:
                # print sql
                c.execute(sql)
        finally:
            db.commit()
            db.close()
        return 0

    def batchinsert(self, deleteSQL, insertSQL, insertValues=[]):

        try:
            db = cx_Oracle.connect(self.User, self.Password, self.TNS)
            # print db.dsn
            # print db.version
            c = db.cursor()
            print(deleteSQL)
            c.execute(deleteSQL)
            print(insertSQL)
            c.prepare(insertSQL)
            c.executemany(None, insertValues)
        finally:
            db.commit()
            db.close()
        return 0

    def batchUpdate(self, updateSQL, updateValues=[]):

        try:
            db = cx_Oracle.connect(self.User, self.Password, self.TNS)
            # print db.dsn
            # print db.version
            c = db.cursor()
            print(updateSQL)
            c.prepare(updateSQL)
            c.executemany(None, updateValues)
        finally:
            db.commit()
            db.close()
        return 0

    def batchinsert_ex(self, deleteSQL, deleteValues, insertSQL, insertValues=[]):

        try:
            db = cx_Oracle.connect(self.User, self.Password, self.TNS)
            # print db.dsn
            # print db.version
            c = db.cursor()
            # print deleteSQL
            c.prepare(deleteSQL)
            c.executemany(None, deleteValues)

            # print insertSQL
            c.prepare(insertSQL)
            c.executemany(None, insertValues)
        finally:
            db.commit()
            db.close()
        return 0

