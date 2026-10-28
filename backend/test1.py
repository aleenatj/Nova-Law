# from app.db.services.question_answers import get_question_scores_and_results
# from app.db.database import SessionLocal

# db = SessionLocal()

# question_scores_and_results = get_question_scores_and_results(db, 1, [10,5,7,2])
# print(question_scores_and_results)

from app.db.services.general import get_case_summary_for_lawyer
from app.db.database import SessionLocal

db = SessionLocal()

case_summary = get_case_summary_for_lawyer(db, 3)
print(case_summary)