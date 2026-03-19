# -*- coding: utf-8 -*-
"""
用户管理模块 - 提供用户注册、登录、修改密码等功能
"""

import hashlib
from utils import (
    load_json, save_json, print_title, print_menu, print_separator,
    input_required, input_choice, input_yes_no, current_timestamp,
    pause, generate_id
)

USERS_FILE = "users.json"

# 角色定义
ROLE_ADMIN = "admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"

ROLE_LABELS = {
    ROLE_ADMIN: "管理员",
    ROLE_TEACHER: "教师",
    ROLE_STUDENT: "学生",
}


def _hash_password(password):
    """对密码进行 SHA-256 哈希处理"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load_users():
    return load_json(USERS_FILE)


def _save_users(users):
    save_json(USERS_FILE, users)


def _init_default_admin():
    """若没有任何用户则创建默认管理员账号"""
    users = _load_users()
    if not users:
        admin = {
            "user_id": "U0001",
            "username": "admin",
            "password": _hash_password("admin123"),
            "role": ROLE_ADMIN,
            "name": "系统管理员",
            "created_at": current_timestamp(),
        }
        _save_users([admin])
        print("  [系统] 已创建默认管理员账号：用户名 admin，密码 admin123")


def login():
    """
    用户登录

    :return: 登录成功返回用户字典，失败返回 None
    """
    _init_default_admin()
    print_title("用户登录")
    for _ in range(3):
        username = input("  用户名: ").strip()
        password = input("  密  码: ").strip()
        users = _load_users()
        hashed = _hash_password(password)
        for user in users:
            if user["username"] == username and user["password"] == hashed:
                print(f"\n  登录成功！欢迎您，{user['name']}（{ROLE_LABELS.get(user['role'], user['role'])}）")
                pause()
                return user
        print("  [错误] 用户名或密码不正确，请重试。\n")
    print("  [错误] 登录失败次数过多，程序退出。")
    return None


def logout(current_user):
    """退出登录"""
    print(f"\n  再见，{current_user['name']}！")
    pause()


# ─── 用户 CRUD ────────────────────────────────────────────────

def add_user(current_user):
    """添加新用户（仅管理员可操作）"""
    if current_user["role"] != ROLE_ADMIN:
        print("  [错误] 无权限执行此操作。")
        pause()
        return
    print_title("添加用户")
    users = _load_users()
    existing_ids = {u["user_id"] for u in users}
    existing_usernames = {u["username"] for u in users}

    username = input_required("  用户名: ")
    if username in existing_usernames:
        print("  [错误] 用户名已存在。")
        pause()
        return

    password = input_required("  密  码: ")
    name = input_required("  姓  名: ")
    role = input_choice(
        "  角  色 (admin/teacher/student): ",
        {ROLE_ADMIN, ROLE_TEACHER, ROLE_STUDENT}
    )

    new_user = {
        "user_id": generate_id("U", existing_ids),
        "username": username,
        "password": _hash_password(password),
        "role": role,
        "name": name,
        "created_at": current_timestamp(),
    }
    users.append(new_user)
    _save_users(users)
    print(f"  [成功] 用户 '{username}' 已添加，ID：{new_user['user_id']}")
    pause()


def list_users(current_user):
    """列出所有用户（仅管理员可操作）"""
    if current_user["role"] != ROLE_ADMIN:
        print("  [错误] 无权限执行此操作。")
        pause()
        return
    users = _load_users()
    print_title("用户列表")
    if not users:
        print("  暂无用户数据。")
        pause()
        return
    print(f"  {'ID':<8} {'用户名':<16} {'姓名':<12} {'角色':<10} {'创建时间'}")
    print_separator("-", 70)
    for u in users:
        role_label = ROLE_LABELS.get(u["role"], u["role"])
        print(f"  {u['user_id']:<8} {u['username']:<16} {u['name']:<12} {role_label:<10} {u['created_at']}")
    pause()


def update_user(current_user):
    """修改用户信息（管理员可修改任意用户，普通用户只能修改自己）"""
    print_title("修改用户信息")
    users = _load_users()

    if current_user["role"] == ROLE_ADMIN:
        uid = input_required("  请输入要修改的用户ID: ")
        target = next((u for u in users if u["user_id"] == uid), None)
        if not target:
            print("  [错误] 用户不存在。")
            pause()
            return
    else:
        target = next((u for u in users if u["user_id"] == current_user["user_id"]), None)

    print(f"  当前姓名：{target['name']}")
    new_name = input("  新姓名（留空保持不变）: ").strip()
    if new_name:
        target["name"] = new_name

    change_pwd = input_yes_no("  是否修改密码？")
    if change_pwd:
        old_pwd = input_required("  当前密码: ")
        if target["password"] != _hash_password(old_pwd):
            print("  [错误] 当前密码不正确。")
            pause()
            return
        new_pwd = input_required("  新密码: ")
        target["password"] = _hash_password(new_pwd)

    _save_users(users)
    print("  [成功] 用户信息已更新。")
    pause()


def delete_user(current_user):
    """删除用户（仅管理员可操作，且不能删除自己）"""
    if current_user["role"] != ROLE_ADMIN:
        print("  [错误] 无权限执行此操作。")
        pause()
        return
    print_title("删除用户")
    users = _load_users()
    uid = input_required("  请输入要删除的用户ID: ")
    target = next((u for u in users if u["user_id"] == uid), None)
    if not target:
        print("  [错误] 用户不存在。")
        pause()
        return
    if target["user_id"] == current_user["user_id"]:
        print("  [错误] 不能删除当前登录的账号。")
        pause()
        return
    confirm = input_yes_no(f"  确认删除用户 '{target['username']}' ({target['name']})？")
    if confirm:
        users.remove(target)
        _save_users(users)
        print("  [成功] 用户已删除。")
    else:
        print("  操作已取消。")
    pause()


def search_user(current_user):
    """查询用户（仅管理员可操作）"""
    if current_user["role"] != ROLE_ADMIN:
        print("  [错误] 无权限执行此操作。")
        pause()
        return
    print_title("查询用户")
    keyword = input_required("  请输入用户名或姓名关键词: ")
    users = _load_users()
    results = [
        u for u in users
        if keyword in u["username"] or keyword in u["name"]
    ]
    if not results:
        print("  未找到匹配的用户。")
    else:
        print(f"  找到 {len(results)} 条记录：")
        print(f"  {'ID':<8} {'用户名':<16} {'姓名':<12} {'角色':<10} {'创建时间'}")
        print_separator("-", 70)
        for u in results:
            role_label = ROLE_LABELS.get(u["role"], u["role"])
            print(f"  {u['user_id']:<8} {u['username']:<16} {u['name']:<12} {role_label:<10} {u['created_at']}")
    pause()


def change_own_password(current_user):
    """当前用户修改自己的密码"""
    print_title("修改密码")
    users = _load_users()
    target = next((u for u in users if u["user_id"] == current_user["user_id"]), None)
    if not target:
        print("  [错误] 账户数据异常。")
        pause()
        return

    old_pwd = input_required("  当前密码: ")
    if target["password"] != _hash_password(old_pwd):
        print("  [错误] 当前密码不正确。")
        pause()
        return
    new_pwd = input_required("  新密码: ")
    confirm_pwd = input_required("  确认新密码: ")
    if new_pwd != confirm_pwd:
        print("  [错误] 两次输入的密码不一致。")
        pause()
        return
    target["password"] = _hash_password(new_pwd)
    _save_users(users)
    print("  [成功] 密码已修改，请重新登录。")
    pause()


def user_management_menu(current_user):
    """用户管理子菜单"""
    while True:
        print_menu(
            "用户管理",
            [
                ("1", "添加用户"),
                ("2", "用户列表"),
                ("3", "修改用户信息"),
                ("4", "删除用户"),
                ("5", "查询用户"),
                ("0", "返回上级菜单"),
            ],
        )
        choice = input("  请选择操作: ").strip()
        if choice == "1":
            add_user(current_user)
        elif choice == "2":
            list_users(current_user)
        elif choice == "3":
            update_user(current_user)
        elif choice == "4":
            delete_user(current_user)
        elif choice == "5":
            search_user(current_user)
        elif choice == "0":
            break
        else:
            print("  [提示] 无效选项，请重新输入。")
