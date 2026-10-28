import logging
import random
from dataclasses import dataclass
from math import exp
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import String, cast, desc, func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models.case import Case
from app.db.models.law_firm import LawFirm
from app.db.models.lawyer import (
    Lawyer,
    LawyerDRPreference,
    LawyerExpertType,
    LawyerMatterType,
    LawyerRelationshipType,
    LawyerExpertise,
    LawyerAccreditedSpecialism,
)
from app.db.models.lawyer_law_firm import LawyerLawFirm
from app.db.models.match import Match
from app.db.models.user import User
from app.db.services.user import (
    create_user_with_role_transactional,
    update_user_generic,
)
from app.enums.file_upload import EntityType
from app.enums.lawyer import (
    DRPreferenceEnum,
    DRTypeEnum,
    ExpertTypeEnum,
    LawyerStatusEnum,
    RegulatorEnum,
)
from app.enums.lawyer_onboarding import LawyerOnboardingStatusEnum
from app.db.models.lawyer_onboarding import LawyerOnboarding
from app.enums.match import MatchStatusEnum
from app.enums.user import GenderEnum, StatusEnum
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.lawyer import (
    InterestedLawyerCaseData,
    InterestedLawyerResponse,
    InterestedLawyersListResponse,
    InterestedLawyerUserData,
    LawyerCreateRequest,
    LawyerSearchRequest,
    LawyerUpdateRequest,
    UserCreateRequest,
)
from app.schemas.v1.user import UserUpdateRequest
from app.services.upload_service import process_file_upload, validate_temp_file_before_processing
from app.utils.encryption import decrypt_id, encrypt_id
from app.utils.helpers import (
    _parse_json_field,
    calculate_hours_to_interested,
    calculate_lawyer_experience,
)
from app.utils.photo_utils import generate_photo_urls
from app.utils.validators import validate_order_params, validate_url_format

logger = logging.getLogger(__name__)

# Helper functions for error handling to fix TRY301 issues
def _raise_invalid_id_format() -> None:
    """Raise HTTPException for invalid ID format."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"success": False, "message": "Invalid expert ID format"},
    )


def _raise_lawyer_not_found() -> None:
    """Raise HTTPException for lawyer not found."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"success": False, "message": "Expert not found"},
    )


def _raise_user_not_found() -> None:
    """Raise HTTPException for user not found."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"success": False, "message": "User not found"},
    )

def _raise_lawyer_access_forbidden() -> None:
    """Raise HTTPException for lawyer access forbidden."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "success": False,
            "message": "You can only update your own expert profile",
        },
    )


def _raise_lawyer_get_access_forbidden() -> None:
    """Raise HTTPException for lawyer get access forbidden."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "success": False,
            "message": "You can only access your own expert profile",
        },
    )


# Constants for field lists
LAWYER_FIELDS = {
    "id",
    "status",
    "city",
    "county",
    "postal_code",
    "reg_no",
    "sra_number",
    "bar_number",
    "regulator",
    "about",
    "photo_url",
    # "accredited_specialisations",
    "linkedin_url",
    "hourly_rate",
    "charge_first_consultation",
    "created_at",
    "admitted_date_solicitor",
    "called_date_barrister",
    "admitted_date_cliex",
    "regulator_other",
    "expert_types_other",
    "expertises_other",
    "accredited_specialism_other",
}

USER_FIELDS = {"user_id", "first_name", "last_name", "email", "phone"}

CASE_FIELDS = {"case_id", "case_no", "case_type", "priority", "case_status", "match_id", "action_date"}


# Dataclasses instead of mock classes
@dataclass
class LawyerQueryData:
    """Lightweight data structure for lawyer query results."""

    id: int
    status: str
    city: str | None
    county: str | None
    postal_code: str | None
    reg_no: str | None
    sra_number: str | None
    bar_number: str | None
    regulator: str | None
    about: str | None
    photo_url: str | None
    # accredited_specialisations: str | None
    linkedin_url: str | None
    hourly_rate: int | None
    charge_first_consultation: int | None
    created_at: Any
    admitted_date_solicitor: Any | None
    called_date_barrister: Any | None
    admitted_date_cliex: Any | None
    regulator_other: str | None
    expert_types_other: str | None
    expertises_other: dict | None
    accredited_specialism_other: dict | None
    @classmethod
    def from_row(cls, row: Any) -> "LawyerQueryData":
        """Create instance from SQLAlchemy row using _mapping (not index-based)."""
        row_dict = {k: v for k, v in row._mapping.items() if k in LAWYER_FIELDS}
        return cls(**row_dict)


@dataclass
class UserQueryData:
    """Lightweight data structure for user query results."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None

    @classmethod
    def from_row(cls, row: Any) -> "UserQueryData":
        """Create instance from SQLAlchemy row using _mapping (not index-based)."""
        row_dict = {k: v for k, v in row._mapping.items() if k in USER_FIELDS}
        return cls(**row_dict)


@dataclass
class CaseQueryData:
    """Lightweight data structure for case query results."""

    case_id: int
    case_no: str | None
    case_type: str | None
    priority: str | None
    case_status: str | None
    match_id: int
    action_date: Any | None

    @classmethod
    def from_row(cls, row: Any) -> "CaseQueryData":
        """Create instance from SQLAlchemy row using _mapping (not index-based)."""
        row_dict = {k: v for k, v in row._mapping.items() if k in CASE_FIELDS}
        return cls(**row_dict)


def _map_to_interested_lawyer_response(
    lawyer, user, case, db: Session
) -> InterestedLawyerResponse:
    """Helper function to convert ORM objects to InterestedLawyerResponse schema."""

    from app.utils.formatters import format_expertises
    from app.utils.formatters import format_accredited_specialisms

    # Calculate lawyer experience (pass lawyer details, not db)
    experience_years = calculate_lawyer_experience(lawyer)

    # Fetch action_date for the match
    action_date = None
    if case and case.action_date:
        action_date = case.action_date

    # Calculate hours to interested (pass action_date directly)
    hours_to_interested = calculate_hours_to_interested(action_date)

    # Create user data
    user_data = InterestedLawyerUserData(
        id=encrypt_id(str(user.user_id)),  # Use user_id from dataclass
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
    )

    # Create case data
    case_data = InterestedLawyerCaseData(
        id=encrypt_id(str(case.case_id)),  # Use case_id from dataclass
        case_no=case.case_no if case.case_no is not None else "",
        case_type=case.case_type if case.case_type else None,
        priority=case.priority if case.priority else None,
        status=case.case_status
        if case.case_status
        else "Open",  # Use case_status from dataclass
    )

    expertises_other = _parse_json_field(lawyer.expertises_other, default={})
    accredited_specialisms_other = _parse_json_field(lawyer.accredited_specialism_other, default=[])

    if isinstance(lawyer, LawyerQueryData):
        lawyer_orm = (
            db.query(Lawyer)
            .options(
                selectinload(Lawyer.expert_types),
                selectinload(Lawyer.expertises),
                selectinload(Lawyer.accredited_specialisms),
            )
            .get(lawyer.id)
        )
        expertises = lawyer_orm.expertises if lawyer_orm and lawyer_orm.expertises else []
        accredited_specialisms = (
            lawyer_orm.accredited_specialisms
            if lawyer_orm and lawyer_orm.accredited_specialisms
            else []
        )
        expert_types = [et.expert_type for et in lawyer_orm.expert_types if not et.expert_type.is_other()]
        if hasattr(lawyer_orm, "expert_types_other") and lawyer_orm.expert_types_other:
            expert_types.append(lawyer_orm.expert_types_other.capitalize())
        expert_types.sort()
    else:
        expertises = lawyer.expertises if lawyer.expertises else []
        accredited_specialisms = lawyer.accredited_specialisms if lawyer.accredited_specialisms else []
        expert_types = [et.expert_type for et in lawyer.expert_types if not et.expert_type.is_other()]
        if hasattr(lawyer, "expert_types_other") and lawyer.expert_types_other:
            expert_types.append(lawyer.expert_types_other.capitalize())
        expert_types.sort()

    expertises = format_expertises(expertises, expertises_other)
    accredited_specialisms = format_accredited_specialisms(accredited_specialisms, accredited_specialisms_other)

    # Create lawyer response
    return InterestedLawyerResponse(
        id=str(lawyer.id),
        status=lawyer.status,
        city=lawyer.city,
        county=lawyer.county,
        postal_code=lawyer.postal_code,
        reg_no=lawyer.reg_no,
        sra_number=lawyer.sra_number,
        bar_number=lawyer.bar_number,
        regulator=lawyer.regulator,
        regulator_other=lawyer.regulator_other,
        about=lawyer.about,
        photo_urls=generate_photo_urls(lawyer.photo_url),
        # accredited_specialisations=lawyer.accredited_specialisations,
        linkedin_url=lawyer.linkedin_url,
        hourly_rate=int(lawyer.hourly_rate) if lawyer.hourly_rate is not None else None,
        charge_first_consultation=int(lawyer.charge_first_consultation) if lawyer.charge_first_consultation is not None else None,
        experience_years=experience_years,
        hours_to_interested=hours_to_interested,
        created_at=lawyer.created_at,
        user=user_data,
        case=case_data,
        expert_types=expert_types,
        expertises=expertises,
        accredited_specialisms=accredited_specialisms,
    )


def create_lawyer_service(
    db: Session, request_data: LawyerCreateRequest, current_user_id: int, lawfirm: LawFirm, financial_claims_exemptions: bool,
    legal_expert: LawyerOnboarding | None = None
) -> tuple[Lawyer, bool]:
    """Create a new lawyer with associated multi-select data."""
    try:
        # comment out validation of dr preferences as an expert can be both
        # is_valid_dr, validation_message = validate_dr_preferences_selection(
        #     request_data.dr_preferences
        # )
        # if not is_valid_dr:
        #     raise ValueError(validation_message)

        # Validate temp file existence and size BEFORE user creation
        validate_temp_file_before_processing(
            photo_url=request_data.photo_url,
            entity_type=EntityType.LAWYER_PROFILE
        )

        user_status = StatusEnum.ACTIVE if request_data.status == LawyerStatusEnum.ACTIVE else StatusEnum.INACTIVE
        # Create the user
        user_data = UserCreateRequest(
            first_name=request_data.first_name,
            last_name=request_data.last_name,
            email=request_data.email,
            phone=request_data.phone,
            gender=request_data.gender,
            # gender_other=request_data.gender_other,
            status=user_status,
            password=None,
        )
        user = create_user_with_role_transactional(db, user_data, UserRoleEnum.LAWYER)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"success": False, "message": "Failed to create user"},
            )

        # VALIDATION: Check if a lawyer with the same user_id and lawfirm_id already exists
        existing_lawyer_lawfirm = (
            db.query(LawyerLawFirm)
            .join(Lawyer, LawyerLawFirm.lawyer_id == Lawyer.id)
            .filter(
                Lawyer.user_id == user.id,
                LawyerLawFirm.lawfirm_id == lawfirm.id
            )
            .first()
        )

        if existing_lawyer_lawfirm:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "success": False,
                "message": "An expert with this user is already associated with this organization",
            })

        if request_data.linkedin_url and not validate_url_format(request_data.linkedin_url):
            raise ValueError("Invalid LinkedIn URL format")

        # Create the main lawyer record first
        lawyer_data = request_data.model_dump(
            exclude={"expert_types", "relationship_types", "matter_types", "dr_preferences", "user_id", "password", "first_name", "last_name", "email", "phone", "gender", "lawfirm_id", "expertise", "accredited_specialisms", "reference_id"}
        )
        # , "gender_other"


        expertises = []
        expertises_other = {}
        # Create expertise
        for key, value in request_data.expertise.model_dump(exclude_unset=True).items():
            if value.get("expertises") is not None:
                expertises.extend(value.get("expertises"))
            if value.get("other") is not None:
                if key not in expertises_other:
                    expertises_other[key] = []
                for other in value.get("other"):
                    if other not in expertises_other[key]:
                        expertises_other[key].append(other)

        lawyer_data["expertises_other"] = expertises_other

        # Set initial photo_url to None (will be updated if processing is successful)
        lawyer_data["photo_url"] = None
        lawyer_data["financial_claims_exemptions"] = financial_claims_exemptions

        lawyer = Lawyer(**lawyer_data, user_id=user.id)
        db.add(lawyer)
        db.flush()  # Get the ID without committing

        # Process photo upload if provided (CREATE operation - new folder)
        processed_photo_url = None
        photo_processing_success = False
        if request_data.photo_url:
            # If photo_url is provided, behave as current flow
            processed_photo_url, photo_processing_success = process_file_upload(
                photo_url=request_data.photo_url,
                entity_id=lawyer.id,
                entity_type=EntityType.LAWYER_PROFILE,
                is_update=False,
            )
        elif legal_expert:
            from app.services.upload_service import copy_files_to_new_location
            if legal_expert.photo_url:  # Legal expert with photo exists
                    processed_photo_url = copy_files_to_new_location(
                        existing_path=legal_expert.photo_url,
                        entity_type=EntityType.LAWYER_PROFILE,
                        entity_id=lawyer.id
                    )
                    if processed_photo_url:
                        photo_processing_success = True
                        
        if legal_expert:
            legal_expert.status = LawyerOnboardingStatusEnum.ONBOARDED
            db.add(legal_expert)

        if processed_photo_url:
            # Update the lawyer record with processed photo URL
            lawyer.photo_url = processed_photo_url
        else:
            lawyer.photo_url = None

        # Create expert types
        for expert_type in request_data.expert_types:
            lawyer_expert = LawyerExpertType(
                lawyer_id=lawyer.id, expert_type=expert_type
            )
            db.add(lawyer_expert)

        # Create relationship types
        for relationship_type in request_data.relationship_types:
            lawyer_relationship = LawyerRelationshipType(
                lawyer_id=lawyer.id, relationship_type=relationship_type
            )
            db.add(lawyer_relationship)

        # Create matter types
        for matter_type in request_data.matter_types:
            lawyer_matter = LawyerMatterType(
                lawyer_id=lawyer.id, matter_type=matter_type
            )
            db.add(lawyer_matter)

        # Create dispute resolution preferences
        for dr_preference in request_data.dr_preferences:
            preference = LawyerDRPreference(
                lawyer_id=lawyer.id,
                dr_preference=dr_preference,
            )
            db.add(preference)
            
        # Create expertise
        for each_expertise in expertises:
            lawyer_expert = LawyerExpertise(
                lawyer_id=lawyer.id, expertise=each_expertise
            )
            db.add(lawyer_expert)

        # Create accredited specialisms
        for each_accredited_specialism in request_data.accredited_specialisms:
            lawyer_accredited_specialism = LawyerAccreditedSpecialism(
                lawyer_id=lawyer.id, accredited_specialism=each_accredited_specialism
            )
            db.add(lawyer_accredited_specialism)

        # Create lawyer law firm
        lawyer_law_firm = LawyerLawFirm(
            lawyer_id=lawyer.id, lawfirm_id=lawfirm.id
        )
        db.add(lawyer_law_firm)

        db.commit()

        # Query the lawyer again with relationships loaded to ensure they're available
        lawyer_with_relationships = (
            db.query(Lawyer)
            .options(
                selectinload(Lawyer.expert_types),
                selectinload(Lawyer.relationship_types),
                selectinload(Lawyer.matter_types),
                selectinload(Lawyer.dr_preferences),
                selectinload(Lawyer.expertises),
                selectinload(Lawyer.accredited_specialisms),
            )
            .filter(Lawyer.id == lawyer.id)
            .first()
        )

        return lawyer_with_relationships, photo_processing_success
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Failed to create expert: {e!s}"},
        ) from e


def update_lawyer_service(
    db: Session, request_data: LawyerUpdateRequest, current_user_id: int, lawfirm: LawFirm | None = None, financial_claims_exemptions: bool = False
) -> tuple[Lawyer, bool]:
    """Update an existing lawyer with associated multi-select data."""
    try:
        # Convert decrypted string ID to integer
        try:
            lawyer_id = decrypt_id(request_data.id)
            if not lawyer_id:
                _raise_invalid_id_format()
        except (ValueError, TypeError):
            _raise_invalid_id_format()

        # Validate temp file existence and size BEFORE user creation
        validate_temp_file_before_processing(
            photo_url=request_data.photo_url,
            entity_type=EntityType.LAWYER_PROFILE
        )
        
        # Get the lawyer by ID
        lawyer = db.query(Lawyer).options(joinedload(Lawyer.user)).filter(Lawyer.id == lawyer_id).first()
        if not lawyer:
            _raise_lawyer_not_found()

        if not lawyer.user:
            _raise_user_not_found()

        # Get all lawyers with the same user_id (including the one being updated)
        lawyers_with_same_user = db.query(Lawyer).filter(Lawyer.user_id == lawyer.user_id).all()

        # Determine the new status for each lawyer after this update
        # Build a list of statuses as they would be after this update
        updated_statuses = []
        for l in lawyers_with_same_user:
            if l.id == lawyer.id:
                # This is the lawyer being updated, use the new status from request_data
                updated_statuses.append(request_data.status)
            else:
                updated_statuses.append(l.status)

        # If all lawyers are deactivated, set user to INACTIVE, else ACTIVE
        if all(status != LawyerStatusEnum.ACTIVE for status in updated_statuses):
            user_status = StatusEnum.INACTIVE
        else:
            user_status = StatusEnum.ACTIVE

        update_user = UserUpdateRequest(
            first_name=request_data.first_name,
            last_name=request_data.last_name,
            email=request_data.email,
            phone=request_data.phone,
            gender=request_data.gender,
            # gender_other=request_data.gender_other,
            status=user_status,
        )
        user = update_user_generic(db, lawyer.user.id, update_user)

        # Update main lawyer fields
        update_data = request_data.model_dump(
            exclude={"id", "expert_types", "relationship_types", "matter_types", "dr_preferences", "user_id", "password", "first_name", "last_name", "email", "phone", "gender", "photo_url", "expertise", "accredited_specialisms"},
            exclude_unset=True,
        )
        # , "gender_other"

        expertises = []
        expertises_other = {}
        # Create expertise
        for key, value in request_data.expertise.model_dump(exclude_unset=True).items():
            if value.get("expertises") is not None:
                expertises.extend(value.get("expertises"))
            if value.get("other") is not None:
                if key not in expertises_other:
                    expertises_other[key] = []
                for other in value.get("other"):
                    if other not in expertises_other[key]:
                        expertises_other[key].append(other)

        update_data["expertises_other"] = expertises_other
        
        photo_processing_success = True
        if request_data.photo_url:
            # Process photo upload if provided (UPDATE operation)
            processed_photo_url, photo_processing_success = process_file_upload(
                photo_url=request_data.photo_url,
                entity_id=lawyer.id,
                entity_type=EntityType.LAWYER_PROFILE,
                is_update=True,
                existing_photo_url=lawyer.photo_url
            )
            # Update photo_url with processed URL if photo was provided
            if processed_photo_url is not None:
                update_data["photo_url"] = processed_photo_url
        else:
            update_data["photo_url"] = None

        update_data["financial_claims_exemptions"] = financial_claims_exemptions

        if request_data.linkedin_url and not validate_url_format(request_data.linkedin_url):
            raise ValueError("Invalid LinkedIn URL format")

        for field, value in update_data.items():
            setattr(lawyer, field, value)

        # Update multi-select fields if provided
        if request_data.expert_types is not None:
            # Remove existing expert types
            db.query(LawyerExpertType).filter(
                LawyerExpertType.lawyer_id == lawyer.id
            ).delete()

            # Add new expert types
            for expert_type in request_data.expert_types:
                lawyer_expert = LawyerExpertType(
                    lawyer_id=lawyer.id, expert_type=expert_type
                )
                db.add(lawyer_expert)

        if request_data.relationship_types is not None:
            # Remove existing relationship types
            db.query(LawyerRelationshipType).filter(
                LawyerRelationshipType.lawyer_id == lawyer.id
            ).delete()

            # Add new relationship types
            for relationship_type in request_data.relationship_types:
                lawyer_relationship = LawyerRelationshipType(
                    lawyer_id=lawyer.id, relationship_type=relationship_type
                )
                db.add(lawyer_relationship)

        if request_data.matter_types is not None:
            # Remove existing matter types
            db.query(LawyerMatterType).filter(
                LawyerMatterType.lawyer_id == lawyer.id
            ).delete()

            # Add new matter types
            for matter_type in request_data.matter_types:
                lawyer_matter = LawyerMatterType(
                    lawyer_id=lawyer.id, matter_type=matter_type
                )
                db.add(lawyer_matter)

        if request_data.dr_preferences is not None:
            # comment out validation of dr preferences as an expert can be both
            # is_valid_dr, validation_message = validate_dr_preferences_selection(
            #     request_data.dr_preferences
            # )
            # if not is_valid_dr:
            #     raise ValueError(validation_message)

            db.query(LawyerDRPreference).filter(
                LawyerDRPreference.lawyer_id == lawyer.id
            ).delete()

            for dr_preference in request_data.dr_preferences:
                preference = LawyerDRPreference(
                    lawyer_id=lawyer.id,
                    dr_preference=dr_preference,
                )
                db.add(preference)
            
        # Update expertise
        db.query(LawyerExpertise).filter(
            LawyerExpertise.lawyer_id == lawyer.id
        ).delete()
        for each_expertise in expertises:
            lawyer_expert = LawyerExpertise(
                lawyer_id=lawyer.id, expertise=each_expertise
            )
            db.add(lawyer_expert)

        # Update accredited specialisms
        db.query(LawyerAccreditedSpecialism).filter(
            LawyerAccreditedSpecialism.lawyer_id == lawyer.id
        ).delete()
        for each_accredited_specialism in request_data.accredited_specialisms:
            lawyer_accredited_specialism = LawyerAccreditedSpecialism(
                lawyer_id=lawyer.id, accredited_specialism=each_accredited_specialism
            )
            db.add(lawyer_accredited_specialism)

        # VALIDATION & UPDATE: Handle lawfirm association changes
        if lawfirm is not None:
            # Get current lawfirm association
            current_lawfirm_association = (
                db.query(LawyerLawFirm)
                .filter(LawyerLawFirm.lawyer_id == lawyer.id)
                .first()
            )
            # Check if lawfirm is being changed
            if current_lawfirm_association and current_lawfirm_association.lawfirm_id != lawfirm.id:
                # Lawfirm is being changed - validate the new combination doesn't exist
                existing_lawyer_lawfirm = (
                    db.query(LawyerLawFirm)
                    .join(Lawyer, LawyerLawFirm.lawyer_id == Lawyer.id)
                    .filter(
                        Lawyer.user_id == lawyer.user_id,
                        LawyerLawFirm.lawfirm_id == lawfirm.id,
                        LawyerLawFirm.lawyer_id != lawyer.id  # Exclude current lawyer
                    )
                    .first()
                )
                if existing_lawyer_lawfirm:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                        "success": False,
                        "message": "An expert with this user is already associated with this organization",
                    })

                # Update the lawfirm association
                current_lawfirm_association.lawfirm_id = lawfirm.id
            elif not current_lawfirm_association:
                # No existing association, create new one (edge case)
                # First validate it doesn't exist for another lawyer with same user
                existing_lawyer_lawfirm = (
                    db.query(LawyerLawFirm)
                    .join(Lawyer, LawyerLawFirm.lawyer_id == Lawyer.id)
                    .filter(
                        Lawyer.user_id == lawyer.user_id,
                        LawyerLawFirm.lawfirm_id == lawfirm.id
                    )
                    .first()
                )
                if existing_lawyer_lawfirm:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                        "success": False,
                        "message": "An expert with this user is already associated with this organization",
                    })

                # Create new association
                new_association = LawyerLawFirm(
                    lawyer_id=lawyer.id,
                    lawfirm_id=lawfirm.id
                )
                db.add(new_association)

        db.commit()

        # Query the lawyer again with relationships loaded to ensure they're available
        lawyer_with_relationships = (
            db.query(Lawyer)
            .options(
                selectinload(Lawyer.expert_types),
                selectinload(Lawyer.relationship_types),
                selectinload(Lawyer.matter_types),
                selectinload(Lawyer.dr_preferences),
                selectinload(Lawyer.expertises),
                selectinload(Lawyer.accredited_specialisms),
            )
            .filter(Lawyer.id == lawyer.id)
            .first()
        )

        return lawyer_with_relationships, photo_processing_success

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Failed to update expert: {e!s}"},
        ) from e


def search_lawyer_service(
    db: Session, request_data: LawyerSearchRequest
) -> tuple[list[Lawyer], int]:
    """Search lawyers with filters, pagination, and ordering."""
    try:
        # Define valid order_by fields to prevent AttributeError
        valid_order_fields = {
            "id",
            "status",
            "city",
            "county",
            "regulator",
            "hourly_rate",
            "created_at",
            "updated_at",
            "address_line_1",
            "address_line_2",
            "postal_code",
            "reg_no",
            "sra_number",
            "bar_number",
            "admitted_date_solicitor",
            "called_date_barrister",
            "admitted_date_cliex",
            "joined_at",
            "left_at",
        }
        validate_order_params(request_data.order_by, request_data.order_dir, valid_order_fields)

        base_query = db.query(Lawyer).join(User, Lawyer.user_id == User.id)

        if request_data.search_term:
            search_term = request_data.search_term.strip()
            base_query = base_query.filter(
                User.first_name.ilike(f"%{search_term}%")
                | User.last_name.ilike(f"%{search_term}%")
                | User.email.ilike(f"%{search_term}%")
                | (func.trim(User.first_name) + " " + func.trim(User.last_name)).ilike(
                    f"%{search_term}%"
                )
            )

        if request_data.country:
            base_query = base_query.filter(Lawyer.country == request_data.country)

        # Apply basic filters (no joins yet)
        if request_data.status:
            base_query = base_query.filter(Lawyer.status == request_data.status)
            base_query = base_query.filter(User.status == request_data.status)
        if request_data.lawyer_status:
            base_query = base_query.filter(Lawyer.status == request_data.lawyer_status)

        if request_data.city:
            request_data.city = request_data.city.strip()
            base_query = base_query.filter(Lawyer.city.ilike(f"%{request_data.city}%"))

        if request_data.county:
            request_data.county = request_data.county.strip()
            base_query = base_query.filter(
                Lawyer.county.ilike(f"%{request_data.county}%")
            )

        if request_data.regulator:
            base_query = base_query.filter(Lawyer.regulator == request_data.regulator)

        if request_data.min_hourly_rate is not None:
            base_query = base_query.filter(
                Lawyer.hourly_rate >= request_data.min_hourly_rate
            )

        if request_data.max_hourly_rate is not None:
            base_query = base_query.filter(
                Lawyer.hourly_rate <= request_data.max_hourly_rate
            )

        # Handle multi-select filters with subqueries to avoid duplicates
        if request_data.expert_type:
            expert_subquery = (
                db.query(LawyerExpertType.lawyer_id)
                .filter(LawyerExpertType.expert_type == request_data.expert_type)
                .subquery()
            )
            base_query = base_query.filter(Lawyer.id.in_(expert_subquery))

        if request_data.relationship_type:
            relationship_subquery = (
                db.query(LawyerRelationshipType.lawyer_id)
                .filter(
                    LawyerRelationshipType.relationship_type
                    == request_data.relationship_type
                )
                .subquery()
            )
            base_query = base_query.filter(Lawyer.id.in_(relationship_subquery))

        if request_data.matter_type:
            matter_subquery = (
                db.query(LawyerMatterType.lawyer_id)
                .filter(LawyerMatterType.matter_type == request_data.matter_type)
                .subquery()
            )
            base_query = base_query.filter(Lawyer.id.in_(matter_subquery))
        
        if request_data.expertise:
            expertise_subquery = (
                db.query(LawyerExpertise.lawyer_id)
                .filter(LawyerExpertise.expertise == request_data.expertise)
                .subquery()
            )
            base_query = base_query.filter(Lawyer.id.in_(expertise_subquery))
            
        if request_data.accredited_specialism:
            accredited_specialism_subquery = (
                db.query(LawyerAccreditedSpecialism.lawyer_id)
                .filter(LawyerAccreditedSpecialism.accredited_specialism == request_data.accredited_specialism)
                .subquery()
            )
            base_query = base_query.filter(Lawyer.id.in_(accredited_specialism_subquery))

        if request_data.lawfirm_id:
            lawfirm_id = decrypt_id(request_data.lawfirm_id)
            try:
                lawfirm_id = int(lawfirm_id)
            except (ValueError, TypeError):
                raise ValueError("Invalid organization ID format")
            lawfirm_subquery = (
                db.query(LawyerLawFirm.lawyer_id)
                .filter(LawyerLawFirm.lawfirm_id == lawfirm_id)
                .subquery()
            )
            base_query = base_query.filter(Lawyer.id.in_(lawfirm_subquery))

        # Get total count before pagination using lightweight scalar query
        total_count: int = (
            base_query.with_entities(func.count(Lawyer.id)).scalar() or 0
        )

        # Apply ordering safely
        order_field = getattr(Lawyer, request_data.order_by)
        if request_data.order_dir.lower() == "desc":
            base_query = base_query.order_by(desc(order_field))
        else:
            base_query = base_query.order_by(order_field)

        # Apply pagination
        offset = (request_data.page - 1) * request_data.limit
        base_query = base_query.offset(offset).limit(request_data.limit)

        # Execute query and load relationships with eager loading to prevent N+1
        # Use selectinload for one-to-many collections to avoid cartesian product
        # explosion; keep joinedload only for the one-to-one User relationship.
        lawyers = base_query.options(
            joinedload(Lawyer.user),
            selectinload(Lawyer.expert_types),
            selectinload(Lawyer.relationship_types),
            selectinload(Lawyer.matter_types),
            selectinload(Lawyer.dr_preferences),
            selectinload(Lawyer.expertises),
            selectinload(Lawyer.accredited_specialisms),
            selectinload(Lawyer.lawyer_law_firms).selectinload(
                LawyerLawFirm.law_firm
            ),
        ).all()

        return lawyers, total_count
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Failed to search experts: {e!s}"},
        ) from e


LAWYER_CARD_LIMIT = 4
LAWYER_CARD_RANDOM_POOL = 20
LAWYER_CARD_MALE_POOL = 10


def _lawyer_card_query(db: Session):
    """Base query for active lawyers shown on home page cards."""
    return (
        db.query(Lawyer)
        .join(User, Lawyer.user_id == User.id)
        .filter(Lawyer.status == LawyerStatusEnum.ACTIVE)
        .filter(User.status == StatusEnum.ACTIVE)
        .options(
            joinedload(Lawyer.user),
            selectinload(Lawyer.expert_types),
            selectinload(Lawyer.relationship_types),
            selectinload(Lawyer.matter_types),
            selectinload(Lawyer.dr_preferences),
            selectinload(Lawyer.expertises),
            selectinload(Lawyer.accredited_specialisms),
            selectinload(Lawyer.lawyer_law_firms).selectinload(LawyerLawFirm.law_firm),
        )
    )


def _is_male_lawyer(lawyer: Lawyer) -> bool:
    return lawyer.user is not None and lawyer.user.gender == GenderEnum.MALE


def _pick_lawyer_cards(lawyers: list[Lawyer], limit: int) -> list[Lawyer]:
    """Pick up to `limit` unique random lawyers, with one male when available.

    The male profile is swapped into a random slot and the result is shuffled,
    so it is not fixed at the start of the list.
    """
    if limit <= 0:
        return []

    unique_lawyers = list({lawyer.id: lawyer for lawyer in lawyers}.values())
    random.shuffle(unique_lawyers)

    picked = unique_lawyers[:limit]
    if not picked or any(_is_male_lawyer(lawyer) for lawyer in picked):
        random.shuffle(picked)
        return picked

    remaining_males = [lawyer for lawyer in unique_lawyers[limit:] if _is_male_lawyer(lawyer)]
    if remaining_males:
        picked[random.randrange(len(picked))] = random.choice(remaining_males)

    random.shuffle(picked)
    return picked


def get_lawyer_cards_service(db: Session, limit: int = LAWYER_CARD_LIMIT) -> list[Lawyer]:
    """Select unique random active lawyers for home page cards.

    Loads a random pool of active lawyers. When that pool has no male profile,
    a second random query adds male profiles. The combined list is then
    shuffled into the card response, with a male included when one exists.
    """
    try:
        active_lawyers = (
            _lawyer_card_query(db)
            .order_by(func.random())
            .limit(LAWYER_CARD_RANDOM_POOL)
            .all()
        )
        if active_lawyers and not any(_is_male_lawyer(lawyer) for lawyer in active_lawyers):
            selected_ids = [lawyer.id for lawyer in active_lawyers]
            male_lawyers = (
                _lawyer_card_query(db)
                .filter(User.gender == GenderEnum.MALE)
                .filter(Lawyer.id.notin_(selected_ids))
                .order_by(func.random())
                .limit(LAWYER_CARD_MALE_POOL)
                .all()
            )
            active_lawyers.extend(male_lawyers)

        return _pick_lawyer_cards(active_lawyers, limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Failed to fetch lawyer cards: {e!s}"},
        ) from e


def get_lawyer_by_id_service(
    db: Session, lawyer_id: str, current_user: User
) -> Lawyer:
    """Get a lawyer by ID."""
    try:
        # Convert decrypted string ID to integer
        try:
            lawyer_id_int = int(lawyer_id)
        except (ValueError, TypeError):
            _raise_invalid_id_format()

        base_query = db.query(Lawyer).options(
            joinedload(Lawyer.user),
            selectinload(Lawyer.expert_types),
            selectinload(Lawyer.relationship_types),
            selectinload(Lawyer.matter_types),
            selectinload(Lawyer.dr_preferences),
            selectinload(Lawyer.expertises),
            selectinload(Lawyer.accredited_specialisms),
            selectinload(Lawyer.lawyer_law_firms).selectinload(LawyerLawFirm.law_firm),
        ).filter(Lawyer.id == lawyer_id_int)

        lawyer = base_query.first()
        if not lawyer:
            _raise_lawyer_not_found()

        return lawyer

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Failed to get expert: {e!s}"},
        ) from e


def get_interested_lawyers(
    db: Session,
    case_id: int | None = None,
    page: int = 1,
    limit: int = 10,
    order_by: str = "created_at",
    order_dir: str = "desc",
) -> InterestedLawyersListResponse:
    """Get lawyers with INTERESTED matches, including user and case details."""

    # Map allowed fields per model
    orderable_fields = {
        "lawyer": {
            "id",
            "status",
            "city",
            "county",
            "postal_code",
            "reg_no",
            "hourly_rate",
            "created_at",
            "updated_at",
        },
        "user": {"id", "first_name", "last_name", "email", "phone", "created_at"},
        "case": {"id", "case_no", "case_type", "priority", "status", "created_at"},
    }

    # Default: lawyer.created_at
    if order_by in orderable_fields["lawyer"]:
        pass
    elif order_by in orderable_fields["user"]:
        pass
    elif order_by in orderable_fields["case"]:
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": f"Invalid order_by field: {order_by}"},
        )

    # Validate order direction
    if order_dir.lower() not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Order direction must be 'asc' or 'desc'",
            },
        )

    # Calculate offset
    offset = (page - 1) * limit

    # Base query - use specific columns to avoid missing column issues
    base_query = (
        db.query(
            Lawyer.id,
            Lawyer.status,
            Lawyer.city,
            Lawyer.county,
            Lawyer.postal_code,
            Lawyer.reg_no,
            Lawyer.sra_number,
            Lawyer.bar_number,
            Lawyer.regulator,
            Lawyer.regulator_other,
            Lawyer.expert_types_other,
            Lawyer.expertises_other,
            Lawyer.accredited_specialism_other,
            Lawyer.about,
            Lawyer.photo_url,
            # Lawyer.accredited_specialisations,
            Lawyer.linkedin_url,
            Lawyer.hourly_rate,
            Lawyer.charge_first_consultation,
            Lawyer.created_at,
            Lawyer.admitted_date_solicitor,
            Lawyer.called_date_barrister,
            Lawyer.admitted_date_cliex,
            User.id.label("user_id"),
            User.first_name,
            User.last_name,
            User.email,
            User.phone,
            Case.id.label("case_id"),
            Case.case_no,
            cast(Case.case_type, String).label("case_type"),
            cast(Case.priority, String).label("priority"),
            cast(Case.status, String).label("case_status"),
            Match.id.label("match_id"),
            Match.action_date.label("action_date"),
        )
        .join(Match, Lawyer.id == Match.lawyer_id)
        .join(User, Lawyer.user_id == User.id)
        .join(Case, Match.case_id == Case.id)
        .filter(Match.status == MatchStatusEnum.INTERESTED)
        .filter(Lawyer.status == LawyerStatusEnum.ACTIVE)
        .filter(User.status == StatusEnum.ACTIVE)
    )

    # Filter by case_id
    if case_id is not None:
        base_query = base_query.filter(Case.id == case_id)

    # Count
    total_count = base_query.count()

    # Apply ordering - map to actual column names, including cross-table fields
    ORDER_BY_COLUMN_MAP: dict[str, Any] = {
        # Lawyer fields
        "id": Lawyer.id,
        "status": Lawyer.status,
        "city": Lawyer.city,
        "county": Lawyer.county,
        "postal_code": Lawyer.postal_code,
        "reg_no": Lawyer.reg_no,
        "hourly_rate": Lawyer.hourly_rate,
        "created_at": Lawyer.created_at,
        "updated_at": Lawyer.updated_at if hasattr(Lawyer, "updated_at") else Lawyer.created_at,
        # User fields
        "user_id": User.id,
        "first_name": User.first_name,
        "last_name": User.last_name,
        "email": User.email,
        "phone": User.phone,
        # Case fields
        "case_id": Case.id,
        "case_no": Case.case_no,
        "case_type": Case.case_type,
        "priority": Case.priority,
        "case_status": Case.status,
        "status_case": Case.status,  # allow for "status" ambiguity
    }

    # Map ambiguous "status" to Case.status if requested, else Lawyer.status
    if order_by == "status":
        # If the user wants to order by case status, they should use "case_status"
        # But if "status" is ambiguous, default to Lawyer.status
        order_column = ORDER_BY_COLUMN_MAP.get("status", Lawyer.created_at)
    else:
        order_column = ORDER_BY_COLUMN_MAP.get(order_by, Lawyer.created_at)

    if order_dir.lower() == "desc":
        base_query = base_query.order_by(desc(order_column))
    else:
        base_query = base_query.order_by(order_column)

    # Pagination
    results = base_query.offset(offset).limit(limit).all()

    # Handle empty results
    if not results:
        # Return an empty response with 200 OK for empty result sets
        return InterestedLawyersListResponse(
            total_count=0,
            records_in_page=0,
            lawyers=[],
        )

    # Convert results to response format using dataclasses instead of mock classes
    lawyer_responses = []
    for row in results:
        # Use dataclasses with row._mapping instead of fragile index-based access
        lawyer = LawyerQueryData.from_row(row)
        user = UserQueryData.from_row(row)
        case = CaseQueryData.from_row(row)

        lawyer_response = _map_to_interested_lawyer_response(lawyer, user, case, db)
        lawyer_responses.append(lawyer_response)

    # Return the proper response schema
    return InterestedLawyersListResponse(
        total_count=total_count,
        records_in_page=len(lawyer_responses),
        lawyers=lawyer_responses,
    )


def check_lawyer_match_exists(db: Session, case_id: int, lawyer: Lawyer) -> bool:
    """Check if a lawyer has a match for a case."""
    return db.query(Match).filter(Match.case_id == case_id, Match.lawyer_id == lawyer.id).first() is not None


def get_financial_claims_exemptions(request_data: LawyerCreateRequest) -> bool:
    """
    Get financial claims exemptions for a lawyer.
    Rules:
    - If the lawyer is a family consultant, mediator, or divorce coach, shuold not be assigned to financial claims.
    """
    exempt_types = {
        ExpertTypeEnum.FAMILY_CONSULTANT,
        ExpertTypeEnum.MEDIATOR,
        ExpertTypeEnum.DIVORCE_COACH
    }
    return bool(request_data.expert_types and any(expert_type in request_data.expert_types for expert_type in exempt_types))


def validate_regulator(request_data: LawyerCreateRequest) -> bool:
    """
    Validate regulator for a lawyer.
    Rules:
    - if solicitor is selected, then regulator should be SRA
    - if barrister is selected, then regulator should be BSB
    - A person cannnot be regualted by both SRA and BSB, similarily for Cilex and BSB
    """

    # Define the required regulator for each expert type
    required_regulator = {
        ExpertTypeEnum.SOLICITOR: RegulatorEnum.SRA,
        ExpertTypeEnum.BARRISTER: RegulatorEnum.BSB,
    }

    # Validate all expert types against the chosen regulator
    if not all(
        request_data.regulator == required_regulator[etype]
        for etype in request_data.expert_types
        if etype in required_regulator
    ):
        return False

    # Check for regulator conflicts - a person cannot be regulated by multiple conflicting regulators
    # Based on the expert types, determine which regulators would be required
    required_regulators = set()
    for expert_type in request_data.expert_types:
        if expert_type == ExpertTypeEnum.SOLICITOR:
            required_regulators.add(RegulatorEnum.SRA)
        elif expert_type == ExpertTypeEnum.BARRISTER:
            required_regulators.add(RegulatorEnum.BSB)
        # Note: CILEX expert type would require CILEX regulator
        # This can be added when CILEX expert type is defined

    # If multiple conflicting regulators are required, it's invalid
    conflicting_pairs = [
        {RegulatorEnum.SRA, RegulatorEnum.BSB},
        {RegulatorEnum.BSB, RegulatorEnum.CILEX},
        # Add more conflicting pairs as needed, e.g.:
        # {RegulatorEnum.SRA, RegulatorEnum.CILEX},
    ]

    for conflicting_pair in conflicting_pairs:
        if conflicting_pair.issubset(required_regulators):
            return False

    return True


def validate_dr_preferences_selection(
    selected_preferences: list[DRPreferenceEnum] | None,
) -> tuple[bool, str]:
    """
    Validate that no 'Support' option is selected together with other roles for the same DR base.
    """

    base_map = {}
    
    for preference in selected_preferences:
        if preference.base:
            base_map.setdefault(preference.base, []).append(preference.type_)
    
    invalid_bases = [
        base
        for base, types in base_map.items()
        if DRTypeEnum.SUPPORT in types and len(types) > 1
    ]

    if invalid_bases:
        invalid_bases_str = ", ".join(invalid_bases)
        return False, f"Cannot select both Support and other roles for: {invalid_bases_str}"
    
    return True, "Valid selection"

def check_match_confirm_exists(db: Session, case_id: int) -> bool:
    """Check if there are any match confirmed lawyers for a case."""
    return db.query(Match.id).filter(Match.case_id == case_id, Match.is_confirmed).first() is not None


def get_case_lawyer_by_case_id_service(db: Session, case_id: int) -> Case | None:
    """Get a lawyer by case ID."""
    from app.db.models.case_lawyer import CaseLawyer
    from app.db.models.case_customer import CaseCustomer
    from app.db.models.customer import Customer
    from app.enums.law_firm import LawFirmStatusEnum
    from app.enums.case import CaseStatusEnum

    return db.query(Case).options(
            joinedload(Case.case_lawyers)
            .joinedload(CaseLawyer.lawyer)
            .joinedload(Lawyer.lawyer_law_firms).joinedload(LawyerLawFirm.law_firm),
            joinedload(Case.case_customers).joinedload(CaseCustomer.customer).joinedload(Customer.user),
        ).filter(Case.id == case_id,
         Case.status == CaseStatusEnum.OPEN, 
         Lawyer.status == LawyerStatusEnum.ACTIVE,
         LawFirm.status == LawFirmStatusEnum.ACTIVE, 
         LawFirm.engage_form_url is not None, 
         Customer.status == StatusEnum.ACTIVE, 
         User.status == StatusEnum.ACTIVE
         ).first()