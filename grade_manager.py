# -*- coding: utf-8 -*-
"""
成绩管理模块 - 提供学生课程成绩的增、删、改、查及统计分析（数据存储于 MySQL）
"""

from db import execute_query, generate_next_id
from utils import (
    print_title, print_menu, print_separator,
    input_required, input_float, input_yes_no, input_choice,
    current_timestamp, pause,
)


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


def _print_grade_row(grade):
    """打印成绩列表行（行内已含 student_name / course_name 字段）"""
    level = _get_grade_level(grade["score"])
    sname = grade.get("student_name", grade["student_id"])
    cname = grade.get("course_name", grade["course_id"])
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


# ─── 增 ──────────────────────────────────────────────────────

def add_grade(current_user):
    """录入成绩"""
    print_title("录入成绩")

    students_exist = execute_query(
        "SELECT COUNT(*) AS cnt FROM students", fetchone=True
    )["cnt"]
    courses_exist = execute_query(
        "SELECT COUNT(*) AS cnt FROM courses", fetchone=True
    )["cnt"]
    if not students_exist:
        print("  [提示] 暂无学生数据，请先添加学生。")
        pause()
        return
    if not courses_exist:
        print("  [提示] 暂无课程数据，请先添加课程。")
        pause()
        return

    student_id = input_required("  请输入学生学号: ")
    student = execute_query(
        "SELECT * FROM students WHERE student_id = %s", (student_id,), fetchone=True
    )
    if not student:
        print("  [错误] 该学生不存在。")
        pause()
        return

    course_id = input_required("  请输入课程编号: ")
    course = execute_query(
        "SELECT * FROM courses WHERE course_id = %s", (course_id,), fetchone=True
    )
    if not course:
        print("  [错误] 该课程不存在。")
        pause()
        return

    semester = course["semester"]
    dup = execute_query(
        "SELECT * FROM grades WHERE student_id = %s AND course_id = %s AND semester = %s",
        (student_id, course_id, semester),
        fetchone=True,
    )
    if dup:
        print(
            f"  [错误] 该学生（{student['name']}）在本学期已有 "
            f"'{course['name']}' 的成绩（{dup['score']}），请使用修改功能。"
        )
        pause()
        return

    score = input_float("  成绩（0~100）: ", min_val=0.0, max_val=100.0)
    remark = input("  备注（可选）: ").strip()
    now = current_timestamp()

    gid = generate_next_id("grades", "grade_id", "G")
    execute_query(
        "INSERT INTO grades "
        "(grade_id, student_id, course_id, score, semester, remark, created_at, updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (gid, student_id, course_id, score, semester, remark, now, now),
    )
    level = _get_grade_level(score)
    print(
        f"  [成功] 已录入 {student['name']} 的 "
        f"'{course['name']}' 成绩：{score}（{level}）"
    )
    pause()


def batch_add_grades(current_user):
    """批量录入一门课程的所有学生成绩"""
    print_title("批量录入课程成绩")

    students_exist = execute_query(
        "SELECT COUNT(*) AS cnt FROM students", fetchone=True
    )["cnt"]
    courses_exist = execute_query(
        "SELECT COUNT(*) AS cnt FROM courses", fetchone=True
    )["cnt"]
    if not students_exist:
        print("  [提示] 暂无学生数据。")
        pause()
        return
    if not courses_exist:
        print("  [提示] 暂无课程数据。")
        pause()
        return

    course_id = input_required("  请输入课程编号: ")
    course = execute_query(
        "SELECT * FROM courses WHERE course_id = %s", (course_id,), fetchone=True
    )
    if not course:
        print("  [错误] 该课程不存在。")
        pause()
        return

    semester = course["semester"]
    print(f"  课程：{course['name']}，学期：{semester}")
    print("  请依次输入每位学生的成绩（输入 'q' 结束录入）\n")

    students = execute_query("SELECT * FROM students ORDER BY student_id", fetch=True)
    now = current_timestamp()
    added = 0
    skipped = 0
    for student in students:
        sid = student["student_id"]
        dup = execute_query(
            "SELECT 1 FROM grades WHERE student_id=%s AND course_id=%s AND semester=%s",
            (sid, course_id, semester),
            fetchone=True,
        )
        if dup:
            print(f"  {student['name']}（{sid}）本学期已有成绩，跳过。")
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

        gid = generate_next_id("grades", "grade_id", "G")
        execute_query(
            "INSERT INTO grades "
            "(grade_id, student_id, course_id, score, semester, remark, created_at, updated_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (gid, sid, course_id, score, semester, "", now, now),
        )
        added += 1

    print(f"\n  [完成] 成功录入 {added} 条，跳过 {skipped} 条。")
    pause()


# ─── 查 ──────────────────────────────────────────────────────

def list_grades(current_user):
    """列出所有成绩（关联学生姓名和课程名称）"""
    grades = execute_query(
        "SELECT g.*, s.name AS student_name, c.name AS course_name "
        "FROM grades g "
        "JOIN students s ON g.student_id = s.student_id "
        "JOIN courses  c ON g.course_id  = c.course_id "
        "ORDER BY g.grade_id",
        fetch=True,
    )
    print_title("成绩列表")
    if not grades:
        print("  暂无成绩数据。")
        pause()
        return
    print(f"  共 {len(grades)} 条成绩记录：\n")
    _print_list_header()
    for g in grades:
        _print_grade_row(g)
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

    base_sql = (
        "SELECT g.*, s.name AS student_name, c.name AS course_name "
        "FROM grades g "
        "JOIN students s ON g.student_id = s.student_id "
        "JOIN courses  c ON g.course_id  = c.course_id "
    )

    if choice == "1":
        sid = input_required("  请输入学号: ")
        results = execute_query(
            base_sql + "WHERE g.student_id = %s ORDER BY g.grade_id",
            (sid,), fetch=True,
        )
    elif choice == "2":
        cid = input_required("  请输入课程编号: ")
        results = execute_query(
            base_sql + "WHERE g.course_id = %s ORDER BY g.grade_id",
            (cid,), fetch=True,
        )
    elif choice == "3":
        sem = input_required("  请输入学期（如 2023-2024-1）: ")
        results = execute_query(
            base_sql + "WHERE g.semester = %s ORDER BY g.grade_id",
            (sem,), fetch=True,
        )
    else:
        LEVELS = {"优秀": (90, 100), "良好": (80, 89.9), "中等": (70, 79.9),
                  "及格": (60, 69.9), "不及格": (0, 59.9)}
        level = input_choice(f"  请选择等级 ({'/'.join(LEVELS)}): ", set(LEVELS))
        lo, hi = LEVELS[level]
        results = execute_query(
            base_sql + "WHERE g.score >= %s AND g.score <= %s ORDER BY g.grade_id",
            (lo, hi), fetch=True,
        )

    if not results:
        print("  未找到匹配的成绩。")
    else:
        print(f"  找到 {len(results)} 条记录：\n")
        _print_list_header()
        for g in results:
            _print_grade_row(g)
    pause()


def view_student_grades(current_user):
    """查看某学生的所有成绩及绩点"""
    print_title("学生成绩单")
    sid = input_required("  请输入学生学号: ")
    student = execute_query(
        "SELECT * FROM students WHERE student_id = %s", (sid,), fetchone=True
    )
    if not student:
        print("  [错误] 未找到该学生。")
        pause()
        return

    grades = execute_query(
        "SELECT g.*, c.name AS course_name, c.credits "
        "FROM grades g "
        "JOIN courses c ON g.course_id = c.course_id "
        "WHERE g.student_id = %s "
        "ORDER BY g.semester, c.name",
        (sid,), fetch=True,
    )
    if not grades:
        print(f"  学生 {student['name']} 暂无成绩记录。")
        pause()
        return

    print(f"\n  学生：{student['name']}（{sid}，{student['class_name']}）\n")
    print(f"  {'课程编号':<10} {'课程名称':<20} {'学分':<6} {'成绩':<8} {'等级':<8} {'学期'}")
    print_separator("-", 70)

    total_weighted = 0.0
    total_credits = 0.0
    for g in grades:
        cname = g["course_name"]
        credits = g["credits"]
        level = _get_grade_level(g["score"])
        gpa_point = _score_to_gpa(g["score"])
        total_weighted += gpa_point * credits
        total_credits += credits
        print(
            f"  {g['course_id']:<10} {cname:<20} {credits:<6} "
            f"{g['score']:<8.1f} {level:<8} {g['semester']}"
        )

    print_separator("-", 70)
    avg_score = sum(g["score"] for g in grades) / len(grades)
    gpa = total_weighted / total_credits if total_credits > 0 else 0
    print(f"  共 {len(grades)} 门课程，总学分：{total_credits:.1f}")
    print(f"  平均分：{avg_score:.2f}，加权绩点（GPA）：{gpa:.2f}")
    pause()


# ─── 改 ──────────────────────────────────────────────────────

def update_grade(current_user):
    """修改成绩"""
    print_title("修改成绩")
    gid = input_required("  请输入要修改的成绩ID: ")
    grade = execute_query(
        "SELECT g.*, s.name AS student_name, c.name AS course_name "
        "FROM grades g "
        "JOIN students s ON g.student_id = s.student_id "
        "JOIN courses  c ON g.course_id  = c.course_id "
        "WHERE g.grade_id = %s",
        (gid,), fetchone=True,
    )
    if not grade:
        print("  [错误] 未找到该成绩记录。")
        pause()
        return

    print(
        f"\n  当前成绩：学生={grade['student_name']}，"
        f"课程={grade['course_name']}，分数={grade['score']}，学期={grade['semester']}"
    )

    score = input_float(f"  新成绩 [{grade['score']}]: ", min_val=0.0, max_val=100.0)
    remark = input(f"  备注 [{grade.get('remark', '')}]（留空不变）: ").strip()
    now = current_timestamp()

    fields = {"score": score, "updated_at": now}
    if remark:
        fields["remark"] = remark

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [gid]
    execute_query(f"UPDATE grades SET {set_clause} WHERE grade_id = %s", values)  # noqa: S608
    print(f"  [成功] 成绩已修改为 {score}（{_get_grade_level(score)}）。")
    pause()


# ─── 删 ──────────────────────────────────────────────────────

def delete_grade(current_user):
    """删除成绩记录"""
    print_title("删除成绩")
    gid = input_required("  请输入要删除的成绩ID: ")
    grade = execute_query(
        "SELECT g.*, s.name AS student_name, c.name AS course_name "
        "FROM grades g "
        "JOIN students s ON g.student_id = s.student_id "
        "JOIN courses  c ON g.course_id  = c.course_id "
        "WHERE g.grade_id = %s",
        (gid,), fetchone=True,
    )
    if not grade:
        print("  [错误] 未找到该成绩记录。")
        pause()
        return

    print(
        f"\n  即将删除：{grade['student_name']} 的 "
        f"'{grade['course_name']}' 成绩（{grade['score']}）"
    )
    confirm = input_yes_no("  确认删除？")
    if confirm:
        execute_query("DELETE FROM grades WHERE grade_id = %s", (gid,))
        print("  [成功] 成绩已删除。")
    else:
        print("  操作已取消。")
    pause()


# ─── 统计 ─────────────────────────────────────────────────────

def grade_statistics(current_user):
    """成绩统计分析"""
    print_title("成绩统计分析")
    total_row = execute_query(
        "SELECT COUNT(*) AS cnt, AVG(score) AS avg, MAX(score) AS max, MIN(score) AS min "
        "FROM grades",
        fetchone=True,
    )
    if not total_row or total_row["cnt"] == 0:
        print("  暂无成绩数据。")
        pause()
        return

    total = total_row["cnt"]
    avg = float(total_row["avg"])
    max_score = float(total_row["max"])
    min_score = float(total_row["min"])

    # 各等级分布（在 Python 中统计）
    all_grades = execute_query("SELECT score FROM grades", fetch=True)
    level_counts = {"优秀": 0, "良好": 0, "中等": 0, "及格": 0, "不及格": 0}
    for g in all_grades:
        level_counts[_get_grade_level(g["score"])] += 1

    # 各课程平均分（SQL 聚合）
    course_avgs = execute_query(
        "SELECT c.name AS course_name, AVG(g.score) AS avg_score, COUNT(*) AS cnt "
        "FROM grades g JOIN courses c ON g.course_id = c.course_id "
        "GROUP BY g.course_id, c.name ORDER BY c.name",
        fetch=True,
    )

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
    print()
    print("  各课程平均分：")
    for row in course_avgs:
        print(f"    {row['course_name']}: {float(row['avg_score']):.2f} 分（{row['cnt']} 人）")
    pause()


def top_students(current_user):
    """查看某课程成绩排名"""
    print_title("各科成绩排名")
    cid = input_required("  请输入课程编号: ")
    course = execute_query(
        "SELECT * FROM courses WHERE course_id = %s", (cid,), fetchone=True
    )
    if not course:
        print("  [错误] 未找到该课程。")
        pause()
        return

    top_n_str = input("  显示前几名？（默认5）: ").strip()
    try:
        top_n = int(top_n_str) if top_n_str else 5
        top_n = max(1, min(top_n, 100))
    except ValueError:
        top_n = 5

    ranked = execute_query(
        "SELECT g.grade_id, g.student_id, s.name AS student_name, g.score, g.semester "
        "FROM grades g "
        "JOIN students s ON g.student_id = s.student_id "
        "WHERE g.course_id = %s "
        "ORDER BY g.score DESC "
        "LIMIT %s",
        (cid, top_n), fetch=True,
    )

    total_in_course = execute_query(
        "SELECT COUNT(*) AS cnt FROM grades WHERE course_id = %s",
        (cid,), fetchone=True,
    )["cnt"]

    if not ranked:
        print(f"  课程 '{course['name']}' 暂无成绩记录。")
        pause()
        return

    print(f"\n  课程：{course['name']}  共 {total_in_course} 人\n")
    print(f"  {'排名':<6} {'学号':<12} {'姓名':<10} {'成绩':<8} {'等级'}")
    print_separator("-", 50)
    for rank, g in enumerate(ranked, 1):
        level = _get_grade_level(g["score"])
        print(
            f"  {rank:<6} {g['student_id']:<12} {g['student_name']:<10} "
            f"{g['score']:<8.1f} {level}"
        )
    pause()


def batch_import_grades(current_user):
    """批量导入示例成绩数据（前10名学生 × 前5门课程）"""
    print_title("批量导入示例成绩数据")
    students_count = execute_query(
        "SELECT COUNT(*) AS cnt FROM students", fetchone=True
    )["cnt"]
    courses_count = execute_query(
        "SELECT COUNT(*) AS cnt FROM courses", fetchone=True
    )["cnt"]
    if not students_count or not courses_count:
        print("  [提示] 请先导入学生和课程数据（学生管理 → 批量导入，课程管理 → 批量导入）。")
        pause()
        return

    students = execute_query(
        "SELECT student_id FROM students ORDER BY student_id LIMIT 10", fetch=True
    )
    courses = execute_query(
        "SELECT course_id, semester FROM courses ORDER BY course_id LIMIT 5", fetch=True
    )

    import random
    random.seed(42)
    now = current_timestamp()
    added = 0

    for student in students:
        for course in courses:
            sid = student["student_id"]
            cid = course["course_id"]
            sem = course["semester"]
            dup = execute_query(
                "SELECT 1 FROM grades WHERE student_id=%s AND course_id=%s AND semester=%s",
                (sid, cid, sem), fetchone=True,
            )
            if dup:
                continue
            score = round(random.uniform(55.0, 99.0), 1)
            gid = generate_next_id("grades", "grade_id", "G")
            execute_query(
                "INSERT INTO grades "
                "(grade_id, student_id, course_id, score, semester, remark, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (gid, sid, cid, score, sem, "", now, now),
            )
            added += 1

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

