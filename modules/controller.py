from modules.model import DatabaseManager
from rich.table import Table
from rich.box import HEAVY_EDGE
from datetime import datetime
from .common import (
    fmt_dt,
    log_msg,
    seconds_to_time,
    time_to_seconds,
    seconds_to_datetime,
    datetime_to_seconds,
    truncate_string,
    COLORS,
    parse_goal_string,
)


def decimal_to_base26(decimal_num):
    """
    Convert a decimal number to its equivalent base-26 string.

    Args:
        decimal_num (int): The decimal number to convert.

    Returns:
        str: The base-26 representation where 'a' = 0, 'b' = 1, ..., 'z' = 25.
    """
    if decimal_num < 0:
        raise ValueError("Decimal number must be non-negative.")

    if decimal_num == 0:
        return "a"  # Special case for zero

    base26 = ""
    while decimal_num > 0:
        digit = decimal_num % 26
        base26 = chr(digit + ord("a")) + base26  # Map digit to 'a'-'z'
        decimal_num //= 26

    return base26


def base26_to_decimal(base26_num):
    """
    Convert a 2-digit base-26 number to its decimal equivalent.

    Args:
        base26_num (str): A 2-character string in base-26 using 'a' as 0 and 'z' as 25.

    Returns:
        int: The decimal equivalent of the base-26 number.
    """
    # Ensure the input is exactly 2 characters
    if len(base26_num) != 2:
        raise ValueError("Input must be a 2-character base-26 number.")

    # Map each character to its base-26 value
    digit1 = ord(base26_num[0]) - ord("a")  # First character
    digit2 = ord(base26_num[1]) - ord("a")  # Second character

    # Compute the decimal value
    decimal_value = digit1 * 26**1 + digit2 * 26**0

    return decimal_value


def indx_to_tag(indx: int, fill: int = 1):
    """
    Convert an index to a base-26 tag.
    """
    return decimal_to_base26(indx).rjust(fill, "a")


class Controller:
    def __init__(self, database_path: str, reset: bool = False):
        self.db_manager = DatabaseManager(database_path, reset=reset)
        self.tag_to_id = {}
        self.goal_names = []
        self.afill = 1

    def is_goal_unique(self, name: str):
        return name not in self.goal_names

    def show_goals_as_list(self, width: int = 70):
        # row_color = COLORS[2]

        goals = self.db_manager.list_goals()
        log_msg(f"got {goals = }")
        self.afill = 1 if len(goals) < 26 else 2 if len(goals) < 676 else 3
        if not goals:
            return [
                "No goals found.",
            ]

        # 2*2 + 3*1 + 3 + 6*4 = 34 => name width = width - 34
        name_width = width - 30
        table = Table(title="goals", expand=True, box=HEAVY_EDGE)
        table.add_column("row", justify="center", width=3, style="dim")
        table.add_column("name", width=name_width, overflow="ellipsis", no_wrap=True)
        table.add_column("done", justify="center", width=6)
        table.add_column("target", justify="right", width=6)
        table.add_column("period", justify="left", width=6)
        table.add_column("warn", justify="center", width=6)

        results = [
            f"{'row':^3}  {'name':<{name_width}} {'done':^5} {'goal':>5}/{'time':<5} {'warn':^6}",
        ]

        # goal_id: 0,  name: 1, time (period): 2, goal (target): 3, warn: 4, created: 5,
        # done: 6
        self.goal_names = []
        for idx, goal in enumerate(goals):
            self.goal_names.append(goal[1])
            tag = indx_to_tag(idx, self.afill)
            self.tag_to_id[tag] = goal[0]
            name = truncate_string(goal[1], name_width)
            time = seconds_to_time(goal[2]) if isinstance(goal[2], int) else goal[2]
            log_msg(f"{goal[2] = }, {time = }")
            warn = goal[4]
            done = goal[6]
            if warn > 0 and done > goal[3] + warn:
                row_color = COLORS[4]
            elif warn < 0 and done < goal[3] + warn:
                row_color = COLORS[4]
            else:
                row_color = COLORS[2]
            warning = f"{warn:+}" if warn else " "

            row = " ".join(
                [
                    f"[dim]{tag:^3}[/dim]",
                    f" [{row_color}]{name:<{name_width}}[/{row_color}]",
                    f"[{row_color}]{goal[6]:^5}[/{row_color}]",
                    f"[{row_color}]{goal[3]:>4}[/{row_color}]",
                    f"[{row_color}]{' '}[/{row_color}]",
                    f"[{row_color}]{time:<4}[/{row_color}]",
                    f"[{row_color}]{warning:^6}[/{row_color}]",
                ]
            )
            results.append(row)

        return results

    def get_goal_string(self, goal_id):
        record = self.db_manager.show_goal(goal_id)
        if not record:
            return None
        name, time, goal, warn = record[1:5]
        return f"{name} {goal}/{seconds_to_time(time)} {warn}"

    def show_goal(self, goal_id):
        if isinstance(goal_id, str):
            goal_id = self.tag_to_id.get(goal_id)
        if not goal_id:
            return None, None, [f"There is no goal corresponding to tag '{goal_id}'."]

        record = self.db_manager.show_goal(goal_id)
        log_msg(f"got: {goal_id = } => {record = }")
        fields = [
            "goal_id",
            "name",
            "time",
            "goal",
            "warn",
            "created",
            "modified",
            "done",
        ]
        field_hsh = dict(zip(fields, record))
        ordered_fields = [
            "goal_id",
            "name",
            "done",
            "goal",
            "time",
            "warn",
            "created",
            "modified",
        ]
        goal_name = record[1]
        time = seconds_to_time(record[2]) if isinstance(record[2], int) else record[2]
        done = record[7]
        results = [f"[bold][yellow]{goal_name}[/yellow][/bold]"]
        for field in ordered_fields:
            value = field_hsh[field]
            # log_msg(f"{field}: {value}")
            field_fmt = f"[bold #87cefa]{field}[/bold #87cefa]"
            if field in ("created", "modified"):
                value = fmt_dt(value, False) if isinstance(value, int) else value
            elif field in ("time",):
                value = time
            elif field in ("done",):
                value = f"{value} (in the last {time})"
            #     continue
            results.append(f"{field_fmt}: [not bold]{value}[/not bold]")

        # completions = self.db_manager.list_completions(goal_id)
        # if not completions:
        #     results.append("No completions")
        # else:
        completions, tag_to_idx = self.goal_history(goal_id, done)
        results.extend(completions)
        log_msg(f"{goal_id = }, {goal_name = }, {results = }, {tag_to_idx = }")
        return goal_id, goal_name, results, tag_to_idx

    def add_goal(self, goal_str: str, created: int = round(datetime.now().timestamp())):
        # name ... goal:int/period:str
        log_msg(f"parsing: {goal_str = }")
        result = parse_goal_string(goal_str)
        if len(result) == 2:
            log_msg(result[1])
            return None
        log_msg(f"parsed: {goal_str = } => {result = }")
        name, goal, time, warn = result
        time = time_to_seconds(time)
        warn = 0 if goal + warn < 0 else warn

        id = self.db_manager.add_goal(name, time, goal, warn, created)
        return id

    def update_goal(self, goal_id: int, goal_str: str):
        # name ... goal:int/period:str
        log_msg(f"parsing: {goal_str = }")
        result = parse_goal_string(goal_str)
        if len(result) == 2:
            log_msg(result[1])
            return None
        log_msg(f"parsed: {goal_str = } => {result = }")
        name, goal, time, warn = result
        time = time_to_seconds(time)
        warn = 0 if goal + warn < 0 else warn

        id = self.db_manager.update_goal(goal_id, name, time, goal, warn)
        return id

    def goal_history(self, goal_id, done: int = 0):
        completions = self.db_manager.list_completions(goal_id)
        tag_to_idx = {}
        if not completions:
            return ["[bold #87cefa]No completions[/bold #87cefa]", tag_to_idx]
        log_msg(f"{completions = }")

        self.afill = 1 if len(completions) < 26 else 2 if len(completions) < 676 else 3
        table = Table(title="completions", expand=True, box=HEAVY_EDGE)
        table.add_column("row", justify="center", width=3, style="dim")
        table.add_column("completion", no_wrap=True)

        results = [
            "[bold #87cefa]Completions[/bold #87cefa]:",
        ]
        for idx, record in enumerate(completions):
            completion_id, completion = record
            log_msg(f"{idx = }, {done = }, {type(done) = },  {completion = }")
            tag = indx_to_tag(idx, self.afill)
            tag_to_idx[tag] = completion_id
            completion = seconds_to_datetime(completion)
            if idx < done:
                row_color = COLORS[4]
            else:
                row_color = COLORS[1]

            row = " ".join(
                [
                    f" [dim]{tag:^3}[/dim]",
                    f" [{row_color}]{completion:<14}[/{row_color}]",
                ]
            )
            results.append(row)

        return results, tag_to_idx

    def record_completion(
        self,
        goal_id,
        completion_datetime,
    ):
        if type(completion_datetime) is datetime:
            completion_datetime = round(completion_datetime.timestamp())
        elif type(completion_datetime) is str:
            completion_datetime = datetime_to_seconds(completion_datetime)
        log_msg(f"Completing goal {goal_id} at {fmt_dt(completion_datetime)}.")
        self.db_manager.record_completion(goal_id, completion_datetime)
        return f"goal {goal_id} completed successfully."

    def remove_completion(self, completion_id):
        if completion_id:
            log_msg(f"Removing completion {completion_id}.")
            self.db_manager.remove_completion(completion_id)
            return f"completion {completion_id} removed successfully."
        return f"No completion found for goal completion '{completion_id}'."

    def get_completion(self, completion_id):
        completion = self.db_manager.get_completion(completion_id)
        return completion

    def update_completion(self, completion_id, completion_datetime):
        if type(completion_datetime) is datetime:
            completion_datetime = round(completion_datetime.timestamp())
        elif type(completion_datetime) is str:
            completion_datetime = datetime_to_seconds(completion_datetime)
        log_msg(
            f"Updating completion {completion_id} to {fmt_dt(completion_datetime)}."
        )
        self.db_manager.update_completion(completion_id, completion_datetime)
        return f"completion {completion_id} updated successfully."

    def remove_goal(self, goal_id):
        if goal_id:
            log_msg(f"Removing goal {goal_id}.")
            self.db_manager.remove_goal(goal_id)
            return f"goal {goal_id} removed successfully."
        return f"No goal found for tag '{goal_id}'."
