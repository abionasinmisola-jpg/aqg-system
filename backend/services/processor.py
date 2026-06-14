import os
from flask import current_app
from backend import db
from backend.models.upload import Upload
from backend.services.extractor import extract_text, chunk_text
from backend.services.embedder import build_faiss_index


def process_upload(upload_id: int) -> dict:
    """
    Process an uploaded file:
    1. Extract text
    2. Clean text
    3. Chunk text
    4. Build FAISS index
    """
    upload = Upload.query.get(upload_id)
    if not upload:
        return {"success": False, "message": "Upload not found"}

    try:
        # Build file path
        upload_folder = os.path.join(
            current_app.root_path, "..", "static", "uploads"
        )
        file_path = os.path.join(upload_folder, upload.filename)

        if not os.path.exists(file_path):
            return {"success": False, "message": "File not found on disk"}

        # Extract text
        text = extract_text(file_path, upload.file_type)

        if not text or len(text.strip()) < 50:
            return {"success": False, "message": "Could not extract enough text from file"}

        # Chunk text
        chunks = chunk_text(text, chunk_size=500, overlap=50)

        # Build FAISS index
        index_folder = os.path.join(
            current_app.root_path, "..", "static", "indexes"
        )
        index_result = build_faiss_index(chunks, upload_id, index_folder)

        # Update upload status
        upload.status = "processed"
        db.session.commit()

        return {
            "success": True,
            "upload_id": upload_id,
            "filename": upload.original_name,
            "text_length": len(text),
            "num_chunks": len(chunks),
            "num_vectors": index_result["num_vectors"],
            "chunks": chunks
        }

    except Exception as e:
        upload.status = "failed"
        db.session.commit()
        return {"success": False, "message": str(e)}