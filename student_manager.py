# -*- coding: utf-8 -*-
"""
学生管理模块 - 提供学生信息的增、删、改、查
"""

from utils import (
    load_json, save_json, print_title, print_menu, print_separator,
    input_required, input_int, input_yes_no, input_choice,
    validate_phone, validate_id_number, current_timestamp,
    pause, generate_id
)

STUDENTS_FILE = "students.json"

GENDER_MALE = "男"
GENDER_FEMALE = "女"


def _load_students():
    return load_json(STUDENTS_FILE)


def _save_students(students):
    save_json(STUDENTS_FILE, students)


def _print_student(student):
    """格式化打印单个学生信息"""
    print(f"  学号        : {student['student_id']}")
    print(f"  姓名        : {student['name']}")
    print(f"  性别        : {student['gender']}")
    print(f"  年龄        : {student['age']}")
    print(f"  班级        : {student['class_name']}")
    print(f"  专业        : {student['major']}")
    print(f"  手机号      : {student['phone']}")
    print(f"  身份证号    : {student['id_number']}")
    print(f"  邮箱        : {student['email']}")
    print(f"  入学时间    : {student['enrollment_date']}")
    print(f"  备注        : {student.get('remark', '')}")
    print(f"  录入时间    : {student['created_at']}")


def _print_student_row(student):
    """打印学生列表中的一行"""
    print(
        f"  {student['student_id']:<10} "
        f"{student['name']:<10} "
        f"{student['gender']:<4} "
        f"{student['age']:<5} "
        f"{student['class_name']:<12} "
        f"{student['major']:<14} "
        f"{student['phone']}"
    )


def _print_list_header():
    """打印学生列表表头"""
    print(
        f"  {'学号':<10} "
        f"{'姓名':<10} "
        f"{'性别':<4} "
        f"{'年龄':<5} "
        f"{'班级':<12} "
        f"{'专业':<14} "
        f"{'手机号'}"
    )
    print_separator("-", 75)


# ─── 增 ──────────────────────────────────────────────────────

def add_student(current_user):
    """添加学生"""
    print_title("添加学生")
    students = _load_students()
    existing_ids = {s["student_id"] for s in students}

    # 基本信息
    name = input_required("  姓名: ")
    gender = input_choice("  性别 (男/女): ", {GENDER_MALE, GENDER_FEMALE})
    age = input_int("  年龄: ", min_val=1, max_val=100)
    class_name = input_required("  班级: ")
    major = input_required("  专业: ")

    # 联系信息
    while True:
        phone = input_required("  手机号: ")
        if validate_phone(phone):
            break
        print("  [提示] 手机号格式不正确（需为11位数字且以1开头），请重新输入。")

    while True:
        id_number = input_required("  身份证号: ")
        if validate_id_number(id_number):
            break
        print("  [提示] 身份证号格式不正确（需为18位），请重新输入。")

    # 检查身份证号唯一性
    if any(s["id_number"] == id_number for s in students):
        print("  [错误] 该身份证号已存在，学生可能已被录入。")
        pause()
        return

    email = input("  邮箱（可选）: ").strip()
    enrollment_date = input("  入学日期（如 2023-09-01，可选）: ").strip()
    remark = input("  备注（可选）: ").strip()

    new_student = {
        "student_id": generate_id("S", existing_ids),
        "name": name,
        "gender": gender,
        "age": age,
        "class_name": class_name,
        "major": major,
        "phone": phone,
        "id_number": id_number,
        "email": email,
        "enrollment_date": enrollment_date,
        "remark": remark,
        "created_at": current_timestamp(),
        "updated_at": current_timestamp(),
    }
    students.append(new_student)
    _save_students(students)
    print(f"  [成功] 学生 '{name}' 已添加，学号：{new_student['student_id']}")
    pause()


# ─── 查 ──────────────────────────────────────────────────────

def list_students(current_user):
    """列出所有学生"""
    students = _load_students()
    print_title("学生列表")
    if not students:
        print("  暂无学生数据。")
        pause()
        return
    print(f"  共 {len(students)} 名学生：\n")
    _print_list_header()
    for s in students:
        _print_student_row(s)
    pause()


def search_student(current_user):
    """查询学生"""
    print_title("查询学生")
    print("  查询方式：")
    print("  1. 按学号查询")
    print("  2. 按姓名查询（支持模糊匹配）")
    print("  3. 按班级查询")
    print("  4. 按专业查询")
    print_separator("-", 60)
    choice = input_choice("  请选择查询方式: ", {"1", "2", "3", "4"})

    students = _load_students()

    if choice == "1":
        sid = input_required("  请输入学号: ")
        results = [s for s in students if s["student_id"] == sid]
    elif choice == "2":
        keyword = input_required("  请输入姓名关键词: ")
        results = [s for s in students if keyword in s["name"]]
    elif choice == "3":
        class_name = input_required("  请输入班级名称: ")
        results = [s for s in students if s["class_name"] == class_name]
    else:
        major = input_required("  请输入专业名称: ")
        results = [s for s in students if s["major"] == major]

    if not results:
        print("  未找到匹配的学生。")
    else:
        print(f"  找到 {len(results)} 条记录：\n")
        _print_list_header()
        for s in results:
            _print_student_row(s)
    pause()


def view_student_detail(current_user):
    """查看学生详情"""
    print_title("学生详情")
    sid = input_required("  请输入学号: ")
    students = _load_students()
    student = next((s for s in students if s["student_id"] == sid), None)
    if not student:
        print("  [错误] 未找到该学生。")
    else:
        print_separator("-", 50)
        _print_student(student)
        print_separator("-", 50)
    pause()


# ─── 改 ──────────────────────────────────────────────────────

def update_student(current_user):
    """修改学生信息"""
    print_title("修改学生信息")
    sid = input_required("  请输入要修改的学生学号: ")
    students = _load_students()
    student = next((s for s in students if s["student_id"] == sid), None)
    if not student:
        print("  [错误] 未找到该学生。")
        pause()
        return

    print("\n  当前信息：")
    _print_student(student)
    print("\n  请输入新信息（留空则保持原值不变）：\n")

    name = input(f"  姓名 [{student['name']}]: ").strip()
    if name:
        student["name"] = name

    gender_input = input(f"  性别 [{student['gender']}] (男/女，留空不变): ").strip()
    if gender_input in (GENDER_MALE, GENDER_FEMALE):
        student["gender"] = gender_input

    age_input = input(f"  年龄 [{student['age']}]: ").strip()
    if age_input:
        try:
            age_val = int(age_input)
            if 1 <= age_val <= 100:
                student["age"] = age_val
            else:
                print("  [提示] 年龄超出范围，保持原值。")
        except ValueError:
            print("  [提示] 年龄格式不正确，保持原值。")

    class_name = input(f"  班级 [{student['class_name']}]: ").strip()
    if class_name:
        student["class_name"] = class_name

    major = input(f"  专业 [{student['major']}]: ").strip()
    if major:
        student["major"] = major

    phone_input = input(f"  手机号 [{student['phone']}]: ").strip()
    if phone_input:
        if validate_phone(phone_input):
            student["phone"] = phone_input
        else:
            print("  [提示] 手机号格式不正确，保持原值。")

    email_input = input(f"  邮箱 [{student['email']}]: ").strip()
    if email_input:
        student["email"] = email_input

    remark_input = input(f"  备注 [{student.get('remark', '')}]: ").strip()
    if remark_input:
        student["remark"] = remark_input

    student["updated_at"] = current_timestamp()
    _save_students(students)
    print("  [成功] 学生信息已更新。")
    pause()


# ─── 删 ──────────────────────────────────────────────────────

def delete_student(current_user):
    """删除学生"""
    print_title("删除学生")
    sid = input_required("  请输入要删除的学生学号: ")
    students = _load_students()
    student = next((s for s in students if s["student_id"] == sid), None)
    if not student:
        print("  [错误] 未找到该学生。")
        pause()
        return

    print(f"\n  即将删除学生：{student['name']}（{student['student_id']}，{student['class_name']}）")
    confirm = input_yes_no("  确认删除？")
    if confirm:
        students.remove(student)
        _save_students(students)
        print("  [成功] 学生已删除。")
    else:
        print("  操作已取消。")
    pause()


# ─── 统计 ─────────────────────────────────────────────────────

def student_statistics(current_user):
    """学生信息统计"""
    students = _load_students()
    print_title("学生统计信息")
    if not students:
        print("  暂无学生数据。")
        pause()
        return

    total = len(students)
    male_count = sum(1 for s in students if s["gender"] == GENDER_MALE)
    female_count = total - male_count

    # 按班级统计
    class_counter = {}
    for s in students:
        class_counter[s["class_name"]] = class_counter.get(s["class_name"], 0) + 1

    # 按专业统计
    major_counter = {}
    for s in students:
        major_counter[s["major"]] = major_counter.get(s["major"], 0) + 1

    # 平均年龄
    avg_age = sum(s["age"] for s in students) / total if total > 0 else 0

    print(f"  学生总数    : {total}")
    print(f"  男生人数    : {male_count}")
    print(f"  女生人数    : {female_count}")
    print(f"  平均年龄    : {avg_age:.1f} 岁")
    print()
    print("  各班级人数：")
    for cls, cnt in sorted(class_counter.items()):
        print(f"    {cls}: {cnt} 人")
    print()
    print("  各专业人数：")
    for major, cnt in sorted(major_counter.items()):
        print(f"    {major}: {cnt} 人")
    pause()


def batch_import_students(current_user):
    """
    批量导入学生（从内置示例数据，用于演示）
    实际项目中可从 CSV 文件读取
    """
    print_title("批量导入示例学生数据")
    students = _load_students()
    existing_ids = {s["student_id"] for s in students}
    existing_id_numbers = {s["id_number"] for s in students}

    sample_data = [
        ("张伟", "男", 20, "计科2101", "计算机科学与技术", "13800010001", "110101200300010001"),
        ("李娜", "女", 19, "计科2101", "计算机科学与技术", "13800010002", "110101200400020002"),
        ("王芳", "女", 21, "软工2102", "软件工程", "13800010003", "110101200200030003"),
        ("刘洋", "男", 20, "软工2102", "软件工程", "13800010004", "110101200300040004"),
        ("陈静", "女", 22, "网络2103", "网络工程", "13800010005", "110101200100050005"),
        ("赵磊", "男", 19, "网络2103", "网络工程", "13800010006", "110101200400060006"),
        ("孙丽", "女", 20, "数据2104", "数据科学与大数据技术", "13800010007", "110101200300070007"),
        ("周杰", "男", 21, "数据2104", "数据科学与大数据技术", "13800010008", "110101200200080008"),
        ("吴敏", "女", 20, "计科2101", "计算机科学与技术", "13800010009", "110101200300090009"),
        ("郑强", "男", 22, "软工2102", "软件工程", "13800010010", "110101200100100010"),
    ]

    added = 0
    for name, gender, age, cls, major, phone, id_num in sample_data:
        if id_num in existing_id_numbers:
            continue
        new_student = {
            "student_id": generate_id("S", existing_ids),
            "name": name,
            "gender": gender,
            "age": age,
            "class_name": cls,
            "major": major,
            "phone": phone,
            "id_number": id_num,
            "email": f"{phone}@example.com",
            "enrollment_date": "2021-09-01",
            "remark": "",
            "created_at": current_timestamp(),
            "updated_at": current_timestamp(),
        }
        students.append(new_student)
        existing_ids.add(new_student["student_id"])
        existing_id_numbers.add(id_num)
        added += 1

    _save_students(students)
    print(f"  [成功] 成功导入 {added} 条学生数据。")
    pause()


# ─── 菜单 ─────────────────────────────────────────────────────

def student_management_menu(current_user):
    """学生管理子菜单"""
    while True:
        print_menu(
            "学生管理",
            [
                ("1", "添加学生"),
                ("2", "学生列表"),
                ("3", "查询学生"),
                ("4", "查看学生详情"),
                ("5", "修改学生信息"),
                ("6", "删除学生"),
                ("7", "学生统计"),
                ("8", "批量导入示例数据"),
                ("0", "返回上级菜单"),
            ],
        )
        choice = input("  请选择操作: ").strip()
        if choice == "1":
            add_student(current_user)
        elif choice == "2":
            list_students(current_user)
        elif choice == "3":
            search_student(current_user)
        elif choice == "4":
            view_student_detail(current_user)
        elif choice == "5":
            update_student(current_user)
        elif choice == "6":
            delete_student(current_user)
        elif choice == "7":
            student_statistics(current_user)
        elif choice == "8":
            batch_import_students(current_user)
        elif choice == "0":
            break
        else:
            print("  [提示] 无效选项，请重新输入。")
