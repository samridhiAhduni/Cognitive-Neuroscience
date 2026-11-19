# faux_pas_task.py -- Faux pas task with a matched factual (non-ToM) control question
import csv, os, random
from datetime import datetime
from psychopy import visual, core, event, gui

# ----------------------- SETTINGS (change these while piloting) -----------------------
FULLSCR = False                          # set True for real data collection
STORY_VISIBLE_DURING_QUESTIONS = False   # False = story disappears before the questions
FIXATION_SEC = 0.5
TEXT_HEIGHT = 0.04
WRAP = 1.2
BG = 'black'
FG = 'white'
STORIES_CSV = 'stories.csv'
# --------------------------------------------------------------------------------------

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
    tom_correct="knew")
END_PRACTICE = "That was the practice.\n\nThe real task starts now. You will not be told whether your answers are right.\n\nPress SPACE to begin."
END_TEXT = "Thank you, you have finished.\n\nPlease tell the experimenter."

def load_rows():
    with open(os.path.join(THIS_DIR, STORIES_CSV), newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def build_trials(rows, pid):
    """Each participant gets each of the 6 stories once. The version alternates by participant
    number, so every person sees 3 Faux Pas and 3 Knowledge-Implied stories."""
    lookup = {(int(r['story_id']), r['version']): r for r in rows}
    trials = []
    for s in range(1, 7):
        version = 'FauxPas' if (pid + s) % 2 == 0 else 'KnowledgeImplied'
        trials.append(lookup[(s, version)])
    random.shuffle(trials)
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
    """Self-paced reading. Returns reading time in seconds."""
    stim = visual.TextStim(win, text=text, height=TEXT_HEIGHT, wrapWidth=WRAP, color=FG)
    hint = visual.TextStim(win, text="Press SPACE when you have finished reading",
                           height=0.03, color='gray', pos=(0, -0.42))
    clock = core.Clock()
    stim.draw()
    hint.draw()
    win.callOnFlip(clock.reset)
    win.flip()
    event.clearEvents()
    keys = event.waitKeys(keyList=['space', 'escape'], timeStamped=clock)
    if keys[0][0] == 'escape':
        quit_now(win)
    return keys[0][1]

def ask(win, question, correct_label, wrong_label, story_text=None):
    """Two-choice question, positions randomised. Returns (chosen, correct_side, rt, is_correct)."""
    correct_side = random.choice(['left', 'right'])
    labels = {correct_side: correct_label,
              ('right' if correct_side == 'left' else 'left'): wrong_label}
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
    return chosen, correct_side, rt, int(chosen == correct_label)

def fixation(win):
    visual.TextStim(win, text='+', height=0.08, color=FG).draw()
    win.flip()
    core.wait(FIXATION_SEC)

def run_trial(win, row, trial_no, writer, fh, pid, feedback=False):
    fixation(win)
    reading_time = read_story(win, row['story_text'])
    story_for_q = row['story_text'] if STORY_VISIBLE_DURING_QUESTIONS else None
    stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Question 1: factual control question (always first). Question 2: belief (ToM) question.
    questions = [
        ('control', row['control_q'], row['control_correct'], row['control_wrong']),
        ('tom', row['tom_q'], row['tom_correct'],
         "knew" if row['tom_correct'] == "didn't know" else "didn't know"),
    ]
    for qtype, qtext, correct, wrong in questions:
        chosen, correct_side, rt, ok = ask(win, qtext, correct.capitalize(), wrong.capitalize(), story_for_q)
        writer.writerow(dict(participant=pid, trial=trial_no, story_id=row['story_id'],
                             version=row['version'], question_type=qtype, question=qtext,
                             response=chosen, correct_answer=correct.capitalize(),
                             correct=ok, rt=round(rt, 4), reading_time=round(reading_time, 3),
                             correct_side=correct_side, timestamp=stamp))
        fh.flush()
        if feedback:
            show_text(win, "Correct!" if ok else "Not quite.", key='space')

FIELDS = ['participant', 'trial', 'story_id', 'version', 'question_type', 'question', 'response',
          'correct_answer', 'correct', 'rt', 'reading_time', 'correct_side', 'timestamp']

def main():
    info = {'participant': ''}
    dlg = gui.DlgFromDict(dictionary=info, title='Faux pas task')
    if not dlg.OK:
        core.quit()
    pid = int(info['participant'])
    rows = load_rows()
    trials = build_trials(rows, pid)

    os.makedirs(os.path.join(THIS_DIR, 'data'), exist_ok=True)
    fname = os.path.join(THIS_DIR, 'data', 'FP_%d_%s.csv' % (pid, datetime.now().strftime('%Y%m%d_%H%M%S')))
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