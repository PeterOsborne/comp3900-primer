from flask import Flask, jsonify, request
from flask_cors import CORS

import db

app = Flask(__name__)
CORS(app)

# Helpers

def err(msg: str, code: int = 404):
    # Spec says "for simplicity all errors return 404"
    return jsonify({"error": msg}), code


def parse_mark(value):
    """
    Accept mark as int/float/string; allow None.
    Enforce 0..100 inclusive.
    Returns int or raises ValueError.
    """
    if value is None:
        return None
    try:
        # int("50"), int(50.0) etc. (but reject booleans)
        if isinstance(value, bool):
            raise ValueError("mark must be a number")
        m = int(float(value))
    except Exception:
        raise ValueError("mark must be a number")
    if m < 0 or m > 100:
        raise ValueError("mark must be between 0 and 100")
    return m


def get_json():
    if not request.is_json:
        return None
    return request.get_json(silent=True)


@app.route("/students")
def get_students():
    """
    Fetch all students from the database.
    return: Array of student objects
    """
    students = db.get_all_students()
    return jsonify(students), 200


@app.route("/students", methods=["POST"])
def create_student():
    """
    Create a student with name, course, optionally mark.
    Return created student.
    """
    data = get_json()
    if data is None:
        return err("Expected JSON body")

    name = (data.get("name") or "").strip()
    course = (data.get("course") or "").strip()

    if not name:
        return err("Missing or empty 'name'")
    if not course:
        return err("Missing or empty 'course'")

    # Edge-case choice: if mark omitted/null/empty -> default to 0
    raw_mark = data.get("mark", None)
    if raw_mark in ("", None):
        mark = 0
    else:
        try:
            mark = parse_mark(raw_mark)
        except ValueError as e:
            return err(str(e))

    created = db.insert_student(name=name, course=course, mark=mark)
    return jsonify(created), 200


@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """
    Update student details by id.
    Return 404 if id does not exist.
    """
    data = get_json()
    if data is None:
        return err("Expected JSON body")

    # allow partial updates; db.update_student handles None by keeping existing values
    name = data.get("name", None)
    course = data.get("course", None)
    mark_raw = data.get("mark", None)

    if name is not None:
        name = str(name).strip()
    if course is not None:
        course = str(course).strip()

    mark = None
    if "mark" in data:
        # If mark present but null/"" -> treat as invalid (edge-case choice)
        if mark_raw in ("", None):
            return err("mark cannot be empty; omit the field to keep existing mark")
        try:
            mark = parse_mark(mark_raw)
        except ValueError as e:
            return err(str(e))

    updated = db.update_student(student_id, name=name, course=course, mark=mark)
    if not updated:
        return err(f"Student {student_id} not found")
    return jsonify(updated), 200


@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    """
    Delete student by id. Return deleted student id object.
    """
    deleted = db.delete_student(student_id)
    if not deleted:
        return err(f"Student {student_id} not found")
    return jsonify(deleted), 200


@app.route("/stats")
def get_stats():
    """
    Return count, average, min, max of all student marks.
    """
    students = db.get_all_students()
    marks = [s.get("mark") for s in students if s.get("mark") is not None]

    if not marks:
        # Edge-case choice: empty set -> zeros but still 200
        return jsonify({"count": 0, "average": 0, "min": 0, "max": 0}), 200

    count = len(marks)
    total = sum(marks)
    avg = total / count

    return jsonify(
        {
            "count": count,
            "average": avg,
            "min": min(marks),
            "max": max(marks),
        }
    ), 200


@app.route("/")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)