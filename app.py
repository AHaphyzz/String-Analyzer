import json

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Boolean
from dotenv import load_dotenv
from collections import Counter
from datetime import datetime, timezone
import os
import hashlib
import re

load_dotenv()

secret_key = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key

database_url = os.getenv("DATABASE_URL", "sqlite:///string-properties.db")


class Base(DeclarativeBase):
    pass


if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)


class StringAnalyzer(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    length: Mapped[int] = mapped_column(Integer, nullable=False)
    is_palindrome: Mapped[bool] = mapped_column(Boolean, nullable=False)
    unique_characters: Mapped[int] = mapped_column(Float, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=True, unique=True)
    character_frequency_map: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


def parse_natural_language(filter_str):
    """parse user's natural language to query parameters"""
    query = {}
    text = filter_str.lower().strip()

    # --- PALINDROME DETECTION ---
    # Matches: "palindrome", "palindromic", "is palindrome", etc.
    if re.search(r"\bpalindrom\w*\b", text):
        query["is_palindrome"] = True

    # --- WORD COUNT DETECTION ---
    # Matches: "single word", "one word", "two words", "3-word string"
    if re.search(r"\b(single|one)\s+word\b", text):
        query["word_count"] = 1
    elif re.search(r"\b(two|2)\s+words?\b", text):
        query["word_count"] = 2
    elif re.search(r"\b(three|3)\s+words?\b", text):
        query["word_count"] = 3

    # --- LENGTH DETECTION ---
    # Matches: "longer than 10", "greater than 15", etc.
    match = re.search(r"(longer|greater)\s+than\s+(\d+)", text)
    if match:
        query["min_length"] = int(match.group(2)) + 1

    match = re.search(r"(shorter|less)\s+than\s+(\d+)", text)
    if match:
        query["max_length"] = int(match.group(2)) - 1

    # --- CHARACTER DETECTION ---
    # Matches: "containing the letter a", "with letter z", etc.
    match = re.search(r"letter\s+([a-z])", text)
    if match:
        query["contains_character"] = match.group(1)

    # --- VOWEL HEURISTIC ---
    # Matches: "first vowel", "contain vowel", etc.
    if re.search(r"(first\s+vowel|a vowel)", text):
        query["contains_character"] = "a"

    return query


@app.route("/strings", methods=["POST"])
def create_string():
    data = request.get_json(force=True)

    if "text" not in data:
        return jsonify({"error": "Missing 'value' field"}), 400

    text = data.get("text", "").strip()

    if not isinstance(text, str):
        return jsonify({"error": "Value must be a string"}), 420

    if db.session.query(StringAnalyzer).filter_by(value=text).first():
        return jsonify({"error": "String already exist"}), 409

    analysis = StringAnalyzer(
        value=text,
        length=len(text),
        word_count=len(text.split()),
        unique_characters=len(set(text)),
        character_frequency_map=json.dumps(dict(Counter(text.lower().replace(" ", "")))),
        is_palindrome=text.lower().replace(" ", "") == text.lower().replace(" ", "")[::-1],
        sha256_hash=hashlib.sha256(text.encode()).hexdigest(),
        created_at=datetime.now(timezone.utc).isoformat()
    )
    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        "id": analysis.id,
        "value": analysis.value,
        "properties": {
            "length": analysis.length,
            "word count": analysis.word_count,
            "is_palindrome": analysis.is_palindrome,
            "unique_characters": analysis.unique_characters,
            "sha265_hash": analysis.sha256_hash,
            "character_frequency_map": json.loads(analysis.character_frequency_map)
        },
        "created_at": analysis.created_at
    }), 201


@app.route("/strings/<string:string_value>", methods=["GET"])
def get_strings(string_value):
    result = db.session.query(StringAnalyzer).filter_by(value=string_value).first()

    if not result:
        return jsonify({"error": "String does not exist in the system"}), 404

    return jsonify({
        "id": result.id,
        "value": result.value,
        "properties": {
            "length": result.length,
            "word count": result.word_count,
            "is_palindrome": result.is_palindrome,
            "unique_characters": result.unique_characters,
            "sha265_hash": result.sha256_hash,
            "character_frequency_map": json.loads(result.character_frequency_map)
        },
        "created_at": result.created_at
    }), 200


@app.route("/all_strings", methods=["GET"])
def get_all_strings():
    all_strings = StringAnalyzer.query.all()
    results = [
        {
            "id": s.id,
            "value": s.value,
            "properties": {
                "length": s.length,
                "word count": s.word_count,
                "is_palindrome": s.is_palindrome,
                "unique_characters": s.unique_characters,
                "sha265_hash": s.sha256_hash,
                "character_frequency_map": json.loads(s.character_frequency_map)
            },
            "created_at": s.created_at
        }
        for s in all_strings
    ]
    return jsonify(results), 200


@app.route("/strings", methods=["GET"])
def filter_strings():
    query = db.session.query(StringAnalyzer)

    params = {
        "is_palindrome": request.args.get("is_palindrome"),
        "min_length": request.args.get("min_length"),
        "max_length": request.args.get("max_length"),
        "word_count": request.args.get("word_count"),
        "contains_character": request.args.get("contains_character")
    }

    errors = []
    # validate param
    if params["is_palindrome"] is not None:
        val = params["is_palindrome"].lower()
        if val not in ["true", "false"]:
            errors.append("is_palindrome must be true or false")

        else:
            params["is_palindrome"] = (val == "true")

    for key in ["min_length", "max_length", "word_count"]:
        if params[key] is not None:
            try:
                params[key] = int(params[key])
            except ValueError:
                errors.append(f"{key} must be integer")

    if (
            params["min_length"] is not None
            and params["max_length"] is not None
            and params["min_length"] > params["max_length"]
    ):
        errors.append("max_length must be greater than min_length")

    if params["contains_character"] is not None:
        if len(params["contains_character"]) != 1:
            errors.append("contains_character must be a single string")

    if errors:
        return jsonify({"error": "Invalid query parameter value or type", "details": errors}), 400

# Dynamic filters
    if params["is_palindrome"] is not None:
        query = query.filter(StringAnalyzer.is_palindrome == params["is_palindrome"])

    if params["min_length"] is not None:
        query = query.filter(StringAnalyzer.length >= params["min_length"])

    if params["max_length"] is not None:
        query = query.filter(StringAnalyzer.length <= params["max_length"])

    if params["word_count"] is not None:
        query = query.filter(StringAnalyzer.word_count == params["word_count"])

    if params["contains_character"] is not None:
        query = query.filter(StringAnalyzer.value.contains(params["contains_character"]))

    results = query.all()
    response = {
        "count": len(results),
        "filter_applied": {k: v for k, v in params.items() if v is not None},
        "data": [{
            "id": r.id,
            "value": r.value,
            "properties": {
                "word_count": r.word_count,
                "length": r.length,
                "is_palindrome": r.is_palindrome,
                "character_frequency_map": json.loads(r.character_frequency_map),
                "unique_character": r.unique_characters,
                "sha256_hash": r.sha256_hash
            },
            "created_at": r.created_at
        }
            for r in results
        ]
    }
    return jsonify(response), 200


@app.route("/strings/filter-by-natural-language", methods=["GET"])
def natural():
    natural_str = request.args.get("query")

    if not natural_str:
        return jsonify({"error": "Unable tp parse natural language query"}), 400

    parsed = parse_natural_language(natural_str)

    if not parsed:
        return jsonify({"error": "Unable to parse natural language query"}), 400

    if "min_length" in parsed and "max_length" in parsed and parsed["min_length"] > parsed["max_length"]:
        return jsonify({"error": "Query parsed but resulted in conflicting filters"}), 422

    # dynamic SQLAlchemy filters
    filters = []

    if "is_palindrome" in parsed:
        filters.append(StringAnalyzer.is_palindrome == parsed["is_palindrome"])
    if "word_count" in parsed:
        filters.append(StringAnalyzer.word_count == parsed["word_count"])
    if "min_length" in parsed:
        filters.append(StringAnalyzer.length >= parsed["min_length"])
    if "max_length" in parsed:
        filters.append(StringAnalyzer.length <= parsed["max_length"])
    if "contains_character" in parsed:
        filters.append(StringAnalyzer.value.contains(parsed["contains_character"]))

    search = db.session.query(StringAnalyzer)
    results = search.filter(*filters).all()

    return jsonify({
        "data": [
            {
                "id": r.id,
                "value": r.value,
                "properties": {
                    "length": r.length,
                    "word_count": r.word_count,
                    "is_palindrome": r.is_palindrome,
                    "unique_characters": r.unique_characters,
                    "sha256_hash": r.sha256_hash,
                    "character_frequency_map": json.loads(r.character_frequency_map),
                },
                "created_at": r.created_at,
            } for r in results
        ],
        "count": len(results),
        "interpreted_query": {
            "original": natural_str,
            "parsed_filters": parsed
        }
    }), 200


@app.route("/strings/<string:string_value>", methods=["DELETE"])
def delete_string(string_value):
    del_results = db.session.query(StringAnalyzer).filter_by(value=string_value).first()

    if not del_results:
        return jsonify({"error": "String does not exist in the system"}), 404

    db.session.delete(del_results)
    db.session.commit()
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
