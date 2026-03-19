# -*- coding: utf-8 -*-
"""
简单的信息管理系统 - 主入口
包含：学生管理、课程管理、教师管理、成绩管理、用户管理

作者：系统默认
版本：1.0.0
"""

import sys

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
VERSION = "1.0.0"


def print_welcome():
    """显示欢迎界面"""
    print_separator("=", 60)
    print(SYSTEM_NAME.center(60))
    print(f"版本 {VERSION}".center(60))
    print_separator("=", 60)
    print()


def show_system_info(current_user):
    """显示系统信息"""
    print_title("系统信息")
    print(f"  系统名称    : {SYSTEM_NAME}")
    print(f"  版本号      : {VERSION}")
    print(f"  当前用户    : {current_user['name']}（{current_user['username']}）")
    print(f"  用户角色    : {current_user['role']}")
    print(f"  当前时间    : {current_timestamp()}")
    print_separator("-", 50)
    print("  数据存储位置: ./data/")
    print("  数据文件：")
    print("    - students.json   学生数据")
    print("    - courses.json    课程数据")
    print("    - teachers.json   教师数据")
    print("    - grades.json     成绩数据")
    print("    - users.json      用户数据")
    pause()


def quick_overview(current_user):
    """快速查看各模块数据量"""
    from utils import load_json
    print_title("数据概览")
    modules = [
        ("students.json", "学生"),
        ("courses.json", "课程"),
        ("teachers.json", "教师"),
        ("grades.json", "成绩记录"),
        ("users.json", "用户"),
    ]
    for filename, label in modules:
        records = load_json(filename)
        print(f"  {label:<12}: {len(records)} 条")
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
    current_user = login()
    if current_user is None:
        sys.exit(1)
    main_menu(current_user)
    print("\n  感谢使用，再见！")


if __name__ == "__main__":
    main()
