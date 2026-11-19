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
    "Each question