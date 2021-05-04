import csv
import wolframalpha
import keyring
import getpass

from sys import platform

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import time

if platform.startswith('linux') or platform == "darwin":
    from bullet import Bullet
elif platform == "win32":
    from consolemenu import SelectionMenu
else: 
    raise Exception('Unsupported Platform')


def usingWindows():
    """Helper function for determining if user is on Windows platform.

    Returns:
        bool:
            True if using Windows platform, False otherwise.
    """
    return platform == "win32"


def menuChoice(title, options):
    """Helper function for displaying choices to user and getting their selection

    Args:
        title (str):
            The title of the selection menu display
        options (list):
            List of strings to be displayed as options for user to select

    Returns:
        int:
            Chosen option index
    """
    if usingWindows():
        idx = SelectionMenu.get_selection(options, title=title)
    else:
        cli = Bullet(title, options, margin=3, return_index=True)
        _, idx = cli.launch()
    return idx


def chooseCourse(c):
    """Returns course number of chosen course from a list of all courses

    Args:
        c (cornellGrading):
            Instance of cornellGrading

    Returns:
        int:
            Chosen course number
    """
    strs, ids = c.listCourses()
    idx = menuChoice("Choose course", strs)
    return ids[idx]


def chooseAssignment(c):
    """Returns assignment number of chosen assignment from a list of all assignments

    Args:
        c (cornellGrading):
            Instance of cornellGrading

    Returns:
        int:
            Chosen assignment number
    """
    strs, ids = c.listAssignments()
    idx = menuChoice("Choose assignment", strs)
    return ids[idx]


def getAssignment(c, courseNum=None, assignmentNum=None):
    """Locate assignment by course number and assignmner number
    or by finding using a menu.

        Args:
            c (cornellGrading)
                Instance of cornellGrading
            courseNum (int):
                Number of course the assignment is in. Defaults to None.
            assignmentNum (int)
                Number of the assignment. Defaults to None.

        Returns:
            canvasapi.assignment.Assignment:
                The Assignment object

    """
    if not courseNum:
        courseNum = chooseCourse(c)

    c.getCourse(courseNum)
    print(f"Processing course: {c.course}")

    if not assignmentNum:
        assignment = chooseAssignment(c)

    asgn = c.course.get_assignment(assignment)
    print(f"Processing assignment: {asgn}")

    return asgn

def latexQuiz(questions):
    token = keyring.get_password("canvas_wolframalpha_token1", "wolframalpha")
    if token is None:
        token = getpass.getpass("Enter wolfram AppID:\n")
        try:
            client = wolframalpha.Client(token)
            keyring.set_password("canvas_wolframalpha_token1", "wolframalpha", token)
            print("Connected.  Token Saved")
        except InvalidAccessToken:
            print("Could not connect. Token not saved.")
    else:
        client = wolframalpha.Client(token)
    
    answers = []
    for question in questions:
        res = client.query(question)
        answers.append(next(res.results).text)
    return answers

def updateKalturaPermissions(contributorList=[], mediaLink=[]):
    #chrome_options = Options()
    #chrome_options.add_argument("--headless")
    driver = webdriver.Safari()

    driver.get("https://canvas.cornell.edu/login/saml")
    # link = driver.find_element_by_link_text("Cornell NetID")
    # link.click()

    usr_elem = driver.find_element_by_id("netid")
    usr_elem.send_keys(os.environ["NETID"])
    time.sleep(1)
    pss_elem = driver.find_element_by_id("password")
    pss_elem.send_keys(os.environ["PASS"])
    pss_elem.submit()

    time.sleep(7)

    # push = driver.find_element_by_class_name("auth-button positive")
    # push.click()
    driver.find_element_by_css_selector("button.auth-button.positive").click()

    time.sleep(10)

    driver.get("https://canvas.cornell.edu/courses/28673/external_tools/184")

    time.sleep(5)

    link = driver.find_element_by_id("advanced menu button")
    link.click()

    link = driver.find_element_by_id("icon-pencil")
    link.click()

    #driver.close()