# -*- coding: utf-8 -*-
"""
简单的信息管理系统 - 主入口
包含：学生管理、课程管理、教师管理、成绩管理、用户管理
数据存储：MySQL 数据库（详见 db.py 和 config.py）

作者：系统默认
版本：2.0.0
"""

import sys

from db import init_db
from utils import print_title, print_menu, print_separator, pause, current_timestamp
from user_manager import (
    login, logout, change_own_password,
    user_management_menu, ROLE_ADMIN,
)
from student_manager import student_management_menu
from course_manager import course_management_menu
from teacher_manager import teacher_management_menu
from grade_manager import grade_management_menu


SYSTEM_NAME = "简单的信息管理系统"
VERSION = "2.0.0"


def print_welcome():
    """显示欢迎界面"""
    print_separator("=", 60)
    print(SYSTEM_NAME.center(60))
    print(f"版本 {VERSION}".center(60))
    print_separator("=", 60)
    print()


def show_system_info(current_user):
    """显示系统信息"""
    from config import DB_CONFIG
    print_title("系统信息")
    print(f"  系统名称    : {SYSTEM_NAME}")
    print(f"  版本号      : {VERSION}")
    print(f"  当前用户    : {current_user['name']}（{current_user['username']}）")
    print(f"  用户角色    : {current_user['role']}")
    print(f"  当前时间    : {current_timestamp()}")
    print_separator("-", 50)
    print(f"  数据库主机  : {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  数据库名称  : {DB_CONFIG['database']}")
    print("  数据表：")
    print("    - users     系统用户")
    print("    - students  学生信息")
    print("    - courses   课程信息")
    print("    - teachers  教师信息")
    print("    - grades    学生成绩")
    pause()


def quick_overview(current_user):
    """快速查看各模块数据量（直接查询 MySQL）"""
    from db import execute_query
    print_title("数据概览")
    modules = [
        ("students", "学生"),
        ("courses",  "课程"),
        ("teachers", "教师"),
        ("grades",   "成绩记录"),
        ("users",    "用户"),
    ]
    for table, label in modules:
        count = execute_query(
            f"SELECT COUNT(*) AS cnt FROM {table}",  # noqa: S608
            fetchone=True,
        )["cnt"]
        print(f"  {label:<12}: {count} 条")
    pause()


def main_menu(current_user):
    """主菜单"""
    while True:
        print_welcome()
        options = [
            ("1", "学生管理"),
            ("2", "课程管理"),
            ("3", "教师管理"),
            ("4", "成绩管理"),
        ]
        if current_user["role"] == ROLE_ADMIN:
            options.append(("5", "用户管理"))
        options += [
            ("6", "修改我的密码"),
            ("7", "数据概览"),
            ("8", "系统信息"),
            ("0", "退出系统"),
        ]
        print_menu(f"主菜单  [当前用户：{current_user['name']}]", options)
        choice = input("  请选择操作: ").strip()

        if choice == "1":
            student_management_menu(current_user)
        elif choice == "2":
            course_management_menu(current_user)
        elif choice == "3":
            teacher_management_menu(current_user)
        elif choice == "4":
            grade_management_menu(current_user)
        elif choice == "5" and current_user["role"] == ROLE_ADMIN:
            user_management_menu(current_user)
        elif choice == "6":
            change_own_password(current_user)
        elif choice == "7":
            quick_overview(current_user)
        elif choice == "8":
            show_system_info(current_user)
        elif choice == "0":
            logout(current_user)
            break
        else:
            print("  [提示] 无效选项，请重新输入。")


def main():
    """程序入口"""
    print_welcome()
    # 初始化数据库表结构
    try:
        init_db()
    except Exception as exc:
        print(f"\n  [错误] 无法连接数据库：{exc}")
        print("  请检查 config.py 中的数据库配置后重试。")
        sys.exit(1)
    current_user = login()
    if current_user is None:
        sys.exit(1)
    main_menu(current_user)
    print("\n  感谢使用，再见！")


if __name__ == "__main__":
    main()
