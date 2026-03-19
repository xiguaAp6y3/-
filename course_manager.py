# -*- coding: utf-8 -*-
"""
课程管理模块 - 提供课程信息的增、删、改、查
"""

from utils import (
    load_json, save_json, print_title, print_menu, print_separator,
    input_required, input_int, input_float, input_yes_no, input_choice,
    current_timestamp, pause, generate_id
)

COURSES_FILE = "courses.json"

COURSE_TYPE_REQUIRED = "必修"
COURSE_TYPE_ELECTIVE = "选修"
COURSE_TYPE_GENERAL = "公共基础"

COURSE_TYPES = {COURSE_TYPE_REQUIRED, COURSE_TYPE_ELECTIVE, COURSE_TYPE_GENERAL}


def _load_courses():
    return load_json(COURSES_FILE)


def _save_courses(courses):
    save_json(COURSES_FILE, courses)


def _print_course(course):
    """格式化打印单门课程"""
    print(f"  课程编号    : {course['course_id']}")
    print(f"  课程名称    : {course['name']}")
    print(f"  课程类型    : {course['course_type']}")
    print(f"  学分        : {course['credits']}")
    print(f"  学时        : {course['hours']}")
    print(f"  开课学期    : {course['semester']}")
    print(f"  授课教师    : {course['teacher_name']}")
    print(f"  课程描述    : {course.get('description', '')}")
    print(f"  录入时间    : {course['created_at']}")


def _print_course_row(course):
    print(
        f"  {course['course_id']:<10} "
        f"{course['name']:<18} "
        f"{course['course_type']:<8} "
        f"{course['credits']:<5} "
        f"{course['hours']:<6} "
        f"{course['semester']:<12} "
        f"{course['teacher_name']}"
    )


def _print_list_header():
    print(
        f"  {'课程编号':<10} "
        f"{'课程名称':<18} "
        f"{'类型':<8} "
        f"{'学分':<5} "
        f"{'学时':<6} "
        f"{'开课学期':<12} "
        f"{'授课教师'}"
    )
    print_separator("-", 78)


# ─── 增 ──────────────────────────────────────────────────────

def add_course(current_user):
    """添加课程"""
    print_title("添加课程")
    courses = _load_courses()
    existing_ids = {c["course_id"] for c in courses}

    name = input_required("  课程名称: ")
    if any(c["name"] == name for c in courses):
        print("  [错误] 该课程名称已存在。")
        pause()
        return

    course_type = input_choice(
        f"  课程类型 ({'/'.join(COURSE_TYPES)}): ",
        COURSE_TYPES,
    )
    credits = input_float("  学分（如 3.0）: ", min_val=0.5, max_val=20.0)
    hours = input_int("  学时: ", min_val=8, max_val=256)
    semester = input_required("  开课学期（如 2023-2024-1）: ")
    teacher_name = input_required("  授课教师姓名: ")
    description = input("  课程描述（可选）: ").strip()

    new_course = {
        "course_id": generate_id("C", existing_ids),
        "name": name,
        "course_type": course_type,
        "credits": credits,
        "hours": hours,
        "semester": semester,
        "teacher_name": teacher_name,
        "description": description,
        "created_at": current_timestamp(),
        "updated_at": current_timestamp(),
    }
    courses.append(new_course)
    _save_courses(courses)
    print(f"  [成功] 课程 '{name}' 已添加，课程编号：{new_course['course_id']}")
    pause()


# ─── 查 ──────────────────────────────────────────────────────

def list_courses(current_user):
    """列出所有课程"""
    courses = _load_courses()
    print_title("课程列表")
    if not courses:
        print("  暂无课程数据。")
        pause()
        return
    print(f"  共 {len(courses)} 门课程：\n")
    _print_list_header()
    for c in courses:
        _print_course_row(c)
    pause()


def search_course(current_user):
    """查询课程"""
    print_title("查询课程")
    print("  查询方式：")
    print("  1. 按课程编号查询")
    print("  2. 按课程名称查询（模糊匹配）")
    print("  3. 按授课教师查询")
    print("  4. 按课程类型查询")
    print("  5. 按学期查询")
    print_separator("-", 60)
    choice = input_choice("  请选择查询方式: ", {"1", "2", "3", "4", "5"})

    courses = _load_courses()

    if choice == "1":
        cid = input_required("  请输入课程编号: ")
        results = [c for c in courses if c["course_id"] == cid]
    elif choice == "2":
        keyword = input_required("  请输入课程名称关键词: ")
        results = [c for c in courses if keyword in c["name"]]
    elif choice == "3":
        teacher = input_required("  请输入教师姓名: ")
        results = [c for c in courses if teacher in c["teacher_name"]]
    elif choice == "4":
        ctype = input_choice(
            f"  请输入课程类型 ({'/'.join(COURSE_TYPES)}): ",
            COURSE_TYPES,
        )
        results = [c for c in courses if c["course_type"] == ctype]
    else:
        semester = input_required("  请输入学期（如 2023-2024-1）: ")
        results = [c for c in courses if c["semester"] == semester]

    if not results:
        print("  未找到匹配的课程。")
    else:
        print(f"  找到 {len(results)} 条记录：\n")
        _print_list_header()
        for c in results:
            _print_course_row(c)
    pause()


def view_course_detail(current_user):
    """查看课程详情"""
    print_title("课程详情")
    cid = input_required("  请输入课程编号: ")
    courses = _load_courses()
    course = next((c for c in courses if c["course_id"] == cid), None)
    if not course:
        print("  [错误] 未找到该课程。")
    else:
        print_separator("-", 50)
        _print_course(course)
        print_separator("-", 50)
    pause()


# ─── 改 ──────────────────────────────────────────────────────

def update_course(current_user):
    """修改课程信息"""
    print_title("修改课程信息")
    cid = input_required("  请输入要修改的课程编号: ")
    courses = _load_courses()
    course = next((c for c in courses if c["course_id"] == cid), None)
    if not course:
        print("  [错误] 未找到该课程。")
        pause()
        return

    print("\n  当前信息：")
    _print_course(course)
    print("\n  请输入新信息（留空则保持原值不变）：\n")

    name = input(f"  课程名称 [{course['name']}]: ").strip()
    if name:
        course["name"] = name

    ct_input = input(
        f"  课程类型 [{course['course_type']}] ({'/'.join(COURSE_TYPES)}，留空不变): "
    ).strip()
    if ct_input in COURSE_TYPES:
        course["course_type"] = ct_input

    credits_input = input(f"  学分 [{course['credits']}]: ").strip()
    if credits_input:
        try:
            credits_val = float(credits_input)
            if 0.5 <= credits_val <= 20.0:
                course["credits"] = credits_val
            else:
                print("  [提示] 学分超出范围（0.5~20.0），保持原值。")
        except ValueError:
            print("  [提示] 学分格式不正确，保持原值。")

    hours_input = input(f"  学时 [{course['hours']}]: ").strip()
    if hours_input:
        try:
            hours_val = int(hours_input)
            if 8 <= hours_val <= 256:
                course["hours"] = hours_val
            else:
                print("  [提示] 学时超出范围（8~256），保持原值。")
        except ValueError:
            print("  [提示] 学时格式不正确，保持原值。")

    semester = input(f"  开课学期 [{course['semester']}]: ").strip()
    if semester:
        course["semester"] = semester

    teacher_name = input(f"  授课教师 [{course['teacher_name']}]: ").strip()
    if teacher_name:
        course["teacher_name"] = teacher_name

    description = input(f"  课程描述 [{course.get('description', '')}]: ").strip()
    if description:
        course["description"] = description

    course["updated_at"] = current_timestamp()
    _save_courses(courses)
    print("  [成功] 课程信息已更新。")
    pause()


# ─── 删 ──────────────────────────────────────────────────────

def delete_course(current_user):
    """删除课程"""
    print_title("删除课程")
    cid = input_required("  请输入要删除的课程编号: ")
    courses = _load_courses()
    course = next((c for c in courses if c["course_id"] == cid), None)
    if not course:
        print("  [错误] 未找到该课程。")
        pause()
        return

    print(f"\n  即将删除课程：{course['name']}（{course['course_id']}）")
    confirm = input_yes_no("  确认删除？")
    if confirm:
        courses.remove(course)
        _save_courses(courses)
        print("  [成功] 课程已删除。")
    else:
        print("  操作已取消。")
    pause()


# ─── 统计 ─────────────────────────────────────────────────────

def course_statistics(current_user):
    """课程统计"""
    courses = _load_courses()
    print_title("课程统计信息")
    if not courses:
        print("  暂无课程数据。")
        pause()
        return

    total = len(courses)
    total_credits = sum(c["credits"] for c in courses)
    total_hours = sum(c["hours"] for c in courses)

    type_counter = {}
    for c in courses:
        type_counter[c["course_type"]] = type_counter.get(c["course_type"], 0) + 1

    semester_counter = {}
    for c in courses:
        semester_counter[c["semester"]] = semester_counter.get(c["semester"], 0) + 1

    print(f"  课程总数    : {total}")
    print(f"  总学分      : {total_credits}")
    print(f"  总学时      : {total_hours}")
    print()
    print("  各类型课程数量：")
    for ctype, cnt in sorted(type_counter.items()):
        print(f"    {ctype}: {cnt} 门")
    print()
    print("  各学期课程数量：")
    for sem, cnt in sorted(semester_counter.items()):
        print(f"    {sem}: {cnt} 门")
    pause()


def batch_import_courses(current_user):
    """批量导入示例课程数据"""
    print_title("批量导入示例课程数据")
    courses = _load_courses()
    existing_ids = {c["course_id"] for c in courses}
    existing_names = {c["name"] for c in courses}

    sample_data = [
        ("高等数学", COURSE_TYPE_REQUIRED, 4.0, 64, "2023-2024-1", "张老师", "微积分、线代等基础数学课程"),
        ("大学英语", COURSE_TYPE_REQUIRED, 3.0, 48, "2023-2024-1", "李老师", "大学英语听说读写"),
        ("Python程序设计", COURSE_TYPE_REQUIRED, 3.0, 48, "2023-2024-1", "王老师", "Python基础编程"),
        ("数据结构", COURSE_TYPE_REQUIRED, 3.5, 56, "2023-2024-2", "刘老师", "基本数据结构与算法"),
        ("操作系统", COURSE_TYPE_REQUIRED, 3.0, 48, "2023-2024-2", "陈老师", "操作系统原理"),
        ("计算机网络", COURSE_TYPE_REQUIRED, 3.0, 48, "2024-2025-1", "赵老师", "TCP/IP等网络基础"),
        ("数据库原理", COURSE_TYPE_REQUIRED, 3.0, 48, "2024-2025-1", "孙老师", "关系型数据库理论与应用"),
        ("人工智能导论", COURSE_TYPE_ELECTIVE, 2.0, 32, "2024-2025-1", "周老师", "AI基本概念与应用"),
        ("软件工程", COURSE_TYPE_REQUIRED, 3.0, 48, "2024-2025-2", "吴老师", "软件开发生命周期管理"),
        ("体育", COURSE_TYPE_GENERAL, 1.0, 32, "2023-2024-1", "郑老师", "体能训练与运动技能"),
    ]

    added = 0
    for name, ctype, credits, hours, semester, teacher, desc in sample_data:
        if name in existing_names:
            continue
        new_course = {
            "course_id": generate_id("C", existing_ids),
            "name": name,
            "course_type": ctype,
            "credits": credits,
            "hours": hours,
            "semester": semester,
            "teacher_name": teacher,
            "description": desc,
            "created_at": current_timestamp(),
            "updated_at": current_timestamp(),
        }
        courses.append(new_course)
        existing_ids.add(new_course["course_id"])
        existing_names.add(name)
        added += 1

    _save_courses(courses)
    print(f"  [成功] 成功导入 {added} 门课程数据。")
    pause()


# ─── 菜单 ─────────────────────────────────────────────────────

def course_management_menu(current_user):
    """课程管理子菜单"""
    while True:
        print_menu(
            "课程管理",
            [
                ("1", "添加课程"),
                ("2", "课程列表"),
                ("3", "查询课程"),
                ("4", "查看课程详情"),
                ("5", "修改课程信息"),
                ("6", "删除课程"),
                ("7", "课程统计"),
                ("8", "批量导入示例数据"),
                ("0", "返回上级菜单"),
            ],
        )
        choice = input("  请选择操作: ").strip()
        if choice == "1":
            add_course(current_user)
        elif choice == "2":
            list_courses(current_user)
        elif choice == "3":
            search_course(current_user)
        elif choice == "4":
            view_course_detail(current_user)
        elif choice == "5":
            update_course(current_user)
        elif choice == "6":
            delete_course(current_user)
        elif choice == "7":
            course_statistics(current_user)
        elif choice == "8":
            batch_import_courses(current_user)
        elif choice == "0":
            break
        else:
            print("  [提示] 无效选项，请重新输入。")
