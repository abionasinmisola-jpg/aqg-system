from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from backend import db
from backend.models.test import Test
from backend.models.question import Question
from backend.models.course import Course
from backend.routes.lecturer import lecturer_required

test_bp = Blueprint("test", __name__, url_prefix="/lecturer-portal/tests")


@test_bp.route("/")
@login_required
@lecturer_required
def my_tests():
    tests = Test.query.filter_by(lecturer_id=current_user.id).all()
    return jsonify({
        "tests": [{
            "id": t.id,
            "title": t.title,
            "course_id": t.course_id,
            "course_code": t.course.code,
            "category": t.category,
            "bloom_level": t.bloom_level,
            "time_limit": t.time_limit,
            "question_count": t.question_count(),
            "is_published": t.is_published
        } for t in tests]
    })

@test_bp.route("/create", methods=["POST"])
@login_required
@lecturer_required
def create_test():
    data = request.get_json()
    title     = data.get("title", "").strip()
    course_id = data.get("course_id")
    time_limit = int(data.get("time_limit", 30))
    bloom     = data.get("bloom_level", "remember")
    category  = data.get("category", "test")

    if not title or not course_id:
        return jsonify({"success": False, "message": "Title and course are required"}), 400

    course = Course.query.filter_by(
        id=course_id, lecturer_id=current_user.id
    ).first_or_404()

    test = Test(
        title=title,
        course_id=course_id,
        lecturer_id=current_user.id,
        bloom_level=bloom,
        domain=course.domain,
        time_limit=time_limit,
        category=category,
        is_published=False
    )
    db.session.add(test)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Test '{title}' created successfully!",
        "test_id": test.id
    })


@test_bp.route("/toggle/<int:test_id>", methods=["POST"])
@login_required
@lecturer_required
def toggle_test(test_id):
    test = Test.query.filter_by(
        id=test_id, lecturer_id=current_user.id
    ).first_or_404()

    test.is_published = not test.is_published
    db.session.commit()

    status = "published" if test.is_published else "unpublished"
    return jsonify({
        "success": True,
        "message": f"Test {status}",
        "is_published": test.is_published
    })


@test_bp.route("/delete/<int:test_id>", methods=["DELETE"])
@login_required
@lecturer_required
def delete_test(test_id):
    test = Test.query.filter_by(
        id=test_id, lecturer_id=current_user.id
    ).first_or_404()

    db.session.delete(test)
    db.session.commit()
    return jsonify({"success": True, "message": "Test deleted"})


@test_bp.route("/add-questions/<int:test_id>", methods=["POST"])
@login_required
@lecturer_required
def add_questions(test_id):
    test = Test.query.filter_by(
        id=test_id, lecturer_id=current_user.id
    ).first_or_404()

    data = request.get_json()
    question_ids = data.get("question_ids", [])

    for qid in question_ids:
        q = Question.query.filter_by(
            id=qid, lecturer_id=current_user.id
        ).first()
        if q:
            q.test_id = test_id

    db.session.commit()
    return jsonify({"success": True, "message": f"{len(question_ids)} questions added to test"})

from flask import current_app
from backend.models.upload import Upload
from backend.services.generator import generate_questions as gen_questions
from backend.services.verifier import verify_all_questions
from backend.services.processor import process_upload
import os


@test_bp.route("/<int:test_id>/uploads", methods=["GET"])
@login_required
@lecturer_required
def test_uploads(test_id):
    test = Test.query.filter_by(id=test_id, lecturer_id=current_user.id).first_or_404()
    uploads = Upload.query.filter_by(test_id=test_id).order_by(Upload.uploaded_at.desc()).all()
    return jsonify({
        "uploads": [{
            "id": u.id,
            "filename": u.original_name,
            "file_type": u.file_type,
            "status": u.status
        } for u in uploads]
    })


@test_bp.route("/<int:test_id>/generate", methods=["POST"])
@login_required
@lecturer_required
def generate_into_test(test_id):
    test = Test.query.filter_by(id=test_id, lecturer_id=current_user.id).first_or_404()
    data = request.get_json()

    upload_id     = data.get("upload_id")
    bloom_level   = data.get("bloom_level", "remember")
    num_questions = int(data.get("num_questions", 10))
    question_type = data.get("question_type", "mcq")
    llm = data.get("llm", "mock")

    if not upload_id:
        return jsonify({"success": False, "message": "Select a note first"}), 400

    upload = Upload.query.filter_by(id=upload_id, lecturer_id=current_user.id).first_or_404()

    # process the note if not already done
    if upload.status != "processed":
        pr = process_upload(int(upload_id))
        if not pr.get("success"):
            return jsonify({"success": False, "message": pr.get("message", "Processing failed")}), 400

    index_folder = os.path.join(current_app.root_path, "..", "static", "indexes")

    result = gen_questions(
        upload_id=int(upload_id),
        bloom_level=bloom_level,
        domain=test.domain,
        num_questions=num_questions,
        question_type=question_type,
        index_folder=index_folder,
        llm=llm
    )

    if not result.get("success"):
        return jsonify(result), 400

    # verify
    verification = verify_all_questions(result["questions"])
    questions = verification["questions"]

    # save straight into this test
    saved = 0
    for q in questions:
        opts = q.get("options", {})
        question = Question(
            test_id=test_id,
            lecturer_id=current_user.id,
            course_id=test.course_id,
            question_text=q.get("question", ""),
            option_a=opts.get("A"),
            option_b=opts.get("B"),
            option_c=opts.get("C"),
            option_d=opts.get("D"),
            correct_answer=str(q.get("answer", "")).lower() if q.get("type") == "fill" else str(q.get("answer", "")),
            question_type=q.get("type", "mcq"),
            llm_used=llm,
            bloom_level=q.get("bloom_level", bloom_level),
            domain=test.domain,
            verification_status=q.get("verification_status", "pending"),
            verification_message=q.get("verification_message", ""),
            bloom_aligned=q.get("bloom_aligned", False),
            is_approved=True
        )
        db.session.add(question)
        saved += 1
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"{saved} question(s) added to test",
        "verification_stats": verification["stats"],
        "saved": saved
    })


@test_bp.route("/<int:test_id>/questions", methods=["GET"])
@login_required
@lecturer_required
def test_questions(test_id):
    test = Test.query.filter_by(id=test_id, lecturer_id=current_user.id).first_or_404()
    questions = Question.query.filter_by(test_id=test_id).order_by(Question.created_at).all()
    return jsonify({
        "test_title": test.title,
        "questions": [{
            "id": q.id,
            "question_text": q.question_text,
            "type": q.question_type,
            "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d} if q.question_type == "mcq" else {},
            "answer": q.correct_answer,
            "bloom_level": q.bloom_level,
            "verification_status": q.verification_status,
            "verification_message": q.verification_message
        } for q in questions]
    })


@test_bp.route("/question/<int:question_id>/remove", methods=["DELETE"])
@login_required
@lecturer_required
def remove_question(question_id):
    q = Question.query.filter_by(id=question_id, lecturer_id=current_user.id).first_or_404()
    db.session.delete(q)
    db.session.commit()
    return jsonify({"success": True, "message": "Question removed"})