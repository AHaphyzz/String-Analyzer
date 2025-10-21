import json

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Boolean
from dotenv import load_dotenv
from collections import Counter
from datetime import datetime, timezone
import os
import hashlib

load_dotenv()

secret_key = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key


class Base(DeclarativeBase):
    pass


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///string-properties.db"
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


@app.route("/strings", methods=["POST"])
def create_string():
    data = request.get_json(force=True)

    if "text" not in data:
        return jsonify({"error": "Missing 'value' field"}, 400)

    text = data.get("text", "").strip()

    if not isinstance(text, str):
        return jsonify({"error": "Value must be a string"}, 420)

    if db.session.query(StringAnalyzer).filter_by(value=text).first():
        return jsonify({"error": "String already exist"}, 409)

    analysis = StringAnalyzer(
        value=text,
        length=len(text),
        word_count=len(text.split()),
        unique_characters=len(set(text)),
        character_frequency_map=json.dumps(dict(Counter(text))),
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
    }, 201)


@app.route("/strings/<string:string_value>", methods=["GET"])
def get_str(string_value):
    result = db.session.query(StringAnalyzer).filter_by(value=string_value).first()

    if not result:
        return jsonify({"error": "String does not exist in the system"}, 404)

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
    }, 200)


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


@app.route("/strings/<string:string_value>", methods=["DELETE"])
def delete_str(string_value):
    del_results = db.session.query(StringAnalyzer).filter_by(value=string_value).first()

    if not del_results:
        return jsonify({"error": "String does not exist in the system"}), 404

    db.session.delete(del_results)
    db.session.commit()
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
