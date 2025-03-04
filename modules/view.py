import click
from modules.common import log_msg
from modules.controller import Controller
from rich.console import Console

console = Console()


class ClickView:
    def __init__(self, controller):
        self.controller = controller
        self.view = "list"
        self.content = None
        self.selected_chore = None
        self.selected_name = None
        self.list_chores()

    def display_content(self):
        console.clear()
        console.print(self.content)

    def list_chores(self):
        self.view = "list"
        self.content = self.controller.show_chores_as_table()
        self.display_content()

    def show_chore(self, tag):
        self.view = "details"
        self.selected_chore, self.selected_name, self.content = (
            self.controller.show_chore(tag)
        )
        self.display_content()

    def handle_input(self):
        while True:
            user_input = click.prompt("", default="", show_default=False).strip()
            log_msg(f"User input: {user_input}")

            if self.view == "list":
                log_msg(f"User input: {user_input}")
                if user_input == "Q":
                    break
                elif user_input in "abcdefghijklmnopqrstuvwxyz":
                    log_msg(f"User selected chore {user_input}.")
                    self.selected_tag = user_input
                    self.show_chore(user_input)
                elif user_input == "A":
                    name = click.prompt("Enter chore name")
                    click.echo(self.controller.add_chore(name))
                elif user_input == "L":
                    self.list_chores()

            elif self.view == "details":
                if user_input == "Q":
                    break
                elif user_input == "C":
                    log_msg(f"Completing chore {self.selected_chore}.")
                    self.controller.complete_chore(self.selected_chore)
                    self.show_chore(self.selected_tag)
                elif user_input == "R":
                    click.echo(
                        self.controller.remove_chore(self.content[0].split()[-1])
                    )
                    self.list_chores()
                elif user_input == "L":
                    self.list_chores()

    def run(self):
        self.handle_input()
