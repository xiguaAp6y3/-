# -*- coding: utf-8 -*-
"""
成绩管理模块 - 提供学生课程成绩的增、删、改、查及统计分析
"""

from utils import (
    load_json, save_json, print_title, print_menu, print_separator,
    input_required, input_float, input_yes_no, input_choice,
    current_timestamp, pause, generate_id
)

GRADES_FILE = "grades.json"
STUDENTS_FILE = "students.json"
COURSES_FILE = "courses.json"


def _load_grades():
    return load_json(GRADES_FILE)


def _save_grades(grades):
    save_json(GRADES_FILE, grades)


def _load_students():
    return load_json(STUDENTS_FILE)


def _load_courses():
    return load_json(COURSES_FILE)


def _get_grade_level(score):
    """根据百分制分数返回等级"""
    if score >= 90:
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 70:
        return "中等"
    elif score >= 60:
        return "及格"
    else:
        return "不及格"


def _print_grade_row(grade, student_name="", course_name=""):
    """打印成绩列表行"""
    level = _get_grade_level(grade["score"])
    sname = student_name if student_name else grade["student_id"]
    cname = course_name if course_name else grade["course_id"]
    print(
        f"  {grade['grade_id']:<10} "
        f"{grade['student_id']:<10} "
        f"{sname:<10} "
        f"{grade['course_id']:<10} "
        f"{cname:<16} "
        f"{grade['score']:<7.1f} "
        f"{level:<6} "
        f"{grade['semester']}"
    )


def _print_list_header():
    """打印成绩列表表头"""
    print(
        f"  {'成绩ID':<10} "
        f"{'学号':<10} "
        f"{'姓名':<10} "
        f"{'课程编号':<10} "
        f"{'课程名称':<16} "
        f"{'成绩':<7} "
        f"{'等级':<6} "
        f"{'学期'}"
    )
    print_separator("-", 90)


def _build_lookup(items, key_field):
    """构建字典查找表，key 为指定字段的值"""
    return {item[key_field]: item for item in items}


# ─── 增 ──────────────────────────────────────────────────────

def add_grade(current_user):
    """录入成绩"""
    print_title("录入成绩")
    grades = _load_grades()
    students = _load_students()
    courses = _load_courses()

    if not students:
        print("  [提示] 暂无学生数据，请先添加学生。")
        pause()
        return
    if not courses:
        print("  [提示] 暂无课程数据，请先添加课程。")
        pause()
        return

    existing_ids = {g["grade_id"] for g in grades}
    student_map = _build_lookup(students, "student_id")
    course_map = _build_lookup(courses, "course_id")

    student_id = input_required("  请输入学生学号: ")
    if student_id not in student_map:
        print("  [错误] 该学生不存在。")
        pause()
        return

    course_id = input_required("  请输入课程编号: ")
    if course_id not in course_map:
        print("  [错误] 该课程不存在。")
        pause()
        return

    semester = course_map[course_id]["semester"]
    # 检查是否已录入
    dup = next(
        (g for g in grades if g["student_id"] == student_id and g["course_id"] == course_id and g["semester"] == semester),
        None,
    )
    if dup:
        print(
            f"  [错误] 该学生（{student_map[student_id]['name']}）在本学期已有 "
            f"'{course_map[course_id]['name']}' 的成绩（{dup['score']}），请使用修改功能。"
        )
        pause()
        return

    score = input_float("  成绩（0~100）: ", min_val=0.0, max_val=100.0)
    remark = input("  备注（可选）: ").strip()

    new_grade = {
        "grade_id": generate_id("G", existing_ids),
        "student_id": student_id,
        "course_id": course_id,
        "score": score,
        "semester": semester,
        "remark": remark,
        "created_at": current_timestamp(),
        "updated_at": current_timestamp(),
    }
    grades.append(new_grade)
    _save_grades(grades)
    level = _get_grade_level(score)
    print(
        f"  [成功] 已录入 {student_map[student_id]['name']} 的 "
        f"'{course_map[course_id]['name']}' 成绩：{score}（{level}）"
    )
    pause()


def batch_add_grades(current_user):
    """批量录入一门课程的成绩"""
    print_title("批量录入课程成绩")
    grades = _load_grades()
    students = _load_students()
    courses = _load_courses()

    if not students:
        print("  [提示] 暂无学生数据。")
        pause()
        return
    if not courses:
        print("  [提示] 暂无课程数据。")
        pause()
        return

    existing_ids = {g["grade_id"] for g in grades}
    student_map = _build_lookup(students, "student_id")
    course_map = _build_lookup(courses, "course_id")

    course_id = input_required("  请输入课程编号: ")
    if course_id not in course_map:
        print("  [错误] 该课程不存在。")
        pause()
        return

    course = course_map[course_id]
    semester = course["semester"]
    print(f"  课程：{course['name']}，学期：{semester}")
    print("  请依次输入每位学生的成绩（输入 'q' 结束录入）\n")

    added = 0
    skipped = 0
    for student in students:
        sid = student["student_id"]
        dup = next(
            (g for g in grades if g["student_id"] == sid and g["course_id"] == course_id and g["semester"] == semester),
            None,
        )
        if dup:
            print(f"  {student['name']}（{sid}）已有成绩 {dup['score']}，跳过。")
            skipped += 1
            continue

        raw = input(f"  {student['name']}（{sid}）的成绩: ").strip()
        if raw.lower() == "q":
            break
        try:
            score = float(raw)
            if not (0 <= score <= 100):
                raise ValueError
        except ValueError:
            print("  [提示] 无效成绩，跳过该学生。")
            skipped += 1
            continue

        new_grade = {
            "grade_id": generate_id("G", existing_ids),
            "student_id": sid,
            "course_id": course_id,
            "score": score,
            "semester": semester,
            "remark": "",
            "created_at": current_timestamp(),
            "updated_at": current_timestamp(),
        }
        grades.append(new_grade)
        existing_ids.add(new_grade["grade_id"])
        added += 1

    _save_grades(grades)
    print(f"\n  [完成] 成功录入 {added} 条，跳过 {skipped} 条。")
    pause()


# ─── 查 ──────────────────────────────────────────────────────

def list_grades(current_user):
    """列出所有成绩"""
    grades = _load_grades()
    print_title("成绩列表")
    if not grades:
        print("  暂无成绩数据。")
        pause()
        return

    students = _load_students()
    courses = _load_courses()
    student_map = _build_lookup(students, "student_id")
    course_map = _build_lookup(courses, "course_id")

    print(f"  共 {len(grades)} 条成绩记录：\n")
    _print_list_header()
    for g in grades:
        sname = student_map.get(g["student_id"], {}).get("name", "")
        cname = course_map.get(g["course_id"], {}).get("name", "")
        _print_grade_row(g, sname, cname)
    pause()


def search_grade(current_user):
    """查询成绩"""
    print_title("查询成绩")
    print("  查询方式：")
    print("  1. 按学生学号查询")
    print("  2. 按课程编号查询")
    print("  3. 按学期查询")
    print("  4. 按成绩等级查询")
    print_separator("-", 60)
    choice = input_choice("  请选择查询方式: ", {"1", "2", "3", "4"})

    grades = _load_grades()
    students = _load_students()
    courses = _load_courses()
    student_map = _build_lookup(students, "student_id")
    course_map = _build_lookup(courses, "course_id")

    if choice == "1":
        sid = input_required("  请输入学号: ")
        results = [g for g in grades if g["student_id"] == sid]
    elif choice == "2":
        cid = input_required("  请输入课程编号: ")
        results = [g for g in grades if g["course_id"] == cid]
    elif choice == "3":
        sem = input_required("  请输入学期（如 2023-2024-1）: ")
        results = [g for g in grades if g["semester"] == sem]
    else:
        LEVELS = {"优秀", "良好", "中等", "及格", "不及格"}
        level = input_choice(f"  请选择等级 ({'/'.join(LEVELS)}): ", LEVELS)
        results = [g for g in grades if _get_grade_level(g["score"]) == level]

    if not results:
        print("  未找到匹配的成绩。")
    else:
        print(f"  找到 {len(results)} 条记录：\n")
        _print_list_header()
        for g in results:
            sname = student_map.get(g["student_id"], {}).get("name", "")
            cname = course_map.get(g["course_id"], {}).get("name", "")
            _print_grade_row(g, sname, cname)
    pause()


def view_student_grades(current_user):
    """查看某学生的所有成绩及绩点"""
    print_title("学生成绩单")
    sid = input_required("  请输入学生学号: ")

    students = _load_students()
    student = next((s for s in students if s["student_id"] == sid), None)
    if not student:
        print("  [错误] 未找到该学生。")
        pause()
        return

    grades = _load_grades()
    courses = _load_courses()
    course_map = _build_lookup(courses, "course_id")

    student_grades = [g for g in grades if g["student_id"] == sid]
    if not student_grades:
        print(f"  学生 {student['name']} 暂无成绩记录。")
        pause()
        return

    print(f"\n  学生：{student['name']}（{sid}，{student['class_name']}）\n")
    print(f"  {'课程编号':<10} {'课程名称':<20} {'学分':<6} {'成绩':<8} {'等级':<8} {'学期'}")
    print_separator("-", 70)

    total_weighted = 0.0
    total_credits = 0.0
    for g in student_grades:
        course = course_map.get(g["course_id"], {})
        cname = course.get("name", g["course_id"])
        credits = course.get("credits", 0)
        level = _get_grade_level(g["score"])
        gpa_point = _score_to_gpa(g["score"])
        total_weighted += gpa_point * credits
        total_credits += credits
        print(
            f"  {g['course_id']:<10} {cname:<20} {credits:<6} "
            f"{g['score']:<8.1f} {level:<8} {g['semester']}"
        )

    print_separator("-", 70)
    avg_score = sum(g["score"] for g in student_grades) / len(student_grades)
    gpa = total_weighted / total_credits if total_credits > 0 else 0
    print(f"  共 {len(student_grades)} 门课程，总学分：{total_credits:.1f}")
    print(f"  平均分：{avg_score:.2f}，加权绩点（GPA）：{gpa:.2f}")
    pause()


def _score_to_gpa(score):
    """百分制转绩点（4.0 制）"""
    if score >= 90:
        return 4.0
    elif score >= 85:
        return 3.7
    elif score >= 80:
        return 3.3
    elif score >= 75:
        return 3.0
    elif score >= 70:
        return 2.7
    elif score >= 65:
        return 2.3
    elif score >= 60:
        return 2.0
    else:
        return 0.0


# ─── 改 ──────────────────────────────────────────────────────

def update_grade(current_user):
    """修改成绩"""
    print_title("修改成绩")
    gid = input_required("  请输入要修改的成绩ID: ")
    grades = _load_grades()
    grade = next((g for g in grades if g["grade_id"] == gid), None)
    if not grade:
        print("  [错误] 未找到该成绩记录。")
        pause()
        return

    students = _load_students()
    courses = _load_courses()
    student_map = _build_lookup(students, "student_id")
    course_map = _build_lookup(courses, "course_id")

    sname = student_map.get(grade["student_id"], {}).get("name", "")
    cname = course_map.get(grade["course_id"], {}).get("name", "")
    print(f"\n  当前成绩：学生={sname}，课程={cname}，分数={grade['score']}，学期={grade['semester']}")

    score = input_float(f"  新成绩 [{grade['score']}]: ", min_val=0.0, max_val=100.0)
    remark = input(f"  备注 [{grade.get('remark', '')}]（留空不变）: ").strip()

    grade["score"] = score
    if remark:
        grade["remark"] = remark
    grade["updated_at"] = current_timestamp()
    _save_grades(grades)
    print(f"  [成功] 成绩已修改为 {score}（{_get_grade_level(score)}）。")
    pause()


# ─── 删 ──────────────────────────────────────────────────────

def delete_grade(current_user):
    """删除成绩记录"""
    print_title("删除成绩")
    gid = input_required("  请输入要删除的成绩ID: ")
    grades = _load_grades()
    grade = next((g for g in grades if g["grade_id"] == gid), None)
    if not grade:
        print("  [错误] 未找到该成绩记录。")
        pause()
        return

    students = _load_students()
    courses = _load_courses()
    student_map = _build_lookup(students, "student_id")
    course_map = _build_lookup(courses, "course_id")
    sname = student_map.get(grade["student_id"], {}).get("name", grade["student_id"])
    cname = course_map.get(grade["course_id"], {}).get("name", grade["course_id"])

    print(f"\n  即将删除：{sname} 的 '{cname}' 成绩（{grade['score']}）")
    confirm = input_yes_no("  确认删除？")
    if confirm:
        grades.remove(grade)
        _save_grades(grades)
        print("  [成功] 成绩已删除。")
    else:
        print("  操作已取消。")
    pause()


# ─── 统计 ─────────────────────────────────────────────────────

def grade_statistics(current_user):
    """成绩统计分析"""
    grades = _load_grades()
    print_title("成绩统计分析")
    if not grades:
        print("  暂无成绩数据。")
        pause()
        return

    courses = _load_courses()
    course_map = _build_lookup(courses, "course_id")

    total = len(grades)
    scores = [g["score"] for g in grades]
    avg = sum(scores) / total
    max_score = max(scores)
    min_score = min(scores)

    level_counts = {"优秀": 0, "良好": 0, "中等": 0, "及格": 0, "不及格": 0}
    for g in grades:
        level_counts[_get_grade_level(g["score"])] += 1

    print(f"  成绩记录总数  : {total}")
    print(f"  总体平均分    : {avg:.2f}")
    print(f"  最高分        : {max_score:.1f}")
    print(f"  最低分        : {min_score:.1f}")
    print()
    print("  各等级分布：")
    for level, cnt in level_counts.items():
        pct = cnt / total * 100
        bar = "█" * int(pct / 5)
        print(f"    {level:<6}: {cnt:>4} 条 ({pct:5.1f}%) {bar}")

    # 按课程统计
    print()
    print("  各课程平均分：")
    course_groups = {}
    for g in grades:
        course_groups.setdefault(g["course_id"], []).append(g["score"])

    for cid, cscores in sorted(course_groups.items()):
        cname = course_map.get(cid, {}).get("name", cid)
        cavg = sum(cscores) / len(cscores)
        print(f"    {cname}: {cavg:.2f} 分（{len(cscores)} 人）")

    pause()


def top_students(current_user):
    """查看各科前N名学生"""
    print_title("各科成绩排名")
    courses = _load_courses()
    if not courses:
        print("  暂无课程数据。")
        pause()
        return

    cid = input_required("  请输入课程编号: ")
    course = next((c for c in courses if c["course_id"] == cid), None)
    if not course:
        print("  [错误] 未找到该课程。")
        pause()
        return

    top_n = input("  显示前几名？（默认5）: ").strip()
    try:
        top_n = int(top_n) if top_n else 5
        top_n = max(1, min(top_n, 100))
    except ValueError:
        top_n = 5

    grades = _load_grades()
    students = _load_students()
    student_map = _build_lookup(students, "student_id")

    course_grades = [g for g in grades if g["course_id"] == cid]
    if not course_grades:
        print(f"  课程 '{course['name']}' 暂无成绩记录。")
        pause()
        return

    course_grades.sort(key=lambda g: g["score"], reverse=True)
    display = course_grades[:top_n]

    print(f"\n  课程：{course['name']}  共 {len(course_grades)} 人\n")
    print(f"  {'排名':<6} {'学号':<12} {'姓名':<10} {'成绩':<8} {'等级'}")
    print_separator("-", 50)
    for rank, g in enumerate(display, 1):
        sname = student_map.get(g["student_id"], {}).get("name", "")
        level = _get_grade_level(g["score"])
        print(f"  {rank:<6} {g['student_id']:<12} {sname:<10} {g['score']:<8.1f} {level}")
    pause()


def batch_import_grades(current_user):
    """批量导入示例成绩数据"""
    print_title("批量导入示例成绩数据")
    grades = _load_grades()
    students = _load_students()
    courses = _load_courses()

    if not students or not courses:
        print("  [提示] 请先导入学生和课程数据（学生管理 → 批量导入，课程管理 → 批量导入）。")
        pause()
        return

    existing_ids = {g["grade_id"] for g in grades}
    existing_keys = {(g["student_id"], g["course_id"], g["semester"]) for g in grades}

    import random
    random.seed(42)

    added = 0
    for student in students[:10]:
        for course in courses[:5]:
            key = (student["student_id"], course["course_id"], course["semester"])
            if key in existing_keys:
                continue
            score = round(random.uniform(55.0, 99.0), 1)
            new_grade = {
                "grade_id": generate_id("G", existing_ids),
                "student_id": student["student_id"],
                "course_id": course["course_id"],
                "score": score,
                "semester": course["semester"],
                "remark": "",
                "created_at": current_timestamp(),
                "updated_at": current_timestamp(),
            }
            grades.append(new_grade)
            existing_ids.add(new_grade["grade_id"])
            existing_keys.add(key)
            added += 1

    _save_grades(grades)
    print(f"  [成功] 成功导入 {added} 条成绩数据。")
    pause()


# ─── 菜单 ─────────────────────────────────────────────────────

def grade_management_menu(current_user):
    """成绩管理子菜单"""
    while True:
        print_menu(
            "成绩管理",
            [
                ("1", "录入成绩"),
                ("2", "批量录入课程成绩"),
                ("3", "成绩列表"),
                ("4", "查询成绩"),
                ("5", "查看学生成绩单（含绩点）"),
                ("6", "修改成绩"),
                ("7", "删除成绩"),
                ("8", "成绩统计分析"),
                ("9", "课程成绩排名"),
                ("A", "批量导入示例数据"),
                ("0", "返回上级菜单"),
            ],
        )
        choice = input("  请选择操作: ").strip().upper()
        if choice == "1":
            add_grade(current_user)
        elif choice == "2":
            batch_add_grades(current_user)
        elif choice == "3":
            list_grades(current_user)
        elif choice == "4":
            search_grade(current_user)
        elif choice == "5":
            view_student_grades(current_user)
        elif choice == "6":
            update_grade(current_user)
        elif choice == "7":
            delete_grade(current_user)
        elif choice == "8":
            grade_statistics(current_user)
        elif choice == "9":
            top_students(current_user)
        elif choice == "A":
            batch_import_grades(current_user)
        elif choice == "0":
            break
        else:
            print("  [提示] 无效选项，请重新输入。")
