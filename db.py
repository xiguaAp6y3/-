# -*- coding: utf-8 -*-
"""
数据库模块 - 提供 MySQL 连接管理和表结构初始化

表结构：
  users     - 系统用户
  students  - 学生信息
  courses   - 课程信息
  teachers  - 教师信息
  grades    - 学生成绩
"""

import mysql.connector
from mysql.connector import pooling, Error
from config import DB_CONFIG

# ─── 连接池 ────────────────────────────────────────────────────

_pool = None


def _get_pool():
    """获取（或初始化）连接池"""
    global _pool
    if _pool is None:
        pool_config = dict(DB_CONFIG)
        pool_config["pool_name"] = "school_pool"
        pool_config["pool_size"] = 5
        _pool = pooling.MySQLConnectionPool(**pool_config)
    return _pool


def get_connection():
    """从连接池中获取一个连接"""
    return _get_pool().get_connection()


# ─── 便捷查询工具 ──────────────────────────────────────────────

def execute_query(sql, params=None, fetch=False, fetchone=False):
    """
    执行 SQL 语句

    :param sql: SQL 字符串（使用 %s 占位符）
    :param params: 参数元组或列表
    :param fetch: 若为 True，返回所有行的字典列表
    :param fetchone: 若为 True，返回第一行字典
    :return: fetch/fetchone 时返回数据，否则返回 lastrowid
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        if fetch:
            return cursor.fetchall()
        if fetchone:
            return cursor.fetchone()
        return cursor.lastrowid
    except Error:
        raise
    finally:
        cursor.close()
        conn.close()


def execute_many(sql, data_list):
    """
    批量执行 SQL（executemany）

    :param sql: SQL 字符串
    :param data_list: 参数元组的列表
    """
    if not data_list:
        return
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, data_list)
    except Error:
        raise
    finally:
        cursor.close()
        conn.close()


# ─── 建表 DDL ──────────────────────────────────────────────────

_DDL_STATEMENTS = [
    # 用户表
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id      VARCHAR(10)  NOT NULL,
        username     VARCHAR(50)  NOT NULL,
        password     VARCHAR(64)  NOT NULL COMMENT 'SHA-256 哈希',
        role         VARCHAR(20)  NOT NULL COMMENT 'admin/teacher/student',
        name         VARCHAR(50)  NOT NULL,
        created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id),
        UNIQUE KEY uq_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';
    """,

    # 学生表
    """
    CREATE TABLE IF NOT EXISTS students (
        student_id       VARCHAR(10)   NOT NULL,
        name             VARCHAR(50)   NOT NULL,
        gender           VARCHAR(5)    NOT NULL,
        age              TINYINT       NOT NULL,
        class_name       VARCHAR(50)   NOT NULL,
        major            VARCHAR(100)  NOT NULL,
        phone            VARCHAR(20)   NOT NULL,
        id_number        VARCHAR(20)   NOT NULL COMMENT '身份证号',
        email            VARCHAR(100)  DEFAULT '',
        enrollment_date  VARCHAR(20)   DEFAULT '',
        remark           TEXT,
        created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                         ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (student_id),
        UNIQUE KEY uq_id_number (id_number)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生信息表';
    """,

    # 课程表
    """
    CREATE TABLE IF NOT EXISTS courses (
        course_id    VARCHAR(10)   NOT NULL,
        name         VARCHAR(100)  NOT NULL,
        course_type  VARCHAR(20)   NOT NULL COMMENT '必修/选修/公共基础',
        credits      FLOAT         NOT NULL,
        hours        SMALLINT      NOT NULL,
        semester     VARCHAR(20)   NOT NULL,
        teacher_name VARCHAR(50)   NOT NULL,
        description  TEXT,
        created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                     ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (course_id),
        UNIQUE KEY uq_course_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程信息表';
    """,

    # 教师表
    """
    CREATE TABLE IF NOT EXISTS teachers (
        teacher_id  VARCHAR(10)   NOT NULL,
        name        VARCHAR(50)   NOT NULL,
        gender      VARCHAR(5)    NOT NULL,
        age         TINYINT       NOT NULL,
        title       VARCHAR(20)   NOT NULL COMMENT '助教/讲师/副教授/教授',
        department  VARCHAR(100)  NOT NULL,
        phone       VARCHAR(20)   NOT NULL,
        email       VARCHAR(100)  DEFAULT '',
        research    TEXT,
        remark      TEXT,
        created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (teacher_id),
        UNIQUE KEY uq_teacher_phone (phone)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师信息表';
    """,

    # 成绩表
    """
    CREATE TABLE IF NOT EXISTS grades (
        grade_id    VARCHAR(10)  NOT NULL,
        student_id  VARCHAR(10)  NOT NULL,
        course_id   VARCHAR(10)  NOT NULL,
        score       FLOAT        NOT NULL,
        semester    VARCHAR(20)  NOT NULL,
        remark      TEXT,
        created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (grade_id),
        UNIQUE KEY uq_grade_record (student_id, course_id, semester),
        CONSTRAINT fk_grade_student FOREIGN KEY (student_id)
            REFERENCES students (student_id) ON DELETE CASCADE,
        CONSTRAINT fk_grade_course  FOREIGN KEY (course_id)
            REFERENCES courses  (course_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生成绩表';
    """,
]


def init_db():
    """
    初始化数据库：执行建表 DDL，若表已存在则跳过。
    应在程序启动时调用一次。
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for ddl in _DDL_STATEMENTS:
            cursor.execute(ddl)
        print("  [数据库] 数据库表初始化完成。")
    except Error as exc:
        print(f"  [数据库错误] 初始化失败：{exc}")
        raise
    finally:
        cursor.close()
        conn.close()


# ─── ID 生成 ───────────────────────────────────────────────────

def generate_next_id(table, id_column, prefix):
    """
    从数据库中查询现有最大序号并生成下一个 ID。

    :param table: 表名
    :param id_column: ID 列名
    :param prefix: ID 前缀（如 'S'、'C'、'T'、'G'、'U'）
    :return: 新 ID 字符串，如 'S0011'
    """
    sql = f"SELECT {id_column} FROM {table}"  # noqa: S608
    rows = execute_query(sql, fetch=True)
    existing_nums = set()
    prefix_len = len(prefix)
    for row in rows:
        val = row[id_column]
        if val.startswith(prefix):
            try:
                existing_nums.add(int(val[prefix_len:]))
            except ValueError:
                pass
    n = 1
    while n in existing_nums:
        n += 1
    return f"{prefix}{n:04d}"
