"""
Engage feedback form option maps (integer key -> label).
Values are stored in the DB as integers; labels are defined here only.
Use these for validation and display; no DB enum.
"""

# 1. How do you feel about the length of time it has taken you to complete Engage?
TIME_VALUE_FEEDBACK_OPTIONS = {
    1: "It has been a valuable use of my time",
    2: "It has been an acceptable use of my time",
    3: "It has been a waste of my time",
}

# 2. How long did it take you overall to complete your Engage submission?
COMPLETION_TIME_OPTIONS = {
    1: "30 mins",
    2: "45 mins",
    3: "1 hour",
    4: "1 hour 15 mins",
    5: "1 hour 30 mins",
    6: "2 hours",
    7: "2 hours 30 mins",
    8: "3 hours",
    9: "More than 3 hours",
}

# 3. How many sessions did it take you to complete your Engage submission?
SESSION_COUNT_OPTIONS = {i: str(i) for i in range(1, 11)}  # 1..10

# 4. Which of the following best describes your use of Engage?
HELP_LEVEL_OPTIONS = {
    1: "I completed it without any help",
    2: "I needed a small amount of help to complete Engage",
    3: "I needed a significant amount of help to complete Engage",
    4: "I had somebody else complete Engage on my behalf.",
}

# 4.1 Who helped you with Engage? (multi-select; store as JSON e.g. {"1": "A relative", "2": "..."})
HELPER_TYPE_OPTIONS = {
    1: "A relative",
    2: "A friend or work colleague",
    3: "A court-appointed Litigation Friend",
    4: "A McKenzie friend",
    5: "An advice centre worker or volunteer",
    6: "The technical support helpline at Family Law Lab",
}

# 4.2 Would you be willing to tell us why you needed help completing Engage? (multi-select)
HELP_REASON_OPTIONS = {
    1: "A problem with internet accessibility",
    2: "A problem with my device",
    3: "I didn't understand the questions or the information provided",
    4: "Physical impairment",
    5: "Mental health challenges",
    6: "A short term or long-standing illness",
    7: "Other",
}

# 5. Having used Engage, how prepared do you feel for your legal consultation?
PREPAREDNESS_LEVEL_OPTIONS = {
    1: "Highly prepared",
    2: "Very prepared",
    3: "Prepared",
    4: "Fairly prepared",
    5: "No difference",
}

# 6. Which age range do you fall into?
AGE_RANGE_OPTIONS = {
    1: "18 to 24",
    2: "25 to 34",
    3: "35 to 44",
    4: "45 to 54",
    5: "55 to 64",
    6: "65 to 74",
    7: "75+",
}

# 7. Gender
GENDER_OPTIONS = {
    1: "Female",
    2: "Male",
    3: "I'd rather not say",
    4: "Other",
}

# 8. How would you rate your overall experience of using Engage?
OVERALL_EXPERIENCE_OPTIONS = {
    1: "Highly positive",
    2: "Positive",
    3: "Satisfactory",
    4: "Unsatisfactory",
    5: "Poor",
}

# 9. On a scale of 1 to 10 how likely you recommend Engage (1=least, 10=most)
RECOMMENDATION_SCORE_OPTIONS = {i: str(i) for i in range(1, 11)}  # 1..10
