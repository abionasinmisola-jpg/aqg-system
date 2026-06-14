from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from backend import db
from backend.models.course import Course
from backend.models.enrollment import Enrollment
from backend.models.test import Test
from backend.models.result import Result
from backend.models.question import Question
from backend.routes.student import student_required
import json

student_views_bp = Blueprint("student_views", __name__, url_prefix="/student")


@student_views_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    # Get enrolled courses
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id,
        status="enrolled"
    ).all()

    enrolled_courses = [e.course for e in enrollments]

    # Get available tests for enrolled courses
    available_tests = []
    for course in enrolled_courses:
        tests = Test.query.filter_by(
            course_id=course.id,
            is_published=True
        ).all()
        for test in tests:
            # Check if student already took this test
            result = Result.query.filter_by(
                student_id=current_user.id,
                test_id=test.id
            ).first()
            if not result:
                available_tests.append({
                    "test": test,
                    "course": course
                })

    # Get recent results
    recent_results = Result.query.filter_by(
        student_id=current_user.id
    ).order_by(Result.submitted_at.desc()).limit(5).all()

    return render_template(
        "student/dashboard.html",
        user=current_user,
        enrolled_courses=enrolled_courses,
        available_tests=available_tests,
        recent_results=recent_results
    )


@student_views_bp.route("/browse-courses")
@login_required
@student_required
def browse_courses():
    # Get all available courses
    courses = Course.query.filter_by(is_available=True).all()

    # Check enrollment status for each
    course_list = []
    for course in courses:
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course.id
        ).first()
        course_list.append({
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "domain": course.domain,
            "lecturer": course.lecturer.full_name,
            "enrolled_count": course.enrolled_count(),
            "question_count": len(course.questions),
            "enrollment_status": enrollment.status if enrollment else None
        })

    return jsonify({"courses": course_list})


@student_views_bp.route("/enroll/<int:course_id>", methods=["POST"])
@login_required
@student_required
def enroll(course_id):
    course = Course.query.filter_by(
        id=course_id, is_available=True
    ).first_or_404()

    # Check if already enrolled
    existing = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first()

    if existing:
        return jsonify({
            "success": False,
            "message": "You are already enrolled in this course"
        }), 400

    enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course_id,
        status="pending"
    )
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"Request sent! Awaiting approval for {course.title}."
        })


@student_views_bp.route("/unenroll/<int:course_id>", methods=["DELETE"])
@login_required
@student_required
def unenroll(course_id):
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first_or_404()

    db.session.delete(enrollment)
    db.session.commit()

    return jsonify({"success": True, "message": "Successfully unenrolled"})


@student_views_bp.route("/my-courses")
@login_required
@student_required
def my_courses():
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id
    ).all()

    return jsonify({
        "courses": [{
            "id": e.course.id,
            "code": e.course.code,
            "title": e.course.title,
            "domain": e.course.domain,
            "lecturer": e.course.lecturer.full_name,
            "status": e.status,
            "enrolled_at": e.enrolled_at.strftime("%d %b %Y")
        } for e in enrollments]
    })


@student_views_bp.route("/take-test/<int:test_id>")
@login_required
@student_required
def take_test(test_id):
    test = Test.query.get_or_404(test_id)

    # Check if student is enrolled
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=test.course_id,
        status="enrolled"
    ).first()

    if not enrollment:
        return jsonify({"success": False, "message": "You are not enrolled in this course"}), 403

    # Check if already taken
    existing = Result.query.filter_by(
        student_id=current_user.id,
        test_id=test_id
    ).first()

    if existing:
        return jsonify({"success": False, "message": "You have already taken this test"}), 400

    # Get questions
    questions = Question.query.filter_by(
        test_id=test_id,
        is_approved=True
    ).all()

    return jsonify({
        "test": {
            "id": test.id,
            "title": test.title,
            "time_limit": test.time_limit,
            "category": test.category,
            "domain": test.domain,
            "course": test.course.title
        },
        "questions": [{
            "id": q.id,
            "question": q.question_text,
            "type": q.question_type,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d
            } if q.question_type == "mcq" else {}
        } for q in questions]
    })


@student_views_bp.route("/submit-test/<int:test_id>", methods=["POST"])
@login_required
@student_required
def submit_test(test_id):
    test = Test.query.get_or_404(test_id)
    data = request.get_json()
    answers = data.get("answers", {})

    # Get questions
    questions = Question.query.filter_by(
        test_id=test_id,
        is_approved=True
    ).all()

    # Calculate score
    score = 0
    total = len(questions)

    for q in questions:
        student_answer = answers.get(str(q.id), "")
        if q.question_type == "fill":
            if student_answer.strip().lower() == (q.correct_answer or "").strip().lower():
                score += 1
        else:  # mcq
            if student_answer.strip().upper() == (q.correct_answer or "").strip().upper():
                score += 1

    percentage = round((score / total) * 100, 1) if total > 0 else 0

    # Calculate grade
    if percentage >= 70:
        grade = "A"
    elif percentage >= 60:
        grade = "B"
    elif percentage >= 50:
        grade = "C"
    elif percentage >= 45:
        grade = "D"
    else:
        grade = "F"

    # Save result
    result = Result(
        student_id=current_user.id,
        test_id=test_id,
        course_id=test.course_id,
        score=score,
        total=total,
        percentage=percentage,
        grade=grade,
        answers=json.dumps(answers)
    )
    db.session.add(result)
    db.session.commit()

    return jsonify({
        "success": True,
        "score": score,
        "total": total,
        "percentage": percentage,
        "grade": grade,
        "message": f"Test submitted! You scored {percentage}% ({grade})"
    })


@student_views_bp.route("/my-results")
@login_required
@student_required
def my_results():
    results = Result.query.filter_by(
        student_id=current_user.id
    ).order_by(Result.submitted_at.desc()).all()

    return jsonify({
        "results": [{
            "id": r.id,
            "test": r.test.title,
            "course": r.course.code,
            "score": r.score,
            "total": r.total,
            "percentage": r.percentage,
            "grade": r.grade,
            "submitted_at": r.submitted_at.strftime("%d %b %Y")
        } for r in results]
    })

@student_views_bp.route("/available-tests")
@login_required
@student_required
def available_tests():
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id, status="enrolled"
    ).all()
    enrolled_course_ids = [e.course_id for e in enrollments]

    tests_out = []
    for cid in enrolled_course_ids:
        course = Course.query.get(cid)
        if not course:
            continue
        tests = Test.query.filter_by(course_id=cid, is_published=True).all()
        for t in tests:
            taken = Result.query.filter_by(student_id=current_user.id, test_id=t.id).first()
            if taken:
                continue
            tests_out.append({
                "id": t.id,
                "title": t.title,
                "course_code": course.code,
                "category": t.category,
                "time_limit": t.time_limit,
                "question_count": Question.query.filter_by(test_id=t.id, is_approved=True).count()
            })

    return jsonify({"tests": tests_out})

@student_views_bp.route("/search-courses")
@login_required
@student_required
def search_courses():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"courses": []})

    like = f"%{q}%"
    courses = Course.query.filter(
        Course.is_available == True,
        db.or_(Course.code.ilike(like), Course.title.ilike(like))
    ).all()

    course_list = []
    for course in courses:
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, course_id=course.id
        ).first()
        course_list.append({
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "domain": course.domain,
            "lecturer": course.lecturer.full_name,
            "enrollment_status": enrollment.status if enrollment else None
        })

    return jsonify({"courses": course_list})

@student_views_bp.route("/test/<int:test_id>")
@login_required
@student_required
def test_page(test_id):
    return render_template("student/take_test.html", test_id=test_id, user=current_user)