# -*- coding: utf-8 -*-
"""
教师管理模块 - 提供教师信息的增、删、改、查
"""

from utils import (
    load_json, save_json, print_title, print_menu, print_separator,
    input_required, input_int, input_yes_no, input_choice,
    validate_phone, validate_email, current_timestamp,
    pause, generate_id
)

TEACHERS_FILE = "teachers.json"

GENDER_MALE = "男"
GENDER_FEMALE = "女"

TITLE_ASSISTANT = "助教"
TITLE_LECTURER = "讲师"
TITLE_ASSOCIATE_PROF = "副教授"
TITLE_PROFESSOR = "教授"

TITLES = {TITLE_ASSISTANT, TITLE_LECTURER, TITLE_ASSOCIATE_PROF, TITLE_PROFESSOR}


def _load_teachers():
    return load_json(TEACHERS_FILE)


def _save_teachers(teachers):
    save_json(TEACHERS_FILE, teachers)


def _print_teacher(teacher):
    """格式化打印单位教师信息"""
    print(f"  教师编号    : {teacher['teacher_id']}")
    print(f"  姓名        : {teacher['name']}")
    print(f"  性别        : {teacher['gender']}")
    print(f"  年龄        : {teacher['age']}")
    print(f"  职称        : {teacher['title']}")
    print(f"  所属院系    : {teacher['department']}")
    print(f"  手机号      : {teacher['phone']}")
    print(f"  邮箱        : {teacher['email']}")
    print(f"  研究方向    : {teacher.get('research', '')}")
    print(f"  备注        : {teacher.get('remark', '')}")
    print(f"  录入时间    : {teacher['created_at']}")


def _print_teacher_row(teacher):
    print(
        f"  {teacher['teacher_id']:<10} "
        f"{teacher['name']:<10} "
        f"{teacher['gender']:<4} "
        f"{teacher['age']:<5} "
        f"{teacher['title']:<8} "
        f"{teacher['department']:<16} "
        f"{teacher['phone']}"
    )


def _print_list_header():
    print(
        f"  {'教师编号':<10} "
        f"{'姓名':<10} "
        f"{'性别':<4} "
        f"{'年龄':<5} "
        f"{'职称':<8} "
        f"{'所属院系':<16} "
        f"{'手机号'}"
    )
    print_separator("-", 75)


# ─── 增 ──────────────────────────────────────────────────────

def add_teacher(current_user):
    """添加教师"""
    print_title("添加教师")
    teachers = _load_teachers()
    existing_ids = {t["teacher_id"] for t in teachers}

    name = input_required("  姓名: ")
    gender = input_choice("  性别 (男/女): ", {GENDER_MALE, GENDER_FEMALE})
    age = input_int("  年龄: ", min_val=22, max_val=80)
    title = input_choice(
        f"  职称 ({'/'.join(sorted(TITLES))}): ",
        TITLES,
    )
    department = input_required("  所属院系: ")

    while True:
        phone = input_required("  手机号: ")
        if validate_phone(phone):
            break
        print("  [提示] 手机号格式不正确，请重新输入。")

    # 检查手机号唯一性
    if any(t["phone"] == phone for t in teachers):
        print("  [错误] 该手机号已存在，教师可能已被录入。")
        pause()
        return

    while True:
        email_input = input("  邮箱（可选，留空跳过）: ").strip()
        if not email_input:
            email = ""
            break
        if validate_email(email_input):
            email = email_input
            break
        print("  [提示] 邮箱格式不正确，请重新输入。")

    research = input("  研究方向（可选）: ").strip()
    remark = input("  备注（可选）: ").strip()

    new_teacher = {
        "teacher_id": generate_id("T", existing_ids),
        "name": name,
        "gender": gender,
        "age": age,
        "title": title,
        "department": department,
        "phone": phone,
        "email": email,
        "research": research,
        "remark": remark,
        "created_at": current_timestamp(),
        "updated_at": current_timestamp(),
    }
    teachers.append(new_teacher)
    _save_teachers(teachers)
    print(f"  [成功] 教师 '{name}' 已添加，教师编号：{new_teacher['teacher_id']}")
    pause()


# ─── 查 ──────────────────────────────────────────────────────

def list_teachers(current_user):
    """列出所有教师"""
    teachers = _load_teachers()
    print_title("教师列表")
    if not teachers:
        print("  暂无教师数据。")
        pause()
        return
    print(f"  共 {len(teachers)} 位教师：\n")
    _print_list_header()
    for t in teachers:
        _print_teacher_row(t)
    pause()


def search_teacher(current_user):
    """查询教师"""
    print_title("查询教师")
    print("  查询方式：")
    print("  1. 按教师编号查询")
    print("  2. 按姓名查询（模糊匹配）")
    print("  3. 按院系查询")
    print("  4. 按职称查询")
    print_separator("-", 60)
    choice = input_choice("  请选择查询方式: ", {"1", "2", "3", "4"})

    teachers = _load_teachers()

    if choice == "1":
        tid = input_required("  请输入教师编号: ")
        results = [t for t in teachers if t["teacher_id"] == tid]
    elif choice == "2":
        keyword = input_required("  请输入姓名关键词: ")
        results = [t for t in teachers if keyword in t["name"]]
    elif choice == "3":
        dept = input_required("  请输入院系名称: ")
        results = [t for t in teachers if dept in t["department"]]
    else:
        title_val = input_choice(
            f"  请输入职称 ({'/'.join(sorted(TITLES))}): ",
            TITLES,
        )
        results = [t for t in teachers if t["title"] == title_val]

    if not results:
        print("  未找到匹配的教师。")
    else:
        print(f"  找到 {len(results)} 条记录：\n")
        _print_list_header()
        for t in results:
            _print_teacher_row(t)
    pause()


def view_teacher_detail(current_user):
    """查看教师详情"""
    print_title("教师详情")
    tid = input_required("  请输入教师编号: ")
    teachers = _load_teachers()
    teacher = next((t for t in teachers if t["teacher_id"] == tid), None)
    if not teacher:
        print("  [错误] 未找到该教师。")
    else:
        print_separator("-", 50)
        _print_teacher(teacher)
        print_separator("-", 50)
    pause()


# ─── 改 ──────────────────────────────────────────────────────

def update_teacher(current_user):
    """修改教师信息"""
    print_title("修改教师信息")
    tid = input_required("  请输入要修改的教师编号: ")
    teachers = _load_teachers()
    teacher = next((t for t in teachers if t["teacher_id"] == tid), None)
    if not teacher:
        print("  [错误] 未找到该教师。")
        pause()
        return

    print("\n  当前信息：")
    _print_teacher(teacher)
    print("\n  请输入新信息（留空则保持原值不变）：\n")

    name = input(f"  姓名 [{teacher['name']}]: ").strip()
    if name:
        teacher["name"] = name

    gender_input = input(f"  性别 [{teacher['gender']}] (男/女，留空不变): ").strip()
    if gender_input in (GENDER_MALE, GENDER_FEMALE):
        teacher["gender"] = gender_input

    age_input = input(f"  年龄 [{teacher['age']}]: ").strip()
    if age_input:
        try:
            age_val = int(age_input)
            if 22 <= age_val <= 80:
                teacher["age"] = age_val
            else:
                print("  [提示] 年龄超出范围，保持原值。")
        except ValueError:
            print("  [提示] 年龄格式不正确，保持原值。")

    title_input = input(f"  职称 [{teacher['title']}] ({'/'.join(sorted(TITLES))}，留空不变): ").strip()
    if title_input in TITLES:
        teacher["title"] = title_input

    dept = input(f"  所属院系 [{teacher['department']}]: ").strip()
    if dept:
        teacher["department"] = dept

    phone_input = input(f"  手机号 [{teacher['phone']}]: ").strip()
    if phone_input:
        if validate_phone(phone_input):
            teacher["phone"] = phone_input
        else:
            print("  [提示] 手机号格式不正确，保持原值。")

    email_input = input(f"  邮箱 [{teacher['email']}]: ").strip()
    if email_input:
        if validate_email(email_input):
            teacher["email"] = email_input
        else:
            print("  [提示] 邮箱格式不正确，保持原值。")

    research_input = input(f"  研究方向 [{teacher.get('research', '')}]: ").strip()
    if research_input:
        teacher["research"] = research_input

    remark_input = input(f"  备注 [{teacher.get('remark', '')}]: ").strip()
    if remark_input:
        teacher["remark"] = remark_input

    teacher["updated_at"] = current_timestamp()
    _save_teachers(teachers)
    print("  [成功] 教师信息已更新。")
    pause()


# ─── 删 ──────────────────────────────────────────────────────

def delete_teacher(current_user):
    """删除教师"""
    print_title("删除教师")
    tid = input_required("  请输入要删除的教师编号: ")
    teachers = _load_teachers()
    teacher = next((t for t in teachers if t["teacher_id"] == tid), None)
    if not teacher:
        print("  [错误] 未找到该教师。")
        pause()
        return

    print(f"\n  即将删除教师：{teacher['name']}（{teacher['teacher_id']}，{teacher['department']}）")
    confirm = input_yes_no("  确认删除？")
    if confirm:
        teachers.remove(teacher)
        _save_teachers(teachers)
        print("  [成功] 教师已删除。")
    else:
        print("  操作已取消。")
    pause()


# ─── 统计 ─────────────────────────────────────────────────────

def teacher_statistics(current_user):
    """教师统计"""
    teachers = _load_teachers()
    print_title("教师统计信息")
    if not teachers:
        print("  暂无教师数据。")
        pause()
        return

    total = len(teachers)
    male_count = sum(1 for t in teachers if t["gender"] == GENDER_MALE)
    female_count = total - male_count
    avg_age = sum(t["age"] for t in teachers) / total if total > 0 else 0

    title_counter = {}
    for t in teachers:
        title_counter[t["title"]] = title_counter.get(t["title"], 0) + 1

    dept_counter = {}
    for t in teachers:
        dept_counter[t["department"]] = dept_counter.get(t["department"], 0) + 1

    print(f"  教师总数    : {total}")
    print(f"  男教师人数  : {male_count}")
    print(f"  女教师人数  : {female_count}")
    print(f"  平均年龄    : {avg_age:.1f} 岁")
    print()
    print("  各职称人数：")
    for title_val, cnt in sorted(title_counter.items()):
        print(f"    {title_val}: {cnt} 人")
    print()
    print("  各院系人数：")
    for dept, cnt in sorted(dept_counter.items()):
        print(f"    {dept}: {cnt} 人")
    pause()


def batch_import_teachers(current_user):
    """批量导入示例教师数据"""
    print_title("批量导入示例教师数据")
    teachers = _load_teachers()
    existing_ids = {t["teacher_id"] for t in teachers}
    existing_phones = {t["phone"] for t in teachers}

    sample_data = [
        ("张老师", "男", 45, TITLE_PROFESSOR, "计算机学院", "13900010001", "zhangls@university.edu.cn", "机器学习"),
        ("李老师", "女", 38, TITLE_ASSOCIATE_PROF, "外语学院", "13900010002", "lils@university.edu.cn", "语言学"),
        ("王老师", "男", 32, TITLE_LECTURER, "计算机学院", "13900010003", "wangls@university.edu.cn", "Python开发"),
        ("刘老师", "男", 40, TITLE_ASSOCIATE_PROF, "计算机学院", "13900010004", "liuls@university.edu.cn", "算法"),
        ("陈老师", "女", 50, TITLE_PROFESSOR, "计算机学院", "13900010005", "chenls@university.edu.cn", "操作系统"),
        ("赵老师", "男", 35, TITLE_LECTURER, "通信学院", "13900010006", "zhaols@university.edu.cn", "网络协议"),
        ("孙老师", "女", 42, TITLE_ASSOCIATE_PROF, "计算机学院", "13900010007", "sunls@university.edu.cn", "数据库"),
        ("周老师", "男", 48, TITLE_PROFESSOR, "人工智能学院", "13900010008", "zhouls@university.edu.cn", "深度学习"),
        ("吴老师", "女", 37, TITLE_LECTURER, "软件学院", "13900010009", "wuls@university.edu.cn", "软件架构"),
        ("郑老师", "男", 30, TITLE_ASSISTANT, "体育学院", "13900010010", "zhengls@university.edu.cn", "运动训练"),
    ]

    added = 0
    for name, gender, age, title, dept, phone, email, research in sample_data:
        if phone in existing_phones:
            continue
        new_teacher = {
            "teacher_id": generate_id("T", existing_ids),
            "name": name,
            "gender": gender,
            "age": age,
            "title": title,
            "department": dept,
            "phone": phone,
            "email": email,
            "research": research,
            "remark": "",
            "created_at": current_timestamp(),
            "updated_at": current_timestamp(),
        }
        teachers.append(new_teacher)
        existing_ids.add(new_teacher["teacher_id"])
        existing_phones.add(phone)
        added += 1

    _save_teachers(teachers)
    print(f"  [成功] 成功导入 {added} 位教师数据。")
    pause()


# ─── 菜单 ─────────────────────────────────────────────────────

def teacher_management_menu(current_user):
    """教师管理子菜单"""
    while True:
        print_menu(
            "教师管理",
            [
                ("1", "添加教师"),
                ("2", "教师列表"),
                ("3", "查询教师"),
                ("4", "查看教师详情"),
                ("5", "修改教师信息"),
                ("6", "删除教师"),
                ("7", "教师统计"),
                ("8", "批量导入示例数据"),
                ("0", "返回上级菜单"),
            ],
        )
        choice = input("  请选择操作: ").strip()
        if choice == "1":
            add_teacher(current_user)
        elif choice == "2":
            list_teachers(current_user)
        elif choice == "3":
            search_teacher(current_user)
        elif choice == "4":
            view_teacher_detail(current_user)
        elif choice == "5":
            update_teacher(current_user)
        elif choice == "6":
            delete_teacher(current_user)
        elif choice == "7":
            teacher_statistics(current_user)
        elif choice == "8":
            batch_import_teachers(current_user)
        elif choice == "0":
            break
        else:
            print("  [提示] 无效选项，请重新输入。")
