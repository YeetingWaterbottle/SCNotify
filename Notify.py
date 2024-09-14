import requests
import logging


class Notify:
    """Send message through online services."""

    def __init__(self, discord_webhook_url: str = None):
        """Initializes the different target urls.

        Args:
            discord_webhook_url: Discord webhook url. Defaults to None.
        """
        self.discord_webhook_url = discord_webhook_url

    def get_diff_message(self, diff: list[dict]) -> str:
        if not diff:
            logging.info("No assignment changes found")
            return None

        output_message = []

        for item in diff:
            if change_message := item.get("assignment_changes"):
                output_message.append(f"### {item.get('course_name')}")
                for message in change_message:
                    output_message.append(message)

        return "\n".join(output_message)

    def send_discord_webhook(self, message: str, username: str = "SCNotify"):
        """Send message through discord webhook.

        Args:
            message: The message to send
            username: The username for the discord webhook. Defaults to "SCNotify".
        """
        if not self.discord_webhook_url:
            logging.warning("Discord webhook url not set, skipping")
            return

        data = {
            "username": username,
            "content": message,
        }

        requests.post(self.discord_webhook_url, json=data)

