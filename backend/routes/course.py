from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from backend import db
from backend.models.course import Course
from backend.models.enrollment import Enrollment
from backend.models.user import User
from backend.routes.lecturer import lecturer_required

course_bp = Blueprint("course", __name__, url_prefix="/lecturer-portal/courses")


def my_courses():
    from backend.models.question import Question
    from backend.models.test import Test

    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    questions_generated = Question.query.filter_by(lecturer_id=current_user.id).count()
    published_tests = Test.query.filter_by(lecturer_id=current_user.id, is_published=True).count()

    return jsonify({
        "courses": [{
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "domain": c.domain,
            "is_available": c.is_available,
            "enrolled_count": c.enrolled_count(),
            "question_count": len(c.questions)
        } for c in courses],
        "questions_generated": questions_generated,
        "published_tests": published_tests
    })


@course_bp.route("/create", methods=["POST"])
@login_required
@lecturer_required
def create_course():
    data = request.get_json()

    code  = data.get("code", "").strip().upper()
    title = data.get("title", "").strip()
    domain = data.get("domain", "programming")
    description = data.get("description", "").strip()

    if not code or not title:
        return jsonify({"success": False, "message": "Course code and title are required"}), 400

    existing = Course.query.filter_by(code=code).first()
    if existing:
        return jsonify({"success": False, "message": "Course code already exists"}), 400

    course = Course(
        code=code,
        title=title,
        domain=domain,
        description=description,
        lecturer_id=current_user.id,
        is_available=False
    )
    db.session.add(course)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Course {code} created successfully!",
        "course_id": course.id
    })


@course_bp.route("/toggle/<int:course_id>", methods=["POST"])
@login_required
@lecturer_required
def toggle_course(course_id):
    course = Course.query.filter_by(
        id=course_id, lecturer_id=current_user.id
    ).first_or_404()

    course.is_available = not course.is_available
    db.session.commit()

    status = "available" if course.is_available else "hidden"
    return jsonify({
        "success": True,
        "message": f"Course is now {status}",
        "is_available": course.is_available
    })


@course_bp.route("/delete/<int:course_id>", methods=["DELETE"])
@login_required
@lecturer_required
def delete_course(course_id):
    course = Course.query.filter_by(
        id=course_id, lecturer_id=current_user.id
    ).first_or_404()

    db.session.delete(course)
    db.session.commit()

    return jsonify({"success": True, "message": "Course deleted successfully"})


@course_bp.route("/students/<int:course_id>", methods=["GET"])
@login_required
@lecturer_required
def course_students(course_id):
    course = Course.query.filter_by(
        id=course_id, lecturer_id=current_user.id
    ).first_or_404()

    enrollments = Enrollment.query.filter_by(
        course_id=course_id, status="enrolled"
    ).all()

    return jsonify({
        "course": course.title,
        "students": [{
            "id": e.student.id,
            "name": e.student.full_name,
            "matric_no": e.student.matric_no,
            "email": e.student.email,
            "enrolled_at": e.enrolled_at.strftime("%d %b %Y")
        } for e in enrollments]
    })


@course_bp.route("/remove-student/<int:enrollment_id>", methods=["DELETE"])
@login_required
@lecturer_required
def remove_student(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)

    course = Course.query.filter_by(
        id=enrollment.course_id, lecturer_id=current_user.id
    ).first_or_404()

    db.session.delete(enrollment)
    db.session.commit()

    return jsonify({"success": True, "message": "Student removed from course"})


@course_bp.route("/pending/<int:course_id>", methods=["GET"])
@login_required
@lecturer_required
def course_pending(course_id):
    course = Course.query.filter_by(
        id=course_id, lecturer_id=current_user.id
    ).first_or_404()

    pending = Enrollment.query.filter_by(
        course_id=course_id, status="pending"
    ).all()

    return jsonify({
        "course": course.title,
        "pending": [{
            "enrollment_id": e.id,
            "student_id": e.student.id,
            "name": e.student.full_name,
            "matric_no": e.student.matric_no,
            "email": e.student.email,
            "requested_at": e.enrolled_at.strftime("%d %b %Y")
        } for e in pending]
    })


@course_bp.route("/approve/<int:enrollment_id>", methods=["POST"])
@login_required
@lecturer_required
def approve_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)

    course = Course.query.filter_by(
        id=enrollment.course_id, lecturer_id=current_user.id
    ).first_or_404()

    enrollment.status = "enrolled"
    db.session.commit()

    return jsonify({"success": True, "message": "Student approved"})


@course_bp.route("/reject/<int:enrollment_id>", methods=["DELETE"])
@login_required
@lecturer_required
def reject_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)

    course = Course.query.filter_by(
        id=enrollment.course_id, lecturer_id=current_user.id
    ).first_or_404()

    db.session.delete(enrollment)
    db.session.commit()

    return jsonify({"success": True, "message": "Request rejected"})
@course_bp.route("/question-bank", methods=["GET"])
@login_required
@lecturer_required
def question_bank():
    from backend.models.question import Question
    from backend.models.test import Test

    domain = request.args.get("domain", "")
    bloom = request.args.get("bloom", "")
    qtype = request.args.get("type", "")
    status = request.args.get("status", "")
    page = int(request.args.get("page", 1))
    per_page = 10

    query = Question.query.filter_by(lecturer_id=current_user.id)

    if domain:
        query = query.filter_by(domain=domain)
    if bloom:
        query = query.filter_by(bloom_level=bloom)
    if qtype:
        query = query.filter_by(question_type=qtype)
    if status:
        query = query.filter_by(verification_status=status)

    total = query.count()
    questions = query.order_by(Question.created_at.desc())\
        .offset((page - 1) * per_page).limit(per_page).all()

    # Stats
    all_q = Question.query.filter_by(lecturer_id=current_user.id)
    stats = {
        "total": all_q.count(),
        "verified": all_q.filter_by(verification_status="verified").count(),
        "warning": all_q.filter_by(verification_status="warning").count(),
        "failed": all_q.filter_by(verification_status="failed").count()
    }

    return jsonify({
        "questions": [{
            "id": q.id,
            "question_text": q.question_text,
            "domain": q.domain,
            "bloom_level": q.bloom_level,
            "question_type": q.question_type,
            "verification_status": q.verification_status,
            "llm_used": q.llm_used or "unknown",
            "course_id": q.course_id,
            "course_code": q.course.code if q.course else "N/A"
        } for q in questions],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "stats": stats
    })