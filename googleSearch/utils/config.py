# -*- coding: utf-8 -*-
# @Time    : 2021/1/19 16:26
# @Author  : Haijun

from dynaconf import settings
import redis
import pymysql


class DatabaseConnection(object):
    try:
        redis_conn = redis.StrictRedis(host=settings.REDIS.HOST, port=settings.REDIS.PORT, db=settings.REDIS.DB,
                                       password=settings.REDIS.PASSWD)
        sql_conn = pymysql.connect(host=settings.MYSQL.HOST, user=settings.MYSQL.USER, password=settings.MYSQL.PASSWD,
                                   database=settings.MYSQL.DATABASE,
                                   port=settings.MYSQL.PORT)
    except Exception as e:
        pass