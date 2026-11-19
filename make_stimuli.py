# make_stimuli.py  -- builds stories.csv from the authors' open R Markdown file.
import os, re, csv

SEARCH_ROOT = r"C:\Users\hp\OneDrive\Documents\Full_R_Project_Code"   # folder that contains the authors' R files (edit if different)
RMD_NAME = "Supplement Analysis Figures.Rmd"
OUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stories.csv")

# Two-choice control answers (correct answer listed first; position is randomised later).
CONTROL = {
    1: ("At a school reunion", "At their old school"),
    2: ("In her living room", "In her son's room"),
    3: ("Directly in front of his office", "In the staff car park"),
    4: ("At his parents' new restaurant", "At a restaurant near his home"),
    5: ("A big box of sweets", "A souvenir from her vacation"),
    6: ("Emma", "Gareth"),
}
def find_rmd(root):
    for folder, _, files in os.walk(root):
        if RMD_NAME in files:
            return os.path.join(folder, RMD_NAME)
    raise FileNotFoundError("Could not find " + RMD_NAME + " under " + root)

def parse_block(text, start_marker, end_marker):
    a = text.index(start_marker)
    b = text.index(end_marker, a)
    block = text[a:b]
    return re.findall(r'sprintf\("(.*?)"\)', block, flags=re.S)

def clean(s):
    return s.replace("\\n", "\n").replace("**", "")

def split_item(raw):
    s = clean(raw)
    parts = [p.strip() for p in s.split("\n\n") if p.strip()]
    idx = next(i for i, p in enumerate(parts) if p.startswith("In the story did someone"))
    story = parts[idx - 1]
    questions = [p for p in parts[idx:] if p.endswith("?")]
    control_q = questions[2]
    tom_q = questions[3]
    story = re.sub(r"^When I.ve finished telling it I will ask you some questions about what happened in the story\s*", "", story).strip()
    return story, control_q, tom_q

def main():
    path = find_rmd(SEARCH_ROOT)
    print("Using:", path)
    text = open(path, encoding="utf-8").read()
    a = text.index("fp_table <- tibble(")
    seg = text[a:]
    fp_raw = parse_block(seg, "FauxPas = c(", "Neutral = c(")
    ki_raw = parse_block(seg, "KnowledgeImplied = c(", "```")
    assert len(fp_raw) == 6 and len(ki_raw) == 6, (len(fp_raw), len(ki_raw))
    rows = []
    for version, raws, tom_correct in (("FauxPas", fp_raw, "didn't know"), ("KnowledgeImplied", ki_raw, "knew")):
        for i, raw in enumerate(raws, start=1):
            story, cq, tq = split_item(raw)
            rows.append(dict(story_id=i, version=version, story_text=story,
                             control_q=cq, control_correct=CONTROL[i][0], control_wrong=CONTROL[i][1],
                             tom_q=tq, tom_correct=tom_correct))
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("Wrote", OUT_CSV, "with", len(rows), "rows")

main()