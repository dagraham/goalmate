# Goal Notes

## Next

- [ ] List completions for a goal

## basics

### goals and notifications

Query which would for a given goal_id, obtain the target, period and created from Goals and from Completions  [completions[-target:]] as current_completions, compute

- now = round(datetime.now().timestamp())  
- available_time = min(now - created, period)
- num_completions = len(current_completions)
- rating = (num_completions / target) * (period / available_time)

and return

- goal_id, name, target, period, created, available_time, num_completions, rating

- Goals
  - id: int
  - name: text
  - target: int
  - period: int (seconds timedelta)
  - created: int (seconds since epoch)

  - if now - created >= period then
  - expected completions = available // period * target
  - actual completions = len([x for x in completions if x >= now - period])

  - report (actual / target) * (period / available) # supposing available > 0

  - If now is the current timestamp, then now - startup is the number of seconds since the goal was created that have been available for completions
  - EC = (now - startup) // (period/target) is the integer number of completions that would be expected in the available time
  - len([x for x in completions if x >= now - period]) is the actual number of completions in the last period
  - If minus is not None and AC < EC - minus, notify
  - If plus is not None and AC > EC + plus, notify

- completions
  - id: int
  - goal_id: int
  - completed: int (seconds since epoch)

Note: 3/7d => target=3, period=7*24*60*60
Expectation: at any moment, 3 completions will have been recorded in the last 7 days.
days:
  1   2   3   4   5   6   7   8   9  10  
|-1-|-1-|-1-|---|---|---|---|---|---|---|
    1+  2+  3+  3+  3+  3+  3   2   1   0

  1   2   3   4   5   6   7   8   9   0   1   2   3   4  
|-1-|---|---|-1-|---|-1-|---|---|---|---|---|---|---|---|
    1+  1+  1+  2+  2+  3+  3   2   2   2   1

  1   2   3   4   5   6   7   8   9   0   1   2   3   4  
|---|-1-|---|-1-|---|-1-|---|---|-1-|---|-1-|---|-1-|---|
    0+  1+  1+  2+  2+  3+  3   3   3   3   3   3   3   3

Expectation: period/target seconds per completion
Suppose "relevant" is a list that begins with "startup" and continues with each of the completed datetimes in ascending order so most recent is last
Then relevant[-history:] is the most recent history completions

- state targets for goals in terms of repetitions per period
  - 2 times per 3 days: 2/3d
  - 3 times per week: 3/w
  - 5 times per 2 weeks: 5/2w
  - with a target of 2/3d, a frequency of 2 per 72 hours or 1 per 36 hours is implied
  - with a target of 3/w, a frequency of 3 per 168 hours or 1 per 56 hours is implied
  - with a target of 5/2w, a frequency of 5 per 336 hours or 1 per 67.2 hours is implied
- expected completions are computed from the target and the time available for completions
  - suppose a goal is created with a target of "2/3d" and thus a frequency of 1 per 36 hours
    - at the time the goal is created, there will have been no time for completions to be recorded
    - after 36 hours, the expectation is that 1 completion recorded
    - after 72 hours, the expectation is that 2 completions are recorded
    - thereafter, the expectation
    - if 5 completions are recorded in the last 336 hours, the goal is met
    - if 4 completions are recorded in the last 336 hours, the goal is not met
    - if 6 completions are recorded in the last 336 hours, the goal is exceeded

>
  S    1   2     3    4     5   N
  |----|---|-----|----|-----|---|

```
```python
# suppose S is the startup datetime of the goal and N is the current datetime 
# suppose h is a list of datetimes starting with S and continuing with each of the completion datetimes for the goal, if any
# let h_ be the last 10 elements from h
h_ = h[-10:]
# note that the period 
avaliable = N - h_[0] 
# has been available for completions since h_[0] and that
num_completions = len(h_) - 1
# have been completed during that period
target = "2/3d"
num_completions, denominator = goal.split("/")
num_periods = int("".join(denominator[:-1])) if len(denominator) > 1 else 1
period = num_periods * parse_td(denominator) # in seconds 
# so the target is num_completions per period
# and the expectation is then for one completion every 
frequency = period / num_completions 
# seconds or for this many completions in the available period
expected_completions = available / frequency∫


```

- state notifications in terms of optional "-" and "+" values
  - with out entries: no notifications
  - with a goal "2/3d" and "- 1": notify if *fewer* than 2-1=1 completions have been recorded in the last 3 days
  - with a goal "5/2w" and "- 2": notify if *fewer* than 5-2=3 completions have been recorded in the last 2 weeks
  - with a goal "3/w" and "+ 1": notify if *more* than 3+1=4 completions have been recorded in the last week

### startup behavior

- when a goal is created, a creation datetime is recorded.
- suppose the goal is "5/2w"
  - initially there will be no completions in the last 2 weeks which would leave a deficit of 5 completions
  -

## Database Design

I need a python file, model.py, for a new application that would use sqlite3 to manage the datastore with this setup:

- Table: goals
  - goal_id: int
  - name: str (unique)
  - last_completion: int (seconds since epoch)
  - mean_interval: int (seconds computed)
  - mean_absolute_deviation: int (seconds computed)
  - begin: int (seconds since epoch computed)
  - next: int (seconds since epoch computed)
  - end: int (seconds since epoch computed)

- Table: Intervals
  - interval_id: int
  - goal_id: int
  - interval: int (seconds)

Database Methods:

- setup_database
- add_goal(name)
- remove_goal(name) and related intervals
- complete_goal(name, completion_datetime: datetime)
  - if there is a last_completion for the goal:
    - add a new interval equal to completion_datetime - last_completion
    - if there are at least 2 intervals
      - update the mean_interval
      - update next = last_completion + mean_interval
    - if there are at least 3 intervals
      - update mean_absolute_deviation
      - update begin = next - 3*mean_absolute_deviation
      - update end = next + 3*mean_absolute_deviation
  - set last_completion = completion_datetime
- list goals
  - goal_id, name, begin, next, end, num_completions
  - order by begin, next, name
- show_goal(name)
  - goal_id, name, last_completion, mean_interval, mean_absolute_deviation, begin, next, end, num_completions

## Entry Design

# Directory Structure

- root
  - modules
    - model.py (already done)
    - controller.py
    - view.py
  goals.py (provisionally done)

# Entry Point

goals.py: (provisional)

  ```python
  from modules.controller import Controller
  from modules.view import ClickView

  def main():
      controller = Controller("example.db")
      view = ClickView(controller)
      view.run()

  if __name__ == "__main__":
      main()
  ```

# Model

model.py: (already done)

  ```python
  import sqlite3
  from sqlite3 import Error

  class DatabaseManager:
      def __init__(self, database_path: str):
          self.database_path = database_path
          self.connection = None
          self.cursor = None
          self.setup_database()

      def setup_database(self):
          try:
              self.connection = sqlite3.connect(self.database_path)
              self.cursor = self.connection.cursor()
              self.cursor.execute(
                  """
                  CREATE TABLE IF NOT EXISTS goals (
                      goal_id INTEGER PRIMARY KEY,
                      name TEXT UNIQUE,
                      last_completion INTEGER,
                      mean_interval INTEGER,
                      mean_absolute_deviation INTEGER,
                      begin INTEGER,
                      next INTEGER,
                      end INTEGER
                  )
                  """
              ...
  ```

# Controller

controller.py: (to be done)

  ```python
  from model import DatabaseManager
  from common import fmt_dt, fmt_td
  from rich.table import Table
  from rich.box import box
  from datetime import datetime 
  import bisect 

  class Controller:
      def __init__(self, database_path: str):
          # Initialize the database manager
          self.db_manager = DatabaseManager(database_path)
          self.tag_to_id = {}  # Maps tag numbers to event IDs
      ...
  ```

# methods to be implemented in Controller

- list_goals()
- show_goal()
- ...

Controller.list_goals():
  goals = self.db_manager.list_goals()

  ```python
  def list_goals(self):
    colors = {
      0: '#0066cc',
      1: '#3385a3',
      2: '#8cba5c',
      3: '#ffff00',
      4: '#ffff00',
      5: '#ffb920',
      6: '#ff8438',
      7: '#ff5050'
    }
    now = round(
      datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    )
    goals = self.db_manager.list_goals()
    if not goals:
      return "No goals found."
    table = Table(
        title=f"goals",
        caption=f"{now.strftime('%Y-%m-%d')}",
        expand=True,
        box=box.HEAVY_EDGE,
    )
    table.add_column("row", justify="center", width=3, style="dim")
    table.add_column("name", width=10, overflow="ellipsis", no_wrap=True)
    table.add_column("last", justify="center", width=8)
    table.add_column("next", justify="center", width=8)
    table.add_column("+/-", justify="center", width=6)

    for idx, goal in enumerate(goals):
      self.tag_to_id[idx] = goal["goal_id"]
      slots = [goal['begin'] + i * goal['mean_absolute_deviation'] for i in range(8)]
      slot_num = bisect.bisect_left(slots, now)
      row_color = colors[slot_num]
      table.add_row(
          str(idx),
          f"[{row_color}]{goal['name']}[/{row_color}]",
          f"[{row_color}]{fmt_dt(goal['last'])}[/{row_color}]",
          f"[{row_color}]{fmt_dt(goal['next'])}[/{row_color}]",
          f"[{row_color}]{fmt_td(3*goal['mean_absolute_deviation'])}[/{row_color}]",
      )
    return table
  ```

Controller.show_goal():

```python
def show_goal(self, tag):
    """
    Process the base26 tag entered by the user.
    """
    goal_id = self.tag_to_id.get(tag, None)
    if not goal_id:
      return [f"There is no item corresponding to tag '{tag}'."]
    details = [f"Tag [{SELECTED_COLOR}]{tag}[/{SELECTED_COLOR}] details"]
    record = self.db_manager.get_goal(goal_id) 
    fields = ["goal_id", "name", "last_completion", "mean_interval", "mean_absolute_deviation", "begin", "next", "end"]
    content = "\n".join(
        f" [cyan]{field}:[/cyan] [white]{value if value is not None else '[dim]NULL[/dim]'}[/white]"
        for field, value in zip(fields, record)
    )
    return details + fields
```

list_goals() and show_goal(name) should return a list of dictionaries with the following keys:

- goal_id
- name
- last_completion
- mean_interval
- mean_absolute_deviation
- begin
- next
- end
- num_completions

## Controller and View Design Thoughts

- keybindings
  - viewing_mode = 'list'
    - 'Q' - quit
    - 'A' - add_goal
    - {tag} - show_goal corresponding to tag and set viewing_mode = 'details'

  - viewing_mode = 'details'
    - 'Q' - quit
    - 'R' - remove_goal (selected goal)
    - 'C' - complete_goal (selected goal)
    - 'U' - update_goal (selected goal)
    - 'L' - list_goals and set viewing_mode = 'list'

colors {
  0: '#0066cc',
  1: '#3385a3',
  2: '#8cba5c',
  3: '#ffff00',
  4: '#ffff00',
  5: '#ffb920',
  6: '#ff8438',
  7: '#ff5050'
}

- display_goals:
  - set viewing_mode = 'list'
  - set selected_goal = None
  - call model.list_goals
  - create a table with the results
    - each row with a tag colored dim that maps to the goal_id
    - with the rest of the row colored corresponding to the status of the goal

```python
now = round(
  datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
)
slots = [begin + i * mean_absolute_deviation for i in range(8)]
slot_num = bisect.bisect_left(slots, now)
row_color = colors[slot_num]
```

- show_goal:
  - activated by pressing the keyboard character corresponding to the tag of a goal
  - set viewing_mode = 'details'
  - set selected_goal = goal_id
  - call model.show_goal(selected_goal)
  - create a table to display the details of the goal
    - goal_id, name, last_completion, mean_interval, mean_absolute_deviation, begin, next, end, num_completions

- add_goal:
  - prompt user for name
  - insure name is unique
  - call model.add_goal(name)

- remove_goal:
  - activated by pressing the keyboard character corresponding to the tag of a goal
  - set viewing_mode = 'details'
  - set selected_goal = goal_id
  - call model.show_goal(selected_goal)
  - create a table to display the details of the goal
    - goal_id, name, last_completion, mean_interval, mean_absolute_deviation, begin, next, end, num_completions

- add_goal:
  - prompt user for name
  - insure name is unique
  - call model.add_goal(name)

- remove_goal:
  - prommpt user for name
  - call model.remove_goal(name)

- complete_goal:
  
Now I need a command line interface, cli.py, that provides a python click interface to the database methods to manage the goals.

CLI Class Methods:

- init: osetup_database
- add_goal: prompt for name, insure unique and call add_goal
