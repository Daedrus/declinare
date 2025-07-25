import json

def split_by_pos(input_path, lang_code):
    output_files = {
        "noun": open(f"{lang_code}_nouns.jsonl", "w", encoding="utf-8"),
        "verb": open(f"{lang_code}_verbs.jsonl", "w", encoding="utf-8"),
        "adj": open(f"{lang_code}_adjs.jsonl", "w", encoding="utf-8"),
    }

    def is_form_of(entry):
        return any("form_of" in sense for sense in entry.get("senses", []))

    with open(input_path, "r", encoding="utf-8") as infile:
        for line in infile:
            try:
                entry = json.loads(line)

                if (
                    entry.get("lang_code") == lang_code and
                    entry.get("pos") in output_files and
                    not is_form_of(entry)
                ):
                    json.dump(entry, output_files[entry["pos"]], ensure_ascii=False)
                    output_files[entry["pos"]].write("\n")
            except json.JSONDecodeError:
                continue

    for f in output_files.values():
        f.close()

    print("✅ Split complete.")

split_by_pos("data/sv.jsonl", "sv")
split_by_pos("data/ro.jsonl", "ro")
split_by_pos("data/sh.jsonl", "sh")
