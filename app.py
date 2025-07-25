from flask import Flask, render_template, request, redirect, url_for
import itertools
import json
import os
import random
import re
import time

app = Flask(__name__)

LANG_FILES = {
    "sv": {"name": "Swedish", "file": "data/sv_nouns.jsonl", "lines": 37484},
    "ro": {"name": "Romanian", "file": "data/ro_nouns.jsonl", "lines": 55202},
    "sh": {"name": "Serbo-Croatian", "file": "data/sh_nouns.jsonl", "lines": 29093}
}

EXCLUDED_TAGS = {"table-tags", "inflection-template", "archaic", "dated", "obsolete"}

def get_valid_declensions(entry):
    return [
        form for form in entry.get("forms", [])
        if (
            form.get("source") == "declension"
            and "form" in form
            and not set(form.get("tags", [])) & EXCLUDED_TAGS
        )
    ]

def get_senses(entry):
    """Flatten and return glosses from non-obsolete senses."""
    return list(itertools.chain.from_iterable(
        sense.get("glosses", [])
        for sense in entry.get("senses", [])
        if not set(sense.get("tags", [])) & EXCLUDED_TAGS
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

@app.route("/", methods=["GET", "POST"])
def quiz():
    lang = request.form.get("lang") or request.args.get("lang") or "sv"

    if lang not in LANG_FILES:
        lang = "sv"

    if request.method == "POST":
        if "word" in request.form and "correct_answer" in request.form:
            word = request.form["word"]
            correct_answer = request.form["correct_answer"]
            tags = request.form["tags"]
            senses = request.form["senses"]
            user_answer = request.form["user_answer"].strip()

            is_correct = user_answer.lower() == correct_answer.lower()

            return render_template(
                "quiz.html",
                word=word,
                tags=tags,
                senses=senses,
                correct_answer=correct_answer,
                feedback=True,
                is_correct=is_correct,
                user_answer=user_answer,
                selected_lang=lang,
                languages=LANG_FILES
            )
        else:
            # User submitted only a language switch — refresh question
            return redirect(url_for("quiz", lang=lang))

    entry, declensions = get_random_noun_entry(lang)
    if not entry or not declensions:
        return "No valid entry found", 500

    form = random.choice(declensions)
    tags = ", ".join(form.get("tags", []))
    senses = ", ".join(get_senses(entry))
    return render_template(
        "quiz.html",
        word=entry.get("word"),
        tags=tags,
        senses=senses,
        correct_answer=form["form"],
        feedback=False,
        selected_lang=lang,
        languages=LANG_FILES
    )

if __name__ == "__main__":
    print("Starting declinare")
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT')))

