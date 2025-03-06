#!/usr/bin/env python3
from modules.controller import Controller
from modules.view_textual import TextualView
from modules.common import log_msg
from modules.make_examples import make_examples
import os
import sys
import json
from datetime import datetime, date, timedelta

CONFIG_FILE = os.path.expanduser("~/.goalmate_config")

pos_to_id = {}


def process_arguments() -> tuple:
    """
    Process sys.argv to get the necessary parameters, like the database file location.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            goalmate_home = json.load(f).get("GOALMATEHOME")
    else:
        envhome = os.environ.get("GOALMATEHOME")
        if envhome:
            goalmate_home = envhome
        else:
            userhome = os.path.expanduser("~")
            goalmate_home = os.path.join(userhome, ".goalmate_home/")

    reset = False
    if sys.argv[1:]:
        if sys.argv[1] == "XXX":
            reset = True
            db_path = "example.db"
        elif sys.argv[1] == "YYY":
            db_path = "example.db"
        else:
            db_path = sys.argv[1]
    else:
        os.makedirs(goalmate_home, exist_ok=True)
        db_path = os.path.join(goalmate_home, "goalmate.db")

    return goalmate_home, db_path, reset


# Get command-line arguments: Process the command-line arguments to get the database file location
# goalmate_home, backup_dir, log_dir, db_path, reset = process_arguments()
goalmate_home, db_path, reset = process_arguments()


# def make_examples(controller):
#     today = date.today()
#     # start 2 weeks ago and add a goal every other day
#     start = today - timedelta(days=21)
#     dt = start
#     for d in range(8):
#         dt += timedelta(days=2)
#         goal = f"from {dt.strftime('%y-%m-%d')} 3/7d -1"
#         id = controller.add_goal(goal)
#         ct = dt
#         for i in range(8):
#             ct += timedelta(days=2)
#             if ct <= today:
#                 controller.record_completion(id, f"{ct.strftime('%y-%m-%d')} 5p")
#         log_msg(f"added {goal = }, {id = }")
#


def main():
    print(f"Using database: {db_path}, reset: {reset}")
    controller = Controller(db_path, reset=reset)
    if reset:
        make_examples(controller)
        # id = controller.add_goal("one of three minus two 3/7d -2")
        # log_msg(f"goal id: {id}")
        # controller.record_completion(id, "2/25 2p")
        # id = controller.add_goal("two of three minus one 3/7d -1")
        # log_msg(f"goal id: {id}")
        # controller.record_completion(id, "2/25 5p")
        # controller.record_completion(id, "3/2 5p")
        # id = controller.add_goal("less than two 0/7d 2")
        # controller.record_completion(id, "2/25 5p")
        # controller.record_completion(id, "3/2 5p")
        # id = controller.add_goal("whatever 3/7d 1")
        # controller.record_completion(id, "2/25 5p")

    view = TextualView(controller)
    view.run()


if __name__ == "__main__":
    main()
