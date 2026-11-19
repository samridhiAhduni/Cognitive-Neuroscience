# faux_pas_task_v2.py -- FINAL version (Version 2): faux pas task + matched factual control question
import csv, os, random
from datetime import datetime
from psychopy import visual, core, event, gui

# ----------------------------------- SETTINGS -----------------------------------
FULLSCR = True                           # True for real data collection
STORY_VISIBLE_DURING_QUESTIONS = False   # keep False (story disappears before the questions)
MIN_READ_SEC = 4                         # story cannot be skipped before this many seconds
FIXATION_SEC = 0.5
TEXT_HEIGHT = 0.04
WRAP = 1.2
BG = 'black'
FG = 'white'
STORIES_CSV = 'stories.csv'
DATA_FOLDER = 'data_main'                # pilot data stays in 'data'; main data goes here
SCRIPT_VERSION = 'v2'
# --------------------------------------------------------------------------------

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

INSTRUCTIONS = (
    "Welcome!\n\n"
    "You will read 6 short stories, one at a time. Read each story carefully at your own pace.\n\n"
    "After each story you will answer TWO questions.\n"
    "Each question has two possible answers, one on the left and one on the right.\n"
    "Press the LEFT arrow key to choose the left answer and the RIGHT arrow key to choose the right answer.\n\n"
    "The story will disappear before the questions appear, so read it carefully.\n\n"
    "First there is one practice story.\n\n"
    "Press SPACE to continue."
)
PRACTICE = dict(
    story_id=0, version='Practice',
    story_text=("Tom hid his sister Ella's birthday present in his wardrobe so she would not find it. "
                "While Tom was at school, their mum told Ella that Tom had bought her a present. "
                "When Tom got home, Ella said, 'Thanks for the present, I can't wait to open it!'"),
    control_q="Where did Tom hide the present?",
    control_correct="In his wardrobe", control_wrong="Under his bed",
    tom_q="Is it more likely that Ella knew or didn't know that Tom had bought her a present?",
    tom_correct="knew", control_side='left', tom_side='right')
END_PRACTICE = "That was the practice.\n\nThe real task starts now. You will not be told whether your answers are right.\n\nPress SPACE to begin."
END_TEXT = "Thank you, you have finished.\n\nPlease tell the experimenter."

def load_rows():
    with open(os.path.join(THIS_DIR, STORIES_CSV), newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def build_trials(rows, pid):
    """Each participant sees each of the 6 stories once. Version alternates by participant number
    (3 Faux Pas + 3 Knowledge-Implied per person). Correct answers are on the left in exactly 3 of 6
    trials per question type. Story order is random."""
    lookup = {(int(r['story_id']), r['version']): r for r in rows}
    trials = []
    for s in range(1, 7):
        version = 'FauxPas' if (pid + s) % 2 == 0 else 'KnowledgeImplied'
        trials.append(dict(lookup[(s, version)]))
    random.shuffle(trials)
    control_sides = ['left'] * 3 + ['right'] * 3
    tom_sides = ['left'] * 3 + ['right'] * 3
    random.shuffle(control_sides)
    random.shuffle(tom_sides)
    for t, cs, ts in zip(trials, control_sides, tom_sides):
        t['control_side'] = cs
        t['tom_side'] = ts
    return trials

def quit_now(win):
    win.close()
    core.quit()

def show_text(win, text, key='space', pos=(0, 0), height=TEXT_HEIGHT):
    stim = visual.TextStim(win, text=text, height=height, wrapWidth=WRAP, color=FG, pos=pos)
    stim.draw()
    win.flip()
    event.clearEvents()
    keys = event.waitKeys(keyList=[key, 'escape'])
    if 'escape' in keys:
        quit_now(win)

def read_story(win, text):
    """Self-paced reading with a minimum time. Returns reading time in seconds."""
    stim = visual.TextStim(win, text=text, height=TEXT_HEIGHT, wrapWidth=WRAP, color=FG)
    hint = visual.TextStim(win, text="Press SPACE when you have finished reading",
                           height=0.03, color='gray', pos=(0, -0.42))
    clock = core.Clock()
    stim.draw()
    win.callOnFlip(clock.reset)
    win.flip()
    core.wait(MIN_READ_SEC)
    stim.draw()
    hint.draw()
    win.flip()
    event.clearEvents()
    keys = event.waitKeys(keyList=['space', 'escape'], timeStamped=clock)
    if keys[0][0] == 'escape':
        quit_now(win)
    return keys[0][1]

def ask(win, question, correct_label, wrong_label, correct_side, story_text=None):
    """Two-choice question. Returns (chosen_label, rt, is_correct)."""
    other = 'right' if correct_side == 'left' else 'left'
    labels = {correct_side: correct_label, other: wrong_label}
    if story_text is not None:
        visual.TextStim(win, text=story_text, height=0.03, wrapWidth=WRAP, color='gray',
                        pos=(0, 0.3)).draw()
        q_pos = (0, -0.05)
    else:
        q_pos = (0, 0.15)
    visual.TextStim(win, text=question, height=TEXT_HEIGHT, wrapWidth=WRAP, color=FG, pos=q_pos).draw()
    visual.TextStim(win, text=labels['left'], height=TEXT_HEIGHT, color=FG, pos=(-0.4, -0.2),
                    wrapWidth=0.5).draw()
    visual.TextStim(win, text=labels['right'], height=TEXT_HEIGHT, color=FG, pos=(0.4, -0.2),
                    wrapWidth=0.5).draw()
    visual.TextStim(win, text="LEFT arrow = left answer      RIGHT arrow = right answer",
                    height=0.03, color='gray', pos=(0, -0.42)).draw()
    clock = core.Clock()
    win.callOnFlip(clock.reset)
    win.flip()
    event.clearEvents()
    keys = event.waitKeys(keyList=['left', 'right', 'escape'], timeStamped=clock)
    key, rt = keys[0]
    if key == 'escape':
        quit_now(win)
    chosen = labels[key]
    return chosen, rt, int(chosen == correct_label)

def fixation(win):
    visual.TextStim(win, text='+', height=0.08, color=FG).draw()
    win.flip()
    core.wait(FIXATION_SEC)

def run_trial(win, row, trial_no, writer, fh, pid, feedback=False):
    fixation(win)
    reading_time = read_story(win, row['story_text'])
    story_for_q = row['story_text'] if STORY_VISIBLE_DURING_QUESTIONS else None
    stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tom_wrong = "knew" if row['tom_correct'] == "didn't know" else "didn't know"
    # Question 1: factual control question (always first, as in the paper). Question 2: belief question.
    questions = [
        ('control', row['control_q'], row['control_correct'], row['control_wrong'], row['control_side']),
        ('tom', row['tom_q'], row['tom_correct'], tom_wrong, row['tom_side']),
    ]
    for qtype, qtext, correct, wrong, side in questions:
        chosen, rt, ok = ask(win, qtext, correct.capitalize(), wrong.capitalize(), side, story_for_q)
        writer.writerow(dict(participant=pid, trial=trial_no, story_id=row['story_id'],
                             version=row['version'], question_type=qtype, question=qtext,
                             response=chosen, correct_answer=correct.capitalize(),
                             correct=ok, rt=round(rt, 4), reading_time=round(reading_time, 3),
                             correct_side=side, script_version=SCRIPT_VERSION, timestamp=stamp))
        fh.flush()
        if feedback:
            show_text(win, "Correct!" if ok else "Not quite.", key='space')

FIELDS = ['participant', 'trial', 'story_id', 'version', 'question_type', 'question', 'response',
          'correct_answer', 'correct', 'rt', 'reading_time', 'correct_side', 'script_version', 'timestamp']

def main():
    info = {'participant': ''}
    dlg = gui.DlgFromDict(dictionary=info, title='Faux pas task (v2)')
    if not dlg.OK:
        core.quit()
    pid = int(info['participant'])
    rows = load_rows()
    trials = build_trials(rows, pid)

    os.makedirs(os.path.join(THIS_DIR, DATA_FOLDER), exist_ok=True)
    fname = os.path.join(THIS_DIR, DATA_FOLDER,
                         'FP2_%d_%s.csv' % (pid, datetime.now().strftime('%Y%m%d_%H%M%S')))
    win = visual.Window(fullscr=FULLSCR, color=BG, units='height', allowGUI=False)
    with open(fname, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        show_text(win, INSTRUCTIONS)
        run_trial(win, PRACTICE, 0, writer, fh, pid, feedback=True)
        show_text(win, END_PRACTICE)
        for i, row in enumerate(trials, start=1):
            run_trial(win, row, i, writer, fh, pid, feedback=False)
        show_text(win, END_TEXT)
    win.close()
    core.quit()

if __name__ == '__main__':
    main()