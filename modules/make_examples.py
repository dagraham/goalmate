import random
from datetime import date, timedelta

# from rich import print
# from modules.model import DatabaseManager
# from modules.common import log_msg

# from time import sleep
import lorem
from typing import List


def phrase():
    # for the summary
    # drop the ending period
    s = lorem.sentence()[:-1]
    num = random.choice([2, 3])
    words = s.split(" ")[:num]
    return " ".join(words).rstrip()


def get_name(names: List[str]):
    """Generate a random phrase not belonging to the provided list."""
    name = phrase()
    count = 0
    while name in names and count < 16:
        count += 1
        name = phrase()
    return name


def make_examples(controller, num_goals: int = 14):
    names = []
    today = date.today()
    for _i in range(num_goals):
        name = get_name(names)
        names.append(name)

        freq = random.choice(["w", "d"])
        if freq == "w":
            interval = random.randint(1, 4)
            goal = random.randint(interval, 2 * interval)
            td = timedelta(weeks=interval)
        else:
            interval = random.randint(3, 7)
            goal = random.randint(2, interval)
            td = timedelta(days=interval)
        # warn = random.randint(1 - goal, 0) if goal > 1 else 0
        warn = -1 if goal > 1 else 0
        goal_string = f"{name} {goal}/{interval}{freq} {warn}"
        id = controller.add_goal(goal_string)
        begin = today - 2 * td
        seconds = round(
            td.total_seconds() / goal
        )  # time in seconds for each completion
        for _ in range(2 * goal):
            completion_td = random.randint(round(1 * seconds), round(1.9 * seconds))
            begin += timedelta(seconds=completion_td)
            if begin <= today:
                controller.record_completion(id, begin.strftime("%y-%m-%d %H:%M"))
