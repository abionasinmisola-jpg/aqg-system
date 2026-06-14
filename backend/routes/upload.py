from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from backend import db
from backend.models.upload import Upload
from backend.routes.lecturer import lecturer_required
import os
import uuid

upload_bp = Blueprint("upload", __name__, url_prefix="/lecturer-portal")

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "pptx", "xlsx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.route("/upload", methods=["POST"])
@login_required
@lecturer_required
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file selected"}), 400

    files = request.files.getlist("file")
    course_id = request.form.get("course_id")
    test_id = request.form.get("test_id")

    if not files:
        return jsonify({"success": False, "message": "No files selected"}), 400

    uploaded = []
    errors = []

    for file in files:
        if file.filename == "":
            continue

        if not allowed_file(file.filename):
            errors.append(f"{file.filename}: Only PDF, DOCX and TXT allowed")
            continue

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            errors.append(f"{file.filename}: File too large (max 10MB)")
            continue

        ext = file.filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"

        upload_folder = os.path.join(current_app.root_path, "..", "static", "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        upload = Upload(
            filename=unique_filename,
            original_name=file.filename,
            file_type=ext,
            file_size=file_size,
            lecturer_id=current_user.id,
            course_id=int(course_id) if course_id else None,
            test_id=int(test_id) if test_id else None,
            status="pending"
        )
        db.session.add(upload)
        uploaded.append(file.filename)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"{len(uploaded)} file(s) uploaded successfully!",
        "uploaded": uploaded,
        "errors": errors
    })


@upload_bp.route("/my-uploads")
@login_required
@lecturer_required
def my_uploads():
    course_id = request.args.get("course_id")

    query = Upload.query.filter_by(lecturer_id=current_user.id)
    if course_id:
        query = query.filter_by(course_id=int(course_id))

    uploads = query.order_by(Upload.uploaded_at.desc()).all()
    return jsonify({
        "uploads": [{
            "id": u.id,
            "filename": u.original_name,
            "file_type": u.file_type,
            "file_size": u.file_size_readable(),
            "status": u.status,
            "uploaded_at": u.uploaded_at.strftime("%d %b %Y %H:%M")
        } for u in uploads]
    })

@upload_bp.route("/delete-upload/<int:id>", methods=["DELETE"])
@login_required
@lecturer_required
def delete_upload(id):
    upload = Upload.query.filter_by(
        id=id, lecturer_id=current_user.id
    ).first_or_404()

    # Delete file from disk
    upload_folder = os.path.join(current_app.root_path, "..", "static", "uploads")
    file_path = os.path.join(upload_folder, upload.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(upload)
    db.session.commit()

    return jsonify({"success": True, "message": "File deleted successfully!"})

from backend.services.processor import process_upload

@upload_bp.route("/process/<int:upload_id>", methods=["POST"])
@login_required
@lecturer_required
def process(upload_id):
    upload = Upload.query.filter_by(
        id=upload_id, lecturer_id=current_user.id
    ).first_or_404()

    if upload.status == "processed":
        return jsonify({"success": True, "message": "File already processed"})

    result = process_upload(upload_id)

    if result["success"]:
        return jsonify({
            "success": True,
            "message": f"Successfully extracted {result['num_chunks']} chunks from {result['filename']}",
            "num_chunks": result["num_chunks"],
            "text_length": result["text_length"]
        })
    else:
        return jsonify({
            "success": False,
            "message": result["message"]
        }), 400

from backend.services.generator import generate_questions as gen_questions
from backend.services.verifier import verify_all_questions
import os

@upload_bp.route("/generate", methods=["POST"])
@login_required
@lecturer_required
def generate():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    upload_id     = data.get("upload_id")
    bloom_level   = data.get("bloom_level", "remember")
    domain        = data.get("domain", "general")
    num_questions = int(data.get("num_questions", 10))
    question_type = data.get("question_type", "mcq")
    llm           = data.get("llm", "mock")

    if not upload_id:
        return jsonify({"success": False, "message": "No file selected"}), 400

    upload = Upload.query.filter_by(
        id=upload_id, lecturer_id=current_user.id
    ).first_or_404()

    index_folder = os.path.join(
        current_app.root_path, "..", "static", "indexes"
    )

    try:
        result = gen_questions(
            upload_id=int(upload_id),
            bloom_level=bloom_level,
            domain=domain,
            num_questions=num_questions,
            question_type=question_type,
            index_folder=index_folder,
            llm=llm
        )
        print(f"Result: {result.get('success')}, LLM: {llm}")

        # Run verification on generated questions
        if result.get("success") and result.get("questions"):
            verification = verify_all_questions(result["questions"])
            result["questions"] = verification["questions"]
            result["verification_stats"] = verification["stats"]

        # Update status to processed
        if result.get("success"):
            upload.status = "processed"
            db.session.commit()

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    
@upload_bp.route("/save-questions", methods=["POST"])
@login_required
@lecturer_required
def save_questions():
    from backend.models.question import Question
    from backend.models.course import Course

    data = request.get_json()
    questions = data.get("questions", [])
    course_id = data.get("course_id")

    if not questions:
        return jsonify({"success": False, "message": "No questions to save"}), 400

    saved = 0
    for q in questions:
        if not q.get("options"):
            continue
        question = Question(
            lecturer_id=current_user.id,
            course_id=course_id if course_id else None,
            question_text=q.get("question", ""),
            option_a=q["options"].get("A", ""),
            option_b=q["options"].get("B", ""),
            option_c=q["options"].get("C", ""),
            option_d=q["options"].get("D", ""),
            correct_answer=q.get("answer", "A"),
            bloom_level=q.get("bloom_level", "remember"),
            domain=q.get("domain", "general"),
            verification_status=q.get("verification_status", "verified"),
            verification_message=q.get("verification_message", ""),
            bloom_aligned=q.get("bloom_aligned", False),
            is_approved=True
        )
        db.session.add(question)
        saved += 1

    db.session.commit()
    return jsonify({"success": True, "message": f"{saved} questions saved to Question Bank!"})


@upload_bp.route("/question-bank")
@login_required
@lecturer_required
def question_bank():
    from backend.models.question import Question
    from backend.models.course import Course

    questions = Question.query.filter_by(
        lecturer_id=current_user.id,
        is_approved=True
    ).order_by(Question.created_at.desc()).all()

    return jsonify({
        "questions": [{
            "id": q.id,
            "question_text": q.question_text,
            "domain": q.domain,
            "bloom_level": q.bloom_level,
            "verification_status": q.verification_status,
            "course_code": q.course.code if q.course else "N/A"
        } for q in questions]
    })


@upload_bp.route("/delete-question/<int:id>", methods=["DELETE"])
@login_required
@lecturer_required
def delete_question(id):
    from backend.models.question import Question

    question = Question.query.filter_by(
        id=id, lecturer_id=current_user.id
    ).first_or_404()

    db.session.delete(question)
    db.session.commit()
    return jsonify({"success": True, "message": "Question deleted"})