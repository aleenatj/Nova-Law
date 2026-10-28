"""
Engage support form option maps (integer key -> label).
Values are stored in the DB as integers; labels are defined here only.
Use these for validation and display; no DB enum.
"""

# 4. How can we help you ?
HOW_CAN_HELP_OPTIONS = {
    1: "I am having difficulty registering with Engage or logging in",
    2: "I am having difficulty using Engage",
    3: "I cannot access my Engage submission PDF",
    4: "I would like to transfer my Engage submission to my new lawyers",
    5: "Something else",
}

# 5. Are you having trouble with any of the following ?
TROUBLE_WITH_ANY_OPTIONS = {
    1: "I cannot login because my password is not working",
    2: "I’ve registered but I get the message ‘Email not verified’ when trying to log in",
    3: "I have not received my registration authentication email yet",
    4: "Something else"
}

# 6. Are you having trouble navigating through the Engage form ?
TROUBLE_NAVIGATING_ENGAGE_OPTIONS = {
    1: "Yes",
    2: "No",
}

# 7. Which page or section are you stuck on?
SECTION_STUCK_ON_OPTIONS = {
    1: "About You",
    2: "Your Relationship",
    3: "Consent & Declaration",
    4: "Something else"
}

# 8. Is it one of the issues listed below?
ISSUES_LISTED_OPTIONS = {
    1: "I can’t find my Engage PDF",
    2: "The password I am using to open the Engage PDF does not work",
    3: "No, it’s something else"
}

# 10. Has this guidance helped resolve your issue ?
HELPED_RESOLVE_ISSUE_OPTIONS = {
    1: "Yes",
    2: "No",
}