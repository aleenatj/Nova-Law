from app.enums.lawyer import AccreditedSpecialismEnum, ExpertiseEnum, RelationshipTypeEnum, MatterTypeEnum

from app.db.database import SessionLocal
from sqlalchemy.orm import joinedload

from app.db.models.lawyer import Lawyer, LawyerExpertise, LawyerAccreditedSpecialism
from app.enums.lawyer import ExpertiseEnum, RelationshipTypeEnum, MatterTypeEnum, AccreditedSpecialismEnum

db = SessionLocal()

from app.utils.formatters import format_expertises, format_accredited_specialisms
# def format_expertises(expertises: list[LawyerExpertise] | None, expertises_other: dict[str, list[str]] | None) -> list[str]:
#     expertises_list = []
#     if expertises is not None:
#         for expertise in expertises:
#             if not expertise.expertise.is_other():
#                 expertises_list.append(expertise.expertise.value)
#     if expertises_other is not None:
#         for key, value in expertises_other.items():
#             expertises_list.extend(value)

#     return expertises_list

# def format_accredited_specialisms(accredited_specialisms: list[LawyerAccreditedSpecialism] | None, accredited_specialism_other: dict[str, list[str]] | None) -> list[str]:
#     accredited_specialisms_list = []
#     if accredited_specialisms is not None:
#         for accredited_specialism in accredited_specialisms:
#             if not accredited_specialism.accredited_specialism.is_other():
#                 accredited_specialisms_list.append(accredited_specialism.accredited_specialism.value)
#     if accredited_specialism_other is not None:
#             accredited_specialisms_list.extend(accredited_specialism_other)
#     return accredited_specialisms_list

# lawyer_id = 41
lawyer_id = 6
lawyer = db.query(Lawyer).options(joinedload(Lawyer.expertises)).filter(Lawyer.id == lawyer_id).first()

print(lawyer.expertises)
print("")
print(lawyer.expertises_other)
print("")
print(lawyer.accredited_specialisms)
print("")
print(lawyer.accredited_specialism_other)
print("")
# print(lawyer.accredited_specialisms)

expertises = format_expertises(lawyer.expertises, lawyer.expertises_other)
print("--------------------------------")
print("Expertises:")
print(expertises)


accredited_specialisms = format_accredited_specialisms(lawyer.accredited_specialisms, lawyer.accredited_specialism_other)
print("--------------------------------")
print("Accredited Specialisms:")
print(accredited_specialisms)