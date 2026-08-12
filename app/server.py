import traceback
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from .config import MAX_STUDY_TEXT_CHARS, MAX_UPLOAD_BYTES, OUTPUT_DIR, SUPPORTED_UPLOAD_EXTENSIONS, UPLOAD_DIR
from .controller import OrpheusController
from .schemas import ErrorResponse
from .utils import ensure_readable_upload

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def create_app():
    application = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")
    CORS(application)
    return application

app = create_app()
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
controller = None


def get_controller():
    global controller
    if controller is None:
        controller = OrpheusController()
    return controller


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/api/health")
def health():
    current_controller = controller
    return jsonify({
        "success": True,
        "service": "ORPHEUS",
        "status": "online",
        "qwen": bool(current_controller and current_controller.qwen_ready),
        "yue": bool(current_controller and current_controller.yue_ready),
    })


@app.post("/api/generate")
def generate():
    try:
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()
        genre = data.get("genre", "uplifting pop").strip()
        mood = data.get("mood", "energetic").strip()
        language = data.get("language", "English").strip()

        if not text:
            return jsonify({"success": False, "error": "Please provide study material."}), 400
        if len(text) > MAX_STUDY_TEXT_CHARS:
            return jsonify({"success": False, "error": "Study material is too long. Please use 24,000 characters or fewer."}), 400

        result = get_controller().generate(text=text, genre=genre, mood=mood, language=language)
        return jsonify(result)
    except Exception as exc:
        traceback.print_exc()
        error = ErrorResponse(error=public_error(exc)).model_dump()
        return jsonify(error), 500


@app.post("/api/upload")
def upload():
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded."}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"success": False, "error": "Invalid filename."}), 400

        extension = Path(file.filename).suffix.lower()
        if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
            return jsonify({"success": False, "error": f"Unsupported file type: {extension}"}), 400

        save_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{extension}"
        file.save(save_path)
        ensure_readable_upload(save_path)

        genre = request.form.get("genre", "uplifting pop").strip()
        mood = request.form.get("mood", "energetic").strip()
        language = request.form.get("language", "English").strip()

        result = get_controller().generate_from_file(path=save_path, genre=genre, mood=mood, language=language)
        return jsonify(result)
    except Exception as exc:
        traceback.print_exc()
        error = ErrorResponse(error=public_error(exc)).model_dump()
        return jsonify(error), 500


@app.get("/api/audio/<song_id>")
def audio(song_id):
    audio_path = OUTPUT_DIR / f"{song_id}.wav"
    if not audio_path.exists():
        return jsonify({"success": False, "error": "Audio not found."}), 404
    return send_file(audio_path, mimetype="audio/wav")


@app.get("/api/song/<song_id>")
def song(song_id):
    current_controller = controller
    result = current_controller.get_result(song_id) if current_controller is not None else None
    if result is None:
        return jsonify({"success": False, "error": "Song not found."}), 404
    return jsonify(result)


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"success": False, "error": "Upload is too large. Files must be 15 MB or smaller."}), 413


def public_error(exc: Exception) -> str:
    message = str(exc)
    if isinstance(exc, OSError):
        return "ORPHEUS could not read or store that file. Please try a different file."
    if "out of memory" in message.lower():
        return "ORPHEUS ran out of GPU memory while composing the song. Try shorter study material."
    if "YuE" in message:
        return "Music generation could not be completed. Confirm that the official YuE implementation and models are available."
    if "Qwen" in message or "Transformers" in message:
        return "Educational analysis could not be completed. Confirm that Qwen3-VL and its dependencies are available."
    return message or "Generation failed. Please try again."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=False)
