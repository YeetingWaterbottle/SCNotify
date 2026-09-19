# SCNotify

A Python tool that watches a school's StudentConnect grade portal and sends a Discord notification when something changes: a new assignment, an updated score, a new teacher comment, or a changed due date.

StudentConnect has no built-in notifications, so the only way to see a new grade is to log in and check. SCNotify does the checking and posts a summary to a Discord channel, mentioning each subscribed student.

## How it works

1. **Log in.** Starts a `requests` session and signs in with each student's credentials, the same way the portal's login form does.
2. **Select a student track.** Loads the mobile student list, finds the student's track ID, and selects it.
3. **Save a snapshot.** Downloads the assignments page and saves it as a timestamped HTML file in a folder named after the student ID.
4. **Compare.** Parses the two most recent snapshots with BeautifulSoup into per-course assignment lists and compares them field by field.
5. **Notify.** Formats the changes into a message grouped by course and sends it through a Discord webhook, mentioning the student's Discord user.

Example message:

```
@student
### AP Computer Science
New assignment added: `Unit 4 Quiz` - **18 / 20**
Assignment grade changed: `Lab 3` - **47/50**
```

## Project structure

```
SCNotify.py                 Portal client: login, track selection, snapshots, parsing, diffing
Notify.py                   Builds the change message and sends the Discord webhook
main.py                     Runs one check for every account in accounts.json
accounts.json.template      Example account file
```

## Setup

Requirements: Python 3.10+.

```bash
pip install requests beautifulsoup4 python-dotenv
```

1. Copy `accounts.json.template` to `accounts.json` and fill in one entry per student (`id`, `password`, and `discord_id`). This file is in `.gitignore`.
2. Create a `.env` file with your webhook URL:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```
3. Run a check:
   ```bash
   python main.py
   ```

Each run saves one snapshot per student, so notifications start from the second run. To check automatically, schedule `main.py` with cron (Linux) or Task Scheduler (Windows).

## Notes

- Written for the Corona-Norco Unified School District portal. Other districts that use StudentConnect may work after changing the base URL in `main.py`, but the HTML parsing depends on that portal's page layout.
- Credentials are read from local files only and are never committed.
- Built for personal use by students on their own accounts.
