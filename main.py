import logging
from SCNotify import SCNotify
from Notify import Notify
import json
import time
import os
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_updates(student_id: str, student_password: str, discord_id: str) -> None:
    student = SCNotify("https://studentconnect.cnusd.k12.ca.us/")
    student.login(student_id, student_password)

    student.select_first_track()

    student.save_snapshot()

    changes = student.check_snapshot_change()

    # print(changes)

    student.logout()

    notify = Notify(discord_webhook_url=DISCORD_WEBHOOK_URL)

    message = notify.get_diff_message(changes)

    if message == "":
        return

    message = f"<@{discord_id}>\n" + message if message else ""

    notify.send_discord_webhook(message)


if __name__ == "__main__":
    load_dotenv()

    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

    accounts = []

    with open("accounts.json", "rt") as file:
        accounts = json.loads(file.read())

    for account in accounts:
        student_id = account["id"]
        student_password = account["password"]
        discord_id = account["discord_id"]

        try:
            get_updates(student_id, student_password, discord_id)
        except:
            logging.error(f"Error Occured, skipping student: {student_id}")

        # time.sleep(10)
