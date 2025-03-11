from .__version__ import version as VERSION
from datetime import datetime, timedelta
from dateutil.parser import ParserError

from textual.screen import ModalScreen
from textual.widgets import Label, Button, Static
from textual.containers import Vertical

# from packaging.version import parse as parse_version
from prompt_toolkit.styles.named_colors import NAMED_COLORS
from rich.console import Console
from rich.segment import Segment
from rich.text import Text
from textual.app import App, ComposeResult
from textual.geometry import Size
from textual.reactive import reactive
from textual.screen import Screen
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.widgets import Input
from textual.widgets import Markdown
import re

# from textual.widgets import Label
import string
import shutil

# from textual.widgets import Button
from rich.rule import Rule
from typing import List

# from textual.app import ComposeResult
from textual.containers import Container

# from textual.widgets import Static, Input
from .common import (
    log_msg,
    display_messages,
    COLORS,
    # fmt_dt,
    # fmt_td,
    parse,
    seconds_to_datetime,
    parse_goal_string,
    truncate_string,
)

HEADER_COLOR = NAMED_COLORS["LightSkyBlue"]
TITLE_COLOR = NAMED_COLORS["Cornsilk"]

HelpTitle = f"GoalMate {VERSION}"
HelpText = """\
### Views 
- **List View**:  
  lists the summaries of each goal in the order of when the next completion is likely to be needed. 
- **Details View**:  
  shows the details of a particular goal.

### Key Bindings
- Always available:
    - **Q**: Quit GoalMate   
    - **?**: Show this help screen
    - **S**: Save a screenshot of the current view to a file
- When list view is active:
    - **A**: Add a new goal.
    - **L**: Refresh the list of goals.
    - **a**-**z**: Show the details of the goal tagged with the corresponding letter.
- When details view is displaying a goal:
    - **C**: Complete the goal.
    - **D**: Delete the goal.
    - **E**: Edit the goal.
    - **ESC**: Return to the list view.

### List View Details

When a goal is completed for the first time, GoalMate records the user provided datetime of the completion as the *last* completion datetime. Thereafter, when a goal is completed, GoalMate first prompts for the datetime the goal was actually completed and then prompts for the datetime that the goal actually needed to be completed. Normally these would be the same and, if this is the case, the user can simply press Enter to accept the completion datetime as the value for the needed datetime as well. 

But the completion and needed datetimes are not necessarily the same. If, for example, the goal is to fill the bird feeders when they are empty, then the completion datetime would be when the feeders are filled, but the needed datetime would be when the feeders became empty. Suppose I noticed that the feeders were empty yesterday at 3pm, but I didn't get around to filling them until 10am today. Then I would enter 10am today as the completion datetime in response to the first prompt and 3pm yesterday in response to the second prompt. Alternatively, if I'm going to be away for a while and won't be able to fill the bird feeders while I'm gone and they are currently half full, then I might fill them now in the hope that they will not be emptied before I return. In this case I would use the current moment as the *completion* datetime. But what about the *needed* datetime? Entering a needed datetime would require me to estimate when the feeders would have become empty. While I could do this, I could also just enter "none". Here's how the different responses would be processed by GoalMate:

1. Both completion and needed datetimes are provided (but will be the same if the user accepts the default):

    a. the interval `needed_completion - last_completion` is added to the list of *completion intervals* for this goal.

    b. from this list of *completion intervals*, the mean (average) and two measures of dispersion about the mean are calculated and used to forecast the next completion datetime and to determine the "hotness" color of the goal in the list view.

    c. `last_completion` is updated to the value of the submitted *completion datetime* to set the beginning of the next interval. The mean interval is added to this datetime to get the forecast of the next completion datetime. 

2. A completion datetime and "none" are provided:

    a. skipped

    b. previous mean and dispersion measures are unchanged

    c. `last_completion` is updated to the value of the submitted *completion datetime* to set the beginning of the next interval. The mean interval is added to this datetime to get the forecast of the next completion datetime. 

Submitting "none" for the needed datetime can be used when the user can't be sure when the completion was or will be needed. 


When a goal is completed, GoalMate records the *interval* between this and the previous completion and then updates the value of the last completion. The updated last completion is displayed in the **last** column of the list view. The mean or average of the recorded intervals for the goal is then added to the last completion to get a forecast of when the next completion will likely be needed. This forecast is displayed in the **next** column of the list view. The goals in list view are sorted by **next**.

How good is the **next** forecast? When three or more intervals have been recorded, GoalMate separates the intervals into those that are *less* than the *mean interval* and those that are *more* than the *mean interval*. The average difference between an interval and the *mean interval* is then calculated for *each* of the two groups and labeled *mad_less* and *mad_more*, respectively. The column in the list view labeled **+/-** displays the range from `next - 2 × mad_less` to `next + 2 × mad_more`. The significance of this value is that at least 50% of the recorded intervals must lie within this range - a consquence of *Chebyshev's inequality*.

The goals are diplayed in the list view in one of seven possible colors based on the current datetime.  The diagram below shows the critical datetimes for a goal with `|`'s. The one labeled `N` in the middle corresponds to the value in the *next* column. The others, moving from the far left to the right represent offsets from *next*:  `next - 4 × mad_less`, `next - 3 × mad_less`, and so forth ending with `next + 4 × mad_more`. The numbers below the line represent the Color number used for the different intervals. 

``` 
   -4  -3  -2  -1   N   1   2   3   4 mad offsets
-x--|---|---|---.---|---.-X-|---|---|----> time
  1   2   3         4         5   6   7 colors
            |<---- 1/2 ---->|
        |<-------- 7/9 -------->| 
    |<------------ 7/8 ------------>|
```

If the current datetime is indicated by `x` on the time axis then the goal would be displayed in Color 1. As time and `x` progress to the right, the color changes from 1 to 2 to 3 and so forth. A cool blue is used for Color 1 with the temperature of the color ramping up to yellow for Color 4 and ultimately red for Color 7. 

Suppose at the moment corresponding to `X` that the goal is completed.  With this new interval, the mean interval, mad_less and mad_more will be updated and all the components of the new diagram will be moved a distance corresponding to the new "mean interval" to the right of `X` which will likely put new postion of `X` in the range for Color 1. 

As noted above, the range for Color 4, from -2 to +2 in the diagram, represents at least 1/2 of the recorded intervals so, based on the history of intervals, having Color 4 means that it will likely need to be completed soon. The 1/2 comes from the formula `1 - 2/k^2` where k is the number of mean absolute deviations from the mean which, in this case, means k = 2. For k = 3 and 4, the fractions of the intervals that fall within the range are 7/9 and 7/8, respectively.  
 """.splitlines()


from textual.events import Key  # Import Key explicitly


class ConfirmScreen(ModalScreen):
    """A floating modal confirmation screen for goal deletion, using 'Y' or 'N' keys."""

    def __init__(self, goal_name, on_confirm):
        super().__init__()
        self.goal_name = goal_name
        self.on_confirm = on_confirm  # Callback function when confirmed

    def compose(self):
        """Create a floating confirmation dialog."""
        with Vertical(id="confirm-box"):
            yield Label(
                f"Are you sure you want to delete '{self.goal_name}'?",
                id="confirm-text",
            )
            yield Label(
                "Press 'Y' to confirm or 'N' to cancel.", id="confirm-instructions"
            )

    def on_key(self, event: Key):
        """Handle key events dynamically for uppercase 'Y' and 'N'."""
        if event.character == "Y":  # Detect uppercase Y
            self.dismiss()
            self.on_confirm()
        elif event.character == "N":  # Detect uppercase N
            self.dismiss()

    def on_mount(self):
        """Ensure the modal remains centered and floating."""
        self.styles.layer = "overlay"  # Ensures it floats above everything
        self.styles.align = ("center", "middle")  # Corrected alignment syntax


class AddGoalScreen(ModalScreen):
    """Screen for adding/editing a goal."""

    def __init__(self, controller, goal_id: int | None = None, goal_string: str = ""):
        super().__init__()
        self.controller = controller
        self.goal_id = goal_id
        self.goal_string = goal_string
        # self.goal_name = ""

    def compose(self) -> ComposeResult:
        """Create UI elements with a fixed footer."""
        with Container(id="content"):  # Content container
            yield Static("Enter the new goal:", id="title")
            if self.goal_id:
                yield Input(value=self.goal_string, id="goal_input")
            else:
                yield Input(placeholder="goal name num/period [warn]", id="goal_input")
            yield Static("", id="validation_message")  # Feedback message

        # Footer explicitly placed at the bottom
        yield Static(
            "[bold yellow]Enter[/bold yellow] submit, [bold yellow]ESC[/bold yellow] cancel",
            id="footer",
        )

    def on_mount(self) -> None:
        """Ensure the footer is styled properly."""
        footer = self.query_one("#footer", Static)
        # footer.styles.align = "center"
        footer.styles.margin_top = 1  # Ensures space between content and footer

    def validate_goal(self, goal_input: str) -> str:
        """Check if input is complete and name is unique."""
        match = re.match(
            r"(.+?)(?:\s+(\d+)(?:/(\d+[a-z]))?)?(?:\s+([-+]?\d+))?$",
            goal_input.strip(),
        )
        if not match:
            return "[yellow]Invalid entry: Expected: 'name X/Yz [W]' where name is unique and W is optional.[/yellow]"

        name, target, period, warn = match.groups()
        if name and not self.goal_id and not self.controller.is_goal_unique(name):
            return "[yellow]Goal name must be unique![/yellow]"
        if not target or not period:
            return "[yellow]Invalid entry: Expected: 'name X/Yz [W]' where name is unique and W is optional.[/yellow]"
        return f"[green]Valid goal: {name} {target}/{period} {warn}[/green]"

    def on_input_changed(self, event: Input.Changed) -> None:
        """Validate input and update the feedback message."""
        validation_message = self.query_one("#validation_message", Static)
        validation_message.update(self.validate_goal(event.value))
        self.goal_string = event.value

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key submission."""
        if event.input.id == "goal_input":
            if self.goal_id:
                # updating goal
                self.controller.update_goal(self.goal_id, self.goal_string)
            else:
                # adding goal
                self.controller.add_goal(self.goal_string)
            self.dismiss(self.goal_string)  # Confirm and close

    def on_key(self, event):
        """Handle key presses for cancellation."""
        if event.key == "escape":
            self.dismiss(None)  # Close without adding goal


class DateInputScreen(ModalScreen):
    """Screen for entering a completion datetime."""

    def __init__(
        self,
        controller,
        goal_id,
        goal_name,
        current_datetime: int | None = None,
        prompt="Update completion datetime",
    ):
        super().__init__()
        self.controller = controller
        self.goal_id = goal_id
        self.goal_name = goal_name
        self.prompt = prompt  # Dynamic prompt message
        self.parsed_date = None  # Holds valid parsed datetime
        self.current_datetime = current_datetime
        self.was_escaped = False  # Tracks whether escape was pressed

    def compose(self) -> ComposeResult:
        """Create UI elements with a fixed footer."""
        with Container(id="content"):  # Content container
            yield Static(
                f'Completion for "{self.goal_name}".\n{self.prompt}',
                id="date_title",
            )
            # current_datetime = round(datetime.now().timestamp())
            if self.current_datetime:
                yield Input(
                    value=f"{seconds_to_datetime(self.current_datetime)}",
                    id="date_input",
                )
            else:
                yield Input(
                    placeholder=f"{seconds_to_datetime(self.current_datetime)}",
                    id="date_input",
                )
            yield Static("", id="validation_message")  # Feedback message

        # Footer explicitly placed at the bottom
        yield Static(
            "[bold yellow]Enter[/bold yellow] submit, [bold yellow]ESC[/bold yellow] cancel",
            id="footer",
        )

    def on_mount(self) -> None:
        """Ensure the footer is styled properly."""
        footer = self.query_one("#footer", Static)
        footer.styles.margin_top = 1  # Ensures space between content and footer

    def validate_date(self, date_str: str) -> str:
        """Try to parse the entered date."""
        log_msg(f"{date_str = }")
        try:
            self.parsed_date = parse(date_str)  # Parse the date
            return f"[green]Recognized: {self.parsed_date.strftime('%y-%m-%d %H:%M (%A)')}[/green]"
        except ParserError:
            self.parsed_date = None
            return "[red]Invalid format! Try again.[/red]"

    def on_input_changed(self, event: Input.Changed) -> None:
        """Validate input and update the feedback message."""
        validation_message = self.query_one("#validation_message", Static)
        validation_message.update(self.validate_date(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key submission."""
        log_msg(f"{event.input.id = }, {event.value = }, {self.was_escaped = }")
        if self.was_escaped:  # Prevent handling if escape was pressed
            return

        if event.input.id == "date_input":
            input_value = event.value.strip()
            try:
                parsed_date = parse(input_value)
                self.dismiss(parsed_date)  # Return the parsed datetime
            except ParserError:
                self.dismiss(None)  # Should not happen due to validation

    def on_key(self, event):
        """Handle key presses for cancellation."""
        if event.key == "escape":
            self.was_escaped = True  # Track that escape was pressed
            self.notify("Completion cancelled.", severity="warning")
            log_msg(f"{self.was_escaped = }")
            self.dismiss("_ESCAPED_")  # Return a special marker to detect escape


class DetailsScreen(Screen):
    """A temporary details screen."""

    def __init__(self, details: List[str], markdown: bool = False):
        super().__init__()
        self.markdown = markdown
        self.title = details[0]
        self.lines = details[1:]
        self.footer = [
            "",
            "[bold yellow]L[/bold yellow] list view, [bold yellow]C[/bold yellow] complete, [bold yellow]D[/bold yellow] delete, [bold yellow]E[/bold yellow] edit",
        ]

    def compose(self) -> ComposeResult:
        """Create UI elements with a fixed footer."""

        if self.markdown:
            yield Static(self.title, id="details_title", classes="title-class")
            yield Markdown("\n".join(self.lines), id="details_text")
            yield Static(
                "[bold yellow]ESC[/bold yellow] return to previous display", id="footer"
            )
        else:
            with Container(id="content"):  # Content container
                yield Static(self.title, id="details_title", classes="title-class")
                # yield markdown("\n".join(self.lines), expand=true, id="details_text")
                if self.markdown:
                    yield Markdown("\n".join(self.lines), id="details_text")
                else:
                    yield Static("\n".join(self.lines), id="details_text")

            # Footer explicitly placed at the bottom
            yield Static("\n".join(self.footer), id="footer")

    def on_mount(self) -> None:
        """Ensure the footer is styled properly."""
        footer = self.query_one("#footer", Static)
        # footer.styles.align = "center"
        footer.styles.margin_top = 1  # Ensures space between content and footer

    def on_key(self, event):
        if event.key == "escape":
            self.app.pop_screen()


class ScrollableList(ScrollView):
    """A scrollable list widget with a fixed title and search functionality."""

    def __init__(self, lines: list[str], **kwargs) -> None:
        super().__init__(**kwargs)

        # Extract the title and remaining lines
        # self.title = Text.from_markup(title) if title else Text("Untitled")
        width = shutil.get_terminal_size().columns - 3
        self.lines = [Text.from_markup(line) for line in lines]  # Exclude the title
        self.virtual_size = Size(
            width, len(self.lines)
        )  # Adjust virtual size for lines
        self.console = Console()
        self.search_term = None
        self.matches = []

    def render_line(self, y: int) -> Strip:
        """Render a single line of the list."""
        scroll_x, scroll_y = self.scroll_offset  # Current scroll position
        y += scroll_y  # Adjust for the current vertical scroll offset

        # If the line index is out of bounds, return an empty line
        if y < 0 or y >= len(self.lines):
            return Strip.blank(self.size.width)

        # Get the Rich Text object for the current line
        line_text = self.lines[y].copy()  # Create a copy to apply styles dynamically

        # Highlight the line if it matches the search term
        # if self.search_term and y in self.matches:
        #     line_text.stylize(f"bold {match_color}")  # apply highlighting

        # Render the Rich Text into segments
        segments = list(line_text.render(self.console))

        # Adjust segments for horizontal scrolling
        cropped_segments = Segment.adjust_line_length(
            segments, self.size.width, style=None
        )
        return Strip(
            cropped_segments,
            self.size.width,
        )


class FullScreenList(Screen):
    """Reusable full-screen list for Last, Next, and Find views."""

    def __init__(
        self,
        details: list[str],
        footer_content: str = "[bold yellow]?[/bold yellow] Help",
    ):
        super().__init__()
        if details:
            self.title = details[0]  # First line is the title
            self.lines = details[1:]  # Remaining lines are scrollable content
        else:
            self.title = "Untitled"
            self.lines = []
        self.footer_content = footer_content
        # log_msg(f"FullScreenList: {details[:3] = }")

    def compose(self) -> ComposeResult:
        """Compose the layout."""
        width = shutil.get_terminal_size().columns - 3
        self.virtual_size = Size(width, len(self.lines))
        # log_msg(
        #     f"FullScreenList: {self.title = }, {len(self.title) = },  {self.lines[:3] = }"
        # )
        yield Static(self.title, id="scroll_title", expand=True)
        yield Static(
            Rule("", style="#fff8dc"), id="separator"
        )  # Add a horizontal line separator
        yield ScrollableList(self.lines, id="list")  # Using "list" as the ID
        yield Static(self.footer_content, id="custom_footer")


class TextualView(App):
    """A Textual-based interface for managing goals."""

    CSS_PATH = "view_textual.css"

    digit_buffer = reactive([])  # To store pressed characters for selecting goals
    afill = 1  # Number of characters needed to trigger a tag action

    BINDINGS = [
        ("Q", "quit", "Quit"),
        ("?", "show_help", "Help"),
        ("S", "take_screenshot", "Screenshot"),
        ("L", "show_list", "Show List"),
    ]

    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        self.title = ""
        self.afill = 1
        self.view = "list"  # Initial view is the ScrollableList
        self.selected_goal = None
        self.selected_name = None
        self.selected_tag = None

    def on_mount(self) -> None:
        """Ensure the list of goals appears on startup."""
        self.action_show_list()

    def action_take_screenshot(self):
        """Save a screenshot of the current app state."""
        screenshot_path = f"{self.view}_screenshot.svg"
        self.save_screenshot(screenshot_path)
        self.notify(f"Screenshot saved to: {screenshot_path}", severity="info")

    # def action_add_goal(self):
    #     """Add a new goal."""
    #     self.notify("Adding a new goal...", severity="info")

    def action_add_goal(self):
        """Prompt the user to enter a new goal name."""

        def on_close(goal_name):
            if goal_name:
                self.notify(
                    f"Goal '{goal_name}' added successfully!", severity="success"
                )
                self.action_show_list()  # Refresh the list view
            else:
                self.notify("Goal addition cancelled.", severity="warning")

        self.push_screen(AddGoalScreen(self.controller), callback=on_close)
        # self.push_screen(AddGoalScreen(self.controller))

    def action_update_goal(self):
        """Update the currently selected goal."""
        goal_string = self.controller.get_goal_string(self.selected_goal)

        def on_close(goal_name):
            if goal_name:
                self.notify(
                    f"Goal '{goal_name}' updated successfully!", severity="success"
                )
                self.action_show_list()  # Refresh the list view
            else:
                self.notify("Goal addition cancelled.", severity="warning")

        self.push_screen(
            AddGoalScreen(self.controller, self.selected_goal, goal_string),
            callback=on_close,
        )
        # self.push_screen(AddGoalScreen(self.controller))

    def action_show_list(self):
        """Show the list of goals using FullScreenList."""
        goals = self.controller.show_goals_as_list(
            self.app.size.width
        )  # Fetch goal data
        num_goals = len(goals) - 1
        self.afill = 1 if num_goals < 26 else 2 if num_goals < 676 else 3
        details = goals  # Title + goal data

        self.view = "list"  # Track that we're in the list view
        self.push_screen(FullScreenList(details))

    def action_show_goal(self, tag: str):
        """Show details for a selected goal."""
        result = self.controller.show_goal(tag)
        log_msg(f"{result = }")
        goal_id, name, details, tag_to_idx = result
        self.selected_goal = goal_id
        self.selected_name = name
        self.selected_tag = tag
        self.completion_tag_to_idx = tag_to_idx
        self.view = "details"  # Track that we're in the details view
        self.push_screen(DetailsScreen(details))

    def action_refresh_goal(self):
        """Show details for a selected goal."""
        result = self.controller.show_goal(self.selected_goal)
        log_msg(f"{result = }")
        goal_id, name, details, tag_to_idx = result
        self.view = "details"  # Track that we're in the details view
        self.push_screen(DetailsScreen(details))

    def action_show_goal_history(self):
        """Show the list of goal completions using FullScreenList."""
        goals = self.controller.show_goal_history(self.selected_goal)  # Fetch goal data
        num_goals = len(goals) - 1
        self.afill = 1 if num_goals < 26 else 2 if num_goals < 676 else 3
        details = goals  # Title + goal data

        self.view = "list"  # Track that we're in the list view
        self.push_screen(FullScreenList(details))

    def action_show_help(self):
        """Show the help screen."""
        self.view = "help"
        width = self.app.size.width
        title = f"{HelpTitle:^{width}}"
        title_fmt = f"[bold][{TITLE_COLOR}]{title}[/{TITLE_COLOR}][/bold]"
        self.push_screen(DetailsScreen([title_fmt, *HelpText], True))

    def action_clear_info(self):
        try:
            footer = self.query_one("#custom_footer", Static)
            footer.update("[bold yellow]?[/bold yellow] Help")
        except LookupError:
            log_msg("Footer not found to update.")

    def action_complete_goal(self):
        """Prompt the user for completion datetime."""
        completion_fmt = ""
        if not self.selected_goal:
            self.notify("No goal selected!", severity="warning")
            return

        def on_completion_close(completion_datetime):
            """Handle first datetime input."""
            log_msg(f"{self.selected_goal = }, {completion_datetime = }")
            if completion_datetime is None:
                return  # User canceled

            if isinstance(completion_datetime, datetime):
                completion_datetime = round(completion_datetime.timestamp())
            # ✅ Ensure record_completion is called with all required arguments
            self.controller.record_completion(self.selected_goal, completion_datetime)

            self.notify(
                f'Recorded completion for "{self.selected_name}"',
                severity="success",
            )

            # Refresh the view
            self.action_refresh_goal()

        # ✅ Ensure the first screen passes its result to on_completion_close
        self.push_screen(
            DateInputScreen(
                self.controller,
                self.selected_goal,
                self.selected_name,
                False,
                "Enter the datetime the goal was completed:",
            ),
            callback=on_completion_close,  # ✅ Correctly passing the callback
        )

    def action_update_completion(self, completion_id):
        """Prompt the user for completion datetime."""
        completion_fmt = ""
        completion_timestamp = self.controller.get_completion(completion_id)
        log_msg(f"{completion_timestamp = }")
        if not completion_timestamp:
            self.notify("Could not obtain the current timestamp!", severity="warning")
            return

        def on_completion_close(completion_datetime):
            """Handle datetime input."""
            log_msg(f"{self.selected_goal = }, {completion_datetime = }")
            if completion_datetime is None:
                return  # User canceled

            if isinstance(completion_datetime, datetime):
                completion_datetime = round(completion_datetime.timestamp())
            # ✅ Ensure record_completion is called with all required arguments
            log_msg(f"{completion_id = }, {completion_datetime = }")
            self.controller.update_completion(completion_id, completion_datetime)

            self.notify(
                f'Updated completion for "{self.selected_name}"',
                severity="success",
            )

            # Refresh the view
            self.action_refresh_goal()

        # ✅ Ensure the first screen passes its result to on_completion_close
        self.push_screen(
            DateInputScreen(
                self.controller,
                self.selected_goal,
                self.selected_name,
                completion_timestamp,
                "Enter the datetime the goal was completed:",
            ),
            callback=on_completion_close,  # ✅ Correctly passing the callback
        )

    def action_remove_completion(self, completion_id: int | None = None):
        """Request confirmation before deleting the completion, using 'y' or 'n'."""
        if completion_id is None:
            self.notify("No completion selected.", severity="warning")
            return
        completion_timestamp = self.controller.get_completion(completion_id)
        if not completion_timestamp:
            self.notify("Could not obtain the current timestamp!", severity="warning")
            return

        def confirm_delete():
            log_msg(f"Deleting {completion_id = }, {completion_timestamp = }")
            self.controller.remove_completion(completion_id)
            self.notify(
                f"Deleted completion {seconds_to_datetime(completion_timestamp)} from {self.selected_name}",
                severity="warning",
            )
            self.action_refresh_goal()

        self.push_screen(ConfirmScreen(self.selected_name, confirm_delete))

    def action_remove_goal(self):
        """Request confirmation before deleting the currently selected goal, using 'y' or 'n'."""
        if self.selected_goal is None:
            self.notify("No goal selected.", severity="warning")
            return

        def confirm_delete():
            log_msg(f"Deleting {self.selected_name = }")
            self.controller.remove_goal(self.selected_goal)
            del self.controller.tag_to_id[self.selected_tag]
            self.notify(f"Deleted {self.selected_name}", severity="warning")
            self.action_show_list()

        self.push_screen(ConfirmScreen(self.selected_name, confirm_delete))

    def on_key(self, event):
        """Handle key events based on the current view."""

        if self.view == "list":
            if (
                event.key in string.ascii_lowercase
            ):  # Only allow lowercase a-z for selecting goals
                self.digit_buffer.append(event.key)
                if len(self.digit_buffer) == self.afill:
                    base26_tag = "".join(self.digit_buffer)
                    self.digit_buffer.clear()
                    self.action_show_goal(base26_tag)
            elif event.key == "A":
                self.action_add_goal()
            elif event.key == "L":
                self.action_show_list()
            elif event.key == "Q":
                self.action_quit()
            elif event.key == "?":
                self.action_show_help()

        elif self.view == "details":
            if event.key in ["escape", "L"]:
                self.action_show_list()
            elif event.key == "C":
                self.action_complete_goal()
            elif event.key == "D":
                self.action_remove_goal()
            elif event.key == "E":
                self.action_update_goal()

            # Step 1: Select a completion tag (lowercase letter)
            elif event.key and event.key in self.completion_tag_to_idx:
                self.selected_tag = self.completion_tag_to_idx[
                    event.key
                ]  # Store selected tag
                self.notify(
                    f"Selected completion {self.selected_tag}. Press 'u' to update or 'r' to remove.",
                    severity="info",
                )

            # Step 2: Perform action based on second keypress
            elif self.selected_tag and event.key in ["u", "r"]:
                if event.key == "u":
                    self.action_update_completion(self.selected_tag)
                elif event.key == "r":
                    self.action_remove_completion(self.selected_tag)
                self.selected_tag = None  # Reset after action

        elif self.view == "help":
            if event.key in ["escape", "L"]:
                self.action_show_list()


if __name__ == "__main__":
    pass
