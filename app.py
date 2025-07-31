from flask import Flask, render_template, request, redirect, session, url_for
import itertools
import json
import os
import random
import sys

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key and __name__ == "__main__":
    print("❌ ERROR: SECRET_KEY environment variable is not set.")
    sys.exit(1)

LANG_FILES = {
    "sv": {"name": "Swedish", "file": "data/sv_nouns.jsonl", "lines": 37484},
    "ro": {"name": "Romanian", "file": "data/ro_nouns.jsonl", "lines": 55167},
    "sh": {"name": "Serbo-Croatian", "file": "data/sh_nouns.jsonl", "lines": 16107}
}

def get_valid_declensions(entry):
    return [
        form for form in entry.get("forms", [])
        if (
            form.get("source") == "declension"
            and "form" in form
            and form.get("form") != '-'
        )
    ]

def get_senses(entry):
    """Flatten and return glosses from non-obsolete senses."""
    return list(itertools.chain.from_iterable(
        sense.get("glosses", [])
        for sense in entry.get("senses", [])
    ))

def get_random_noun_entry(lang_code, max_tries=50):
    info = LANG_FILES.get(lang_code)
    if not info:
        return None, []

    file_path = info["file"]
    total_lines = info["lines"]

    for attempt in range(max_tries):
        line_num = random.randint(0, total_lines - 1)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == line_num:
                        entry = json.loads(line)

                        decls = get_valid_declensions(entry)
                        if decls:
                            return entry, decls

                        break
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            continue

    print(f"Failed to find valid entry after {max_tries} attempts")
    return None, []


@app.route("/quiz", methods=["GET"])
def quiz():
    new_lang = request.args.get("lang")
    current_lang = session.get("lang", "sv")

    # If language is explicitly changed, reset the streak
    if new_lang and new_lang != current_lang:
        session["lang"] = new_lang
        session["streak"] = 0
    else:
        session["lang"] = current_lang

    entry, declensions = get_random_noun_entry(session["lang"])
    if not entry or not declensions:
        return "No valid entry found", 500

    form = random.choice(declensions)
    tags = form.get("tags", [])
    senses = get_senses(entry)

    session["quiz"] = {
        "word": entry.get("word"),
        "tags": tags,
        "senses": senses,
        "correct_answer": form["form"]
    }

    return render_template(
        "quiz.html",
        word=entry.get("word"),
        tags=", ".join(tags),
        senses=", ".join(senses),
        feedback=False,
        selected_lang=session["lang"],
        languages=LANG_FILES,
        streak=session.get("streak", 0)
    )


@app.route("/submit", methods=["POST"])
def submit_answer():
    quiz = session.get("quiz")
    if not quiz:
        return redirect(url_for("quiz"))

    user_answer = request.form["user_answer"].strip()
    correct_answer = quiz["correct_answer"]

    is_correct = user_answer.lower() == correct_answer.lower()
    if is_correct:
        session["streak"] = session.get("streak", 0) + 1
    else:
        session["streak"] = 0

    wiktionary_url = f"https://en.wiktionary.org/wiki/{quiz['word']}#{LANG_FILES[session.get('lang', 'sv')]['name']}"

    session.pop("quiz", None)

    return render_template(
        "quiz.html",
        word=quiz["word"],
        tags=", ".join(quiz["tags"]),
        senses=", ".join(quiz["senses"]),
        correct_answer=correct_answer,
        feedback=True,
        is_correct=is_correct,
        user_answer=user_answer,
        wiktionary_url=wiktionary_url,
        selected_lang=session.get('lang', 'sv'),
        languages=LANG_FILES,
        streak=session.get("streak", 0)
    )


@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("quiz"))


if __name__ == "__main__":
    print("Starting declinare")
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT')))

