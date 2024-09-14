import os
import logging
from urllib.parse import urljoin
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class SCNotify:
    """Interacts and return information from StudentConnect."""

    DESKTOP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    MOBILE_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"

    def __init__(self, base_domain: str) -> None:
        """Initializes the instance with base domain of the studentconnect.

        Args:
            base_domain (str): URL of the target StudentConnect website
        """
        self.base_domain = base_domain
        self.SC_session = requests.Session()
        self.SC_session.headers.update({"User-Agent": self.DESKTOP_USER_AGENT})
        self.is_logged_in = False
        self.student_id = None

    def login(self, student_id: str, password: str) -> bool:
        """Login to StudentConnect with student credentials.

        Args:
            student_id (str): The student account login
            password (str): The student account password

        Returns:
            bool: Whether the login was successful
        """
        url = urljoin(self.base_domain, "Home/Login")

        login_data = {
            "Pin": student_id,
            "Password": password,
        }

        response = self.SC_session.post(url, data=login_data)

        json_response = response.json()

        logging.info(f"Login response: `{json_response}`")

        if json_response.get("valid") == "1":
            logging.info("Login successful")
            self.is_logged_in = True
            logging.info(f"Set login status: `{self.is_logged_in}`")
            self.student_id = student_id
            logging.info(f"Set active student id: `{self.student_id}`")
            return True

        else:
            logging.error("Login failed")
            return False

    def logged_in(self) -> bool:
        """Checks if student is logged in.

        Returns:
            bool: Whether the student is logged in
        """
        if not self.is_logged_in:
            logging.warning("Student not logged in")
            return False

        return True

    def select_first_track(self) -> None:
        url = urljoin(self.base_domain, "Home/LoadStuMobileList")

        track_page = self.SC_session.get(
            url, headers={"User-Agent": self.MOBILE_USER_AGENT}
        )

        soup = BeautifulSoup(track_page.content, "html.parser")

        track_element = soup.find("a", class_="clsMyStudents")

        href_attr = track_element.get("href")

        if track_id_match := re.findall(r"\d+", href_attr):  # Find all digits
            track_id = track_id_match[0]
            logging.info(f"Found Track ID: `{track_id}`")

            self.select_track(track_id)
        else:
            logging.warning("Could not find Track ID")

    def get_tracks(self) -> list[dict]:
        """Get the student tracks from StudentConnect.

        Returns:
            list[dict]: The track information
        """
        if not self.logged_in():
            return []

        url = urljoin(self.base_domain, "Home/LoadStuMobileList")

        track_page = self.SC_session.get(
            url, headers={"User-Agent": self.MOBILE_USER_AGENT}
        )

        soup = BeautifulSoup(track_page.content, "html.parser")

        track_elements = soup.find_all("a", class_="clsMyStudents")

        track_data_list = []

        for track_element in track_elements:
            student_name = ""
            track_id = None
            track_name = ""
            track_year = None

            if student_name_match := track_element.find_all("b"):  # Get student name
                student_name = student_name_match[0].text.strip()
                logging.info(f"Found student name: `{student_name}`")
            else:
                logging.warning("Could not find student name")

            # Get track id
            # <a ... href="javascript:onClick_Student('2320841')">
            href_attr = track_element.get("href")

            if track_id_match := re.findall(r"\d+", href_attr):  # Find all digits
                track_id = track_id_match[0]
                logging.info(f"Found Track ID: `{track_id}`")
            else:
                logging.warning("Could not find Track ID")

            # Get track name and year
            TRACK_INFO_INDEX = 2

            if track_info_match := track_element.find_all("div")[TRACK_INFO_INDEX]:
                track_info = track_info_match.text.split("\xa0")

                track_name = track_info[0].strip()
                track_year = track_info[1].strip()
                logging.info(f"Found track info: `{track_name} {track_year}`")
            else:
                logging.warning("Could not find track info")

            track_data = {
                "student_name": student_name,
                "track_id": track_id,
                "track_name": track_name,
                "track_year": track_year,
            }

            track_data_list.append(track_data)

        return track_data_list

    def select_track(self, track_id: str) -> None:
        """Set the student track by sending request to StudentConnect website.

        Args:
            track_id (str): The target track id to select
        """
        if not self.logged_in():
            return

        url = urljoin(self.base_domain, f"StudentBanner/SetStudentBanner/{track_id}")
        self.SC_session.get(url)

    def save_snapshot(self) -> None:
        """Saves a copy of the assignment page.
        Creates a new folder based on the student id, then creates a new html
        file named with the current time
        """
        if not self.logged_in():
            return

        url = urljoin(self.base_domain, "Home/LoadProfileData/Assignments")

        # Create new folder for student if not present
        folder_name = self.student_id

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        snapshot_filename = (
            f"assignment-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.html"
        )

        snapshot_path = os.path.join(folder_name, snapshot_filename)

        assignment_page_content = self.SC_session.get(url).content

        with open(snapshot_path, "wb") as assignment_file:
            assignment_file.write(assignment_page_content)

        logging.info(f"Snapshot saved to {snapshot_path}")

    def get_snapshot_list(self) -> list[str]:
        """Gets the snapshots saved.

        Get the list of file located in a folder named to the student id

        Returns:
            list[str]: List of saved snapshot filenames
        """
        folder_name = self.student_id

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        all_snapshots = os.listdir(path=folder_name)

        return sorted(all_snapshots)[::-1]  # sorts by latest

    def get_snapshot_content(self, index: int) -> str:
        """Gets the content of snapshot by index.

        Args:
            index (int): The index of the target snapshot file

        Returns:
            str: The text content of the file
        """
        folder_name = self.student_id

        all_snapshots = self.get_snapshot_list()
        target_snapshot = all_snapshots[index]

        target_path = os.path.join(folder_name, target_snapshot)

        logging.info(f"Getting snapshot: {target_path}")

        with open(target_path, "rb") as file:
            return file.read()

    def parse_assignment(self, assignment_content: str) -> list[dict]:
        """Parse the raw assignment html file to a formatted list.

        Args:
            assignment_content (str): Raw html content of assignments

        Returns:
            list[dict]: List of assignment details
        """
        soup = BeautifulSoup(assignment_content, "html.parser")

        assignment_data_list = []

        for assignment_entry in soup.find_all("tr"):
            assignment_info = {}
            try:
                assignment_detail = assignment_entry.find_all("td")
                assignment_info["due_date"] = assignment_detail[1].text.strip()
                assignment_info["assigned_date"] = assignment_detail[2].text.strip()
                assignment_info["title"] = assignment_detail[3].text.strip()
                assignment_info["total_score"] = assignment_detail[4].text.strip()
                assignment_info["score"] = assignment_detail[5].text.strip()
                assignment_info["extra_credit"] = bool(assignment_detail[7].find("img"))
                assignment_info["not_graded"] = bool(assignment_detail[8].find("img"))
                assignment_info["comments"] = assignment_detail[9].text.strip()

            except AttributeError as e:
                logging.warning(f"Assignment entry missing attribute: {e}")
                continue

            assignment_data_list.append(assignment_info)

        return assignment_data_list

    def parse_snapshot(self, snapshot_content: str) -> list[dict]:
        """Parse the snapshot file and return a couse info list.

        Args:
            snapshot_content (str): The string content of a snapshot file

        Returns:
            list[dict]: The course info and the number of assignment persent
        """
        soup = BeautifulSoup(snapshot_content, "html.parser")

        course_data_list = []

        for course_table in soup.find_all("table"):
            course_info = {}

            try:
                course_caption = course_table.find("caption").text.strip().split("\xa0")
                course_info["course_period"] = course_caption[0].strip().split()[-1]
                course_info["course_name"] = course_caption[-1].strip()
            except AttributeError:
                logging.warning("Course table missing caption (course info)")
                continue  # Skip if caption is missing

            try:
                course_assignments = course_table.find("tbody")
                all_assignments = self.parse_assignment(str(course_assignments))
                course_info["assignments"] = self.remove_duplicate_assignments(
                    all_assignments
                )
            except AttributeError:
                logging.warning("Course table missing tbody (assignment elements)")

            course_data_list.append(course_info)

        return course_data_list

    def remove_duplicate_assignments(self, assignments: list[dict]) -> list[dict]:
        """Remove duplicated assignments with the same title

        Args:
            assignments (list[dict]): List of assignments generated by the self.parse_assignment() method

        Returns:
            list[dict]: List of assignment dictionaries without entries with the same title
        """
        seen = set()
        result = []
        for d in assignments:
            if d["title"] not in seen:
                result.append(d)
                seen.add(d["title"])
        return result

    def compare_assignments(
        self, old_assignments: list[dict], new_assignments: list[dict]
    ) -> list[str]:
        """Compare two lists of assignments and generate message about the change.

        Args:
            old_assignments (list[dict]): A list of dictionaries that consists of assignment information.
            new_assignments (list[dict]): A list of dictionaries that consists of assignment information, possibly differ from old_assignments.

        Returns:
            list[str]: A list of messages describing the change between assignment lists
        """

        messages = []
        # Create a dictionary to store old assignments by title for faster lookup
        old_assignments_by_title = {a["title"]: a for a in old_assignments}

        for new_assignment in new_assignments:
            title = new_assignment["title"]
            if title not in old_assignments_by_title:
                # New assignment added
                score = new_assignment["score"] if new_assignment["score"] else "?"
                total_score = (
                    new_assignment["total_score"]
                    if new_assignment["total_score"]
                    else "?"
                )
                score_caption = f"{score} / {total_score}"
                messages.append(
                    f"New assignment added: `{title}` - **{score_caption}**"
                )

            else:
                old_assignment = old_assignments_by_title[title]
                # Check for changes in each field
                for field in new_assignment:
                    if new_assignment[field] != old_assignment.get(field, None):
                        if field == "comments" and new_assignment[field]:
                            # New assignment comment
                            messages.append(f"Assignment comment added: `{title}`")
                        elif field in ["score", "total_score"]:
                            # Assignment grade changed
                            messages.append(
                                f"Assignment grade changed: `{title}` - **{new_assignment['score']}/{new_assignment['total_score']}**"
                            )
                        else:
                            # Other assignment update (e.g., due date)
                            messages.append(
                                f"Assignment updated: `{title}` - **({field})** : **{new_assignment[field]}**"
                            )

        return messages

    def check_snapshot_change(self) -> list[dict]:
        """Checks two snapshot files for changes.

        Returns:
            A list of changes across two snapshots
        """
        if len(self.get_snapshot_list()) < 2:
            logging.warning(
                f"Not enough snapshot for student `{self.student_id}` to check changes, skipping"
            )
            return None

        snapshot_1_content = self.get_snapshot_content(0)
        snapshot_2_content = self.get_snapshot_content(1)

        snapshot_1 = self.parse_snapshot(snapshot_1_content)
        snapshot_2 = self.parse_snapshot(snapshot_2_content)

        if len(snapshot_1) != len(snapshot_2):
            logging.warning("Course count mismatch between snapshot 1 and 2")
            return [{"message": "Course count mismatch"}]

        results = []

        # Check for difference in assignments
        for course_data_1, course_data_2 in zip(snapshot_1, snapshot_2):
            course_name = course_data_1.get("course_name")
            course_period = course_data_1.get("course_period")

            assignments_1 = course_data_1.get("assignments")
            assignments_2 = course_data_2.get("assignments")

            change_message = self.compare_assignments(assignments_2, assignments_1)
            modified_course_data = {
                "course_name": course_name,
                "course_period": course_period,
                "assignment_changes": change_message,
            }
            results.append(modified_course_data)

        return results

    def logout(self) -> None:
        """Logs student off from Student Connect."""
        if not self.logged_in():
            return

        url = urljoin(self.base_domain, "Home/Logout")
        self.SC_session.get(url)
