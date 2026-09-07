import re

from slack_bolt.async_app import AsyncApp

from .feedback_buttons import handle_feedback_button
from .issue_buttons import handle_issue_button
from .resolution_buttons import handle_resolution_approve


def register(app: AsyncApp):
    app.action(re.compile(r"^category_"))(handle_issue_button)
    app.action("feedback")(handle_feedback_button)
    app.action("resolution_approve")(handle_resolution_approve)
