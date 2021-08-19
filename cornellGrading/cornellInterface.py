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
from selenium.webdriver.common.action_chains import ActionChains
import os
import time

from cornellGrading import cornellGrading

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

def updateKalturaPermissions(contributorList=[], mediaNames=[]):
    #chrome_options = Options()
    #chrome_options.add_argument("--headless")

    c = cornellGrading()
    course_number = chooseCourse(c)

    driver = webdriver.Safari()
    driver.get("https://canvas.cornell.edu/login/saml")

    usr_elem = driver.find_element_by_id("username")
    usr_elem.send_keys(os.environ["NETID"])
    time.sleep(1)
    pss_elem = driver.find_element_by_id("password")
    pss_elem.send_keys(os.environ["PASS"])
    driver.find_element_by_name("_eventId_proceed").click()
    #pss_elem.submit()

    print("logged in!")
    time.sleep(7)
    # TODO wait for page to finish loading instead of time.sleep()

    # push = driver.find_element_by_class_name("auth-button positive")
    # push.click()
    
    driver.switch_to_frame("duo_iframe")
    driver.find_element_by_css_selector("button.auth-button.positive").click()

    time.sleep(10)

    media_page = f"https://canvas.cornell.edu/courses/{course_number}/external_tools/184"
    driver.get(media_page)

    time.sleep(4)

    frame = driver.find_element_by_name("tool_content")
    driver.switch_to.frame(frame)
    
    media_elements = driver.find_elements_by_class_name("item_link")
    num_elements   = len(media_elements) // 2
    
    for i in range(num_elements):
        element = media_elements[i]
        link = element.get_attribute("href")
        driver.get(link)
        time.sleep(4)

        edit_element = driver.find_element_by_id("tab-Edit")
        edit_link = edit_element.get_attribute("href")
        driver.get(edit_link)
        time.sleep(4)

        collab_tab_link = driver.find_element_by_id("collaboration-tab")
        collab_tab_link.click()
        time.sleep(1)
        
        verify_text = "add-collaborator"
        candidate_links = driver.find_elements_by_tag_name("a")
        add_collaborator_link = ""
        for a in candidate_links:
            current_link = a.get_attribute("href")
            if current_link != None and verify_text in current_link:
                add_collaborator_link   = current_link
                add_collaborator_button = a
                break
        
        link = driver.find_element_by_link_text('Add Collaborator')
        link.click()
        time.sleep(4)

        permission_buttons = driver.find_elements_by_name("EditEntryCollaborator[permissions][]")
        for button in permission_buttons:
            button.click()

        user_input_field = driver.find_elements_by_class_name("css-1hwfws3")[0]
        user_input_field.click()
        
        
        for collaborator in contributorList:
            ActionChains(driver).send_keys(collaborator).perform()
            time.sleep(1)
            ActionChains(driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
        ActionChains(driver).send_keys(Keys.ENTER).perform()
        
        
        # go back to where we started...
        driver.get(media_page)

    
    #driver.close()