# -*- coding: utf-8 -*-
"""
工具模块 - 提供通用工具函数（输入、显示、校验等）
数据存储已迁移至 MySQL，详见 db.py
"""

import os
import re
from datetime import datetime


def print_separator(char="=", width=60):
    """打印分隔线"""
    print(char * width)


def print_title(title, char="=", width=60):
    """打印标题"""
    print_separator(char, width)
    print(title.center(width))
    print_separator(char, width)


def print_menu(title, options):
    """
    打印菜单

    :param title: 菜单标题
    :param options: 选项列表，每个元素为 (编号, 描述) 元组
    """
    print_title(title)
    for key, desc in options:
        print(f"  {key}. {desc}")
    print_separator("-", 60)


def input_required(prompt):
    """要求必填的输入，不允许为空"""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  [提示] 该项不能为空，请重新输入。")


def input_optional(prompt, default=""):
    """可选输入，为空时使用默认值"""
    value = input(prompt).strip()
    return value if value else default


def input_int(prompt, min_val=None, max_val=None):
    """
    输入整数，可指定范围

    :param prompt: 提示信息
    :param min_val: 最小值（包含）
    :param max_val: 最大值（包含）
    :return: 整数
    """
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print("  [提示] 请输入有效的整数。")
            continue
        if min_val is not None and value < min_val:
            print(f"  [提示] 输入值不能小于 {min_val}。")
            continue
        if max_val is not None and value > max_val:
            print(f"  [提示] 输入值不能大于 {max_val}。")
            continue
        return value


def input_float(prompt, min_val=None, max_val=None):
    """
    输入浮点数，可指定范围

    :param prompt: 提示信息
    :param min_val: 最小值（包含）
    :param max_val: 最大值（包含）
    :return: 浮点数
    """
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            print("  [提示] 请输入有效的数字。")
            continue
        if min_val is not None and value < min_val:
            print(f"  [提示] 输入值不能小于 {min_val}。")
            continue
        if max_val is not None and value > max_val:
            print(f"  [提示] 输入值不能大于 {max_val}。")
            continue
        return value


def input_choice(prompt, valid_choices):
    """
    从给定选项中选择

    :param prompt: 提示信息
    :param valid_choices: 合法选项的集合或列表
    :return: 用户输入的合法选项
    """
    while True:
        choice = input(prompt).strip()
        if choice in valid_choices:
            return choice
        print(f"  [提示] 请输入有效的选项：{', '.join(str(c) for c in valid_choices)}")


def input_yes_no(prompt):
    """
    输入 Y/N 确认

    :param prompt: 提示信息
    :return: True 表示确认，False 表示取消
    """
    choice = input_choice(f"{prompt} (Y/N): ", {"Y", "y", "N", "n"})
    return choice in ("Y", "y")


def validate_phone(phone):
    """验证手机号格式（11位数字，以1开头）"""
    pattern = re.compile(r"^1\d{10}$")
    return bool(pattern.match(phone))


def validate_email(email):
    """验证邮箱格式"""
    pattern = re.compile(r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$")
    return bool(pattern.match(email))


def validate_id_number(id_num):
    """简单验证身份证号（18位数字或末位X）"""
    pattern = re.compile(r"^\d{17}[\dXx]$")
    return bool(pattern.match(id_num))


def current_timestamp():
    """返回当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def current_date():
    """返回当前日期字符串"""
    return datetime.now().strftime("%Y-%m-%d")


def pause():
    """暂停，等待用户按键继续"""
    input("\n  按 Enter 键继续...")


def clear_screen():
    """清屏"""
    os.system("cls" if os.name == "nt" else "clear")


def format_table(headers, rows, col_widths=None):
    """
    格式化为表格字符串

    :param headers: 表头列表
    :param rows: 行数据，每行为列表
    :param col_widths: 每列宽度，默认自动计算
    :return: 表格字符串
    """
    if not col_widths:
        col_widths = []
        for i, h in enumerate(headers):
            max_w = _display_len(h)
            for row in rows:
                cell = str(row[i]) if i < len(row) else ""
                max_w = max(max_w, _display_len(cell))
            col_widths.append(max_w + 2)

    def make_row(cells):
        parts = []
        for cell, w in zip(cells, col_widths):
            cell_str = str(cell)
            parts.append(cell_str + " " * max(0, w - _display_len(cell_str)))
        return "| " + " | ".join(parts) + " |"

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    lines = [sep, make_row(headers), sep]
    for row in rows:
        lines.append(make_row(row))
    lines.append(sep)
    return "\n".join(lines)


def _display_len(s):
    """计算字符串的显示宽度（中文字符占2个宽度）"""
    width = 0
    for ch in str(s):
        if "\u4e00" <= ch <= "\u9fff" or "\u3000" <= ch <= "\u303f":
            width += 2
        else:
            width += 1
    return width



