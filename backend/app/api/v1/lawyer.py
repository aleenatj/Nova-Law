"""Expert API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.enums.law_firm import LawFirmStatusEnum
from app.core.security import get_current_active_user
from app.db.models.user import User
from app.db.services.law_firm import get_law_firm_by_id
from app.db.models.lawyer import Lawyer
from app.db.services.lawyer import (
    create_lawyer_service,
    get_financial_claims_exemptions,
    get_lawyer_by_id_service,
    get_lawyer_cards_service,
    validate_regulator,
    search_lawyer_service,
    update_lawyer_service,
)
from app.enums.events import EventType
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.base import BaseResponse, ResponseMessage
from app.schemas.v1.event import Event
from app.schemas.v1.lawyer import (
    LawFirmData,
    LawyerCreateRequest,
    LawyerListResponse,
    LawyerResponse,
    LawyerSearchRequest,
    LawyerUpdateRequest,
    LawyerExpertiseInput,
    MarriedCivilPartnersExpertiseGroup,
    CohabiteesExpertiseGroup,
)
from app.utils.dependencies import get_db
from app.utils.encryption import decrypt_id
from app.utils.helpers import calculate_lawyer_experience, extract_status_messages
from app.utils.photo_utils import generate_photo_urls
from app.enums.lawyer import RelationshipTypeEnum, RegulatorEnum
from app.enums.lawyer import LawyerStatusEnum
from app.enums.user import StatusEnum
from app.utils.formatters import build_lawyer_card_data, format_accredited_specialisms, format_expertises

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_lawyer_response(lawyer: Lawyer) -> LawyerResponse:
    """Map a lawyer ORM instance to the API response schema."""
    expert_types = [et.expert_type for et in lawyer.expert_types]
    expert_types_all = [et.expert_type.value for et in lawyer.expert_types if not et.expert_type.is_other()]
    if hasattr(lawyer, "expert_types_other") and lawyer.expert_types_other:
        expert_types_all.append(lawyer.expert_types_other.capitalize())
    expert_types_all.sort()

    relationship_types = [rt.relationship_type for rt in lawyer.relationship_types]
    matter_types = [
        mt.matter_type.value if hasattr(mt.matter_type, "value") else str(mt.matter_type)
        for mt in lawyer.matter_types
    ]
    dr_preferences = [preference.dr_preference for preference in lawyer.dr_preferences]
    expertise = LawyerExpertiseInput(
        married_civil_partners=MarriedCivilPartnersExpertiseGroup(
            expertises=[
                expertise.expertise
                for expertise in lawyer.expertises
                if expertise.expertise.relationship_type == RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS
            ],
            other=[
                other
                for other in (lawyer.expertises_other or {}).get("married_civil_partners", [])
            ],
        ),
        cohabitees=CohabiteesExpertiseGroup(
            expertises=[
                expertise.expertise
                for expertise in lawyer.expertises
                if expertise.expertise.relationship_type == RelationshipTypeEnum.COHABITEES
            ],
            other=[
                other
                for other in (lawyer.expertises_other or {}).get("cohabitees", [])
            ],
        ),
    )
    accredited_specialisms = [
        accredited_specialism.accredited_specialism
        for accredited_specialism in lawyer.accredited_specialisms
    ]

    photos = generate_photo_urls(lawyer.photo_url) or None
    lawfirm = lawyer.lawyer_law_firms[0].law_firm if lawyer.lawyer_law_firms else None
    logos = generate_photo_urls(lawfirm.logo) if lawfirm else None
    logos = logos if logos else None
    lawyer_password_set = bool(lawyer.user.password) if lawyer.user.status == StatusEnum.ACTIVE else True
    experience = calculate_lawyer_experience(lawyer)
    expertises_formatted = format_expertises(lawyer.expertises, lawyer.expertises_other)

    return LawyerResponse(
        id=str(lawyer.id),
        first_name=lawyer.user.first_name,
        last_name=lawyer.user.last_name,
        email=lawyer.user.email,
        phone=lawyer.user.phone,
        gender=lawyer.user.gender,
        status=lawyer.status,
        address_line_1=lawyer.address_line_1,
        address_line_2=lawyer.address_line_2,
        city=lawyer.city,
        county=lawyer.county,
        country=lawyer.country,
        postal_code=lawyer.postal_code,
        reg_no=lawyer.reg_no,
        sra_number=lawyer.sra_number,
        bar_number=lawyer.bar_number,
        regulator=lawyer.regulator,
        regulator_other=lawyer.regulator_other,
        admitted_date_solicitor=lawyer.admitted_date_solicitor,
        called_date_barrister=lawyer.called_date_barrister,
        admitted_date_cliex=lawyer.admitted_date_cliex,
        joined_at=lawyer.joined_at,
        left_at=lawyer.left_at,
        about=lawyer.about,
        photo_urls=photos,
        testimonial=lawyer.testimonial,
        linkedin_url=lawyer.linkedin_url,
        hourly_rate=lawyer.hourly_rate,
        charge_first_consultation=lawyer.charge_first_consultation,
        conflict_level_disinclination=lawyer.conflict_level_disinclination,
        pi_insurance=lawyer.pi_insurance,
        user_id=str(lawyer.user_id),
        expert_types=expert_types,
        expert_types_other=lawyer.expert_types_other,
        expert_types_all=expert_types_all,
        relationship_types=relationship_types,
        matter_types=matter_types,
        dr_preferences=dr_preferences,
        expertises=expertise,
        accredited_specialisms=accredited_specialisms,
        accredited_specialism_other=lawyer.accredited_specialism_other,
        created_at=lawyer.created_at,
        updated_at=lawyer.updated_at,
        experience=experience,
        lawfirms=LawFirmData(id=str(lawfirm.id), name=lawfirm.name, logos=logos) if lawfirm else None,
        needs_password_setup=not lawyer_password_set,
        accreditations=format_accredited_specialisms(
            lawyer.accredited_specialisms, lawyer.accredited_specialism_other
        ),
        expertises_all=expertises_formatted,
        lawyer_card_data=build_lawyer_card_data(
            expert_types=expert_types,
            expert_types_other=lawyer.expert_types_other,
            dr_preferences=dr_preferences,
            experience=experience + " of experience" if experience else "",
            expertises_all=expertises_formatted,
        ),
    )


@router.post(
    "/lawyer",
    response_model=BaseResponse[LawyerResponse],
    summary="Create a new Expert",
    description="Create a new expert record with all associated data",
)
async def create_lawyer_endpoint(
    request_data: LawyerCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BaseResponse[LawyerResponse]:
    """Create a new expert."""
    try:
        if request_data.lawfirm_id:
            lawfirm_id = decrypt_id(request_data.lawfirm_id)
            if not lawfirm_id:
                logging.error(f"Invalid lawfirm ID: {request_data.lawfirm_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "Invalid lawfirm ID"})
            lawfirm = get_law_firm_by_id(db, lawfirm_id)
            if not lawfirm:
                logging.error(f"Lawfirm not found: {request_data.lawfirm_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"success": False, "message": "Lawfirm not found"})
            if lawfirm.status == LawFirmStatusEnum.INACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "Lawfirm is inactive"})
        else:
            logging.error(f"Lawfirm ID is required: {request_data.lawfirm_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Lawfirm ID is required"})

        # Validate regulator_other is provided when regulator is OTHER
        if request_data.regulator == RegulatorEnum.OTHER:
            if not request_data.regulator_other or not request_data.regulator_other.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "regulator_other is required when regulator is OTHER"})

        valid = validate_regulator(request_data)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Invalid regulator"})

        legal_expert = None
        if request_data.reference_id:
            # If no photo_url, check if reference_id is provided and valid legal expert exists
            reference_id: str | None = getattr(request_data, "reference_id", None)
            reference_id = decrypt_id(reference_id)
            if not reference_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "Invalid reference ID"},
                )

            from app.db.models.lawyer_onboarding import LawyerOnboarding  # local import to avoid circular
            from sqlalchemy.orm.exc import NoResultFound
            
            try:
                legal_expert = (
                    db.query(LawyerOnboarding)
                    .filter(LawyerOnboarding.id == reference_id)
                    .one()
                )
            except NoResultFound:
                legal_expert = None
                
            if not legal_expert:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"success": False, "message": "Legal expert not found"},
                )

        financial_claims_exemptions = get_financial_claims_exemptions(request_data)

        created_lawyer, photo_processing_success = create_lawyer_service(db, request_data, current_user.id, lawfirm, financial_claims_exemptions, legal_expert)

        # Get expert types
        expert_types = [et.expert_type for et in created_lawyer.expert_types]
        # Get relationship types
        relationship_types = [
            rt.relationship_type for rt in created_lawyer.relationship_types
        ]
        # Get matter types - convert enum to string value
        matter_types = [mt.matter_type.value if hasattr(mt.matter_type, 'value') else str(mt.matter_type) for mt in created_lawyer.matter_types]

        # Prepare DR preferences
        dr_preferences = [
            preference.dr_preference for preference in created_lawyer.dr_preferences
        ]
        # Get expertises 
        expertise = LawyerExpertiseInput(
            married_civil_partners=MarriedCivilPartnersExpertiseGroup(
                expertises=[expertise.expertise for expertise in created_lawyer.expertises if expertise.expertise.relationship_type == RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS],
                other = [
                    other
                    for other in (created_lawyer.expertises_other or {}).get('married_civil_partners', [])
                ]
            ),
            cohabitees=CohabiteesExpertiseGroup(
                expertises=[expertise.expertise for expertise in created_lawyer.expertises if expertise.expertise.relationship_type == RelationshipTypeEnum.COHABITEES],
                other = [
                    other
                    for other in (created_lawyer.expertises_other or {}).get('cohabitees', [])
                ]
            )
        )

        # Get accredited specialisms
        accredited_specialisms = [
            accredited_specialism.accredited_specialism for accredited_specialism in created_lawyer.accredited_specialisms
        ]


        # Generate photo URLs from folder path
        photos = generate_photo_urls(created_lawyer.photo_url)
        # Return null if no photos available
        photos = photos if photos else None

        lawfirm = created_lawyer.lawyer_law_firms[0].law_firm if created_lawyer.lawyer_law_firms else None
        logos = generate_photo_urls(lawfirm.logo) if lawfirm else None
        logos = logos if logos else None

        lawyer_response = LawyerResponse(
            id=str(created_lawyer.id),
            first_name=created_lawyer.user.first_name,
            last_name=created_lawyer.user.last_name,
            email=created_lawyer.user.email,
            phone=created_lawyer.user.phone,
            gender=created_lawyer.user.gender,
            # gender_other=created_lawyer.user.gender_other,
            status=created_lawyer.status,
            address_line_1=created_lawyer.address_line_1,
            address_line_2=created_lawyer.address_line_2,
            city=created_lawyer.city,
            county=created_lawyer.county,
            country=created_lawyer.country,
            postal_code=created_lawyer.postal_code,
            reg_no=created_lawyer.reg_no,
            sra_number=created_lawyer.sra_number,
            bar_number=created_lawyer.bar_number,
            regulator=created_lawyer.regulator,
            regulator_other=created_lawyer.regulator_other,
            admitted_date_solicitor=created_lawyer.admitted_date_solicitor,
            called_date_barrister=created_lawyer.called_date_barrister,
            admitted_date_cliex=created_lawyer.admitted_date_cliex,
            joined_at=created_lawyer.joined_at,
            left_at=created_lawyer.left_at,
            about=created_lawyer.about,
            photo_urls=photos,
            # accredited_specialisations=created_lawyer.accredited_specialisations,
            testimonial=created_lawyer.testimonial,
            linkedin_url=created_lawyer.linkedin_url,
            hourly_rate=created_lawyer.hourly_rate,
            charge_first_consultation=created_lawyer.charge_first_consultation,
            conflict_level_disinclination=created_lawyer.conflict_level_disinclination,
            pi_insurance=created_lawyer.pi_insurance,
            user_id=str(created_lawyer.user_id),
            expert_types=expert_types,
            relationship_types=relationship_types,
            matter_types=matter_types,
            dr_preferences=dr_preferences,
            expertises=expertise,
            accredited_specialisms=accredited_specialisms,
            accredited_specialism_other=created_lawyer.accredited_specialism_other,
            created_at=created_lawyer.created_at,
            updated_at=created_lawyer.updated_at,
            experience=calculate_lawyer_experience(created_lawyer),
            lawfirms=LawFirmData(id=str(lawfirm.id), name=lawfirm.name, logos=logos) if lawfirm else None,
            needs_password_setup=not bool(created_lawyer.user.password),
        )

        # Prepare success messages
        messages = [ResponseMessage(success=True, message="Expert created successfully")]

        # Trigger INITIAL_PASSWORD_LINK_SENT event for newly created lawyer
        # Only if user has Active status
        if created_lawyer.user.status == "Active":
            try:
                event_data = Event(
                    event_type=EventType.INITIAL_PASSWORD_LINK_SENT,
                    payload={
                        "user_id": created_lawyer.user_id,
                    },
                    user_id=current_user.id,
                    current_user=current_user,
                )
                await event_dispatcher.dispatch_event(db, event_data)

                # Extract and append event response messages to API response
                _, event_messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
                for msg in event_messages:
                    messages.append(ResponseMessage(
                        success=bool(msg["success"]),
                        message=str(msg["message"])
                    ))
            except Exception as event_error:
                logger.warning(f"Failed to send initial password email: {event_error}")
                messages.append(ResponseMessage(
                    success=False,
                    message=f"Initial password email could not be sent: {event_error!s}"
                ))

        # Add photo processing status message only if photo was provided
        if request_data.photo_url:
            if not photo_processing_success:
                logger.error(f"Expert created successfully, but photo processing failed for expert ID: {created_lawyer.id}")

        return BaseResponse(
            success=True,
            message=messages,
            data=lawyer_response,
        )
    except ValueError:
        raise
    except HTTPException as e1:
        logging.exception(f"Failed to create expert: {e1!s}")
        raise
    except Exception as e:
        logging.exception(f"Failed to create expert: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to create expert"},
        ) from e


@router.put(
    "/lawyer",
    response_model=BaseResponse[LawyerResponse],
    summary="Update an existing expert",
    description="Update an existing expert record with all associated data",
)
async def update_lawyer_endpoint(
    request_data: LawyerUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BaseResponse[LawyerResponse]:
    """Update an existing expert."""
    try:
        lawfirm_id = None
        lawfirm = None
        if request_data.lawfirm_id:
            lawfirm_id = decrypt_id(request_data.lawfirm_id)
            if not lawfirm_id:
                logging.error(f"Invalid lawfirm ID: {request_data.lawfirm_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "Invalid lawfirm ID"})
            lawfirm = get_law_firm_by_id(db, lawfirm_id)
            if not lawfirm:
                logging.error(f"Lawfirm not found: {request_data.lawfirm_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"success": False, "message": "Lawfirm not found"})
            if request_data.status != LawyerStatusEnum.DEACTIVE and lawfirm.status == LawFirmStatusEnum.INACTIVE:
            # if lawfirm.status == LawFirmStatusEnum.INACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "Lawfirm is inactive"})
        else:
            logging.error(f"Lawfirm ID is required: {request_data.lawfirm_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Lawfirm ID is required"})

        # Validate regulator_other is provided when regulator is OTHER
        if request_data.regulator == RegulatorEnum.OTHER:
            if not request_data.regulator_other or not request_data.regulator_other.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "regulator_other is required when regulator is OTHER"})

        valid = validate_regulator(request_data)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Invalid regulator"})

        financial_claims_exemptions = get_financial_claims_exemptions(request_data)

        updated_lawyer, photo_processing_success = update_lawyer_service(db, request_data, current_user.id, lawfirm, financial_claims_exemptions)

        # Get expert types
        expert_types = [et.expert_type for et in updated_lawyer.expert_types]
        # Get relationship types
        relationship_types = [
            rt.relationship_type for rt in updated_lawyer.relationship_types
        ]
        # Get matter types - convert enum to string value
        matter_types = [mt.matter_type.value if hasattr(mt.matter_type, 'value') else str(mt.matter_type) for mt in updated_lawyer.matter_types]

        # Prepare DR preferences
        dr_preferences = [
            preference.dr_preference for preference in updated_lawyer.dr_preferences
        ]
        # Get expertises 
        expertise = LawyerExpertiseInput(
            married_civil_partners=MarriedCivilPartnersExpertiseGroup(
                expertises=[expertise.expertise for expertise in updated_lawyer.expertises if expertise.expertise.relationship_type == RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS],
                other = [
                    other
                    for other in (updated_lawyer.expertises_other or {}).get('married_civil_partners', [])
                ]
            ),
            cohabitees=CohabiteesExpertiseGroup(
                expertises=[expertise.expertise for expertise in updated_lawyer.expertises if expertise.expertise.relationship_type == RelationshipTypeEnum.COHABITEES],
                other = [
                    other
                    for other in (updated_lawyer.expertises_other or {}).get('cohabitees', [])
                ]
            )
        )

        # Get accredited specialisms
        accredited_specialisms = [
            accredited_specialism.accredited_specialism for accredited_specialism in updated_lawyer.accredited_specialisms
        ]


        # Generate photo URLs from folder path
        photos = generate_photo_urls(updated_lawyer.photo_url)
        # Return null if no photos available
        photos = photos if photos else None

        lawfirm = updated_lawyer.lawyer_law_firms[0].law_firm if updated_lawyer.lawyer_law_firms else None
        logos = generate_photo_urls(lawfirm.logo) if lawfirm else None
        logos = logos if logos else None

        lawyer_response = LawyerResponse(
            id=str(updated_lawyer.id),
            first_name=updated_lawyer.user.first_name,
            last_name=updated_lawyer.user.last_name,
            email=updated_lawyer.user.email,
            phone=updated_lawyer.user.phone,
            gender=updated_lawyer.user.gender,
            # gender_other=updated_lawyer.user.gender_other,
            status=updated_lawyer.status,
            address_line_1=updated_lawyer.address_line_1,
            address_line_2=updated_lawyer.address_line_2,
            city=updated_lawyer.city,
            county=updated_lawyer.county,
            country=updated_lawyer.country,
            postal_code=updated_lawyer.postal_code,
            reg_no=updated_lawyer.reg_no,
            sra_number=updated_lawyer.sra_number,
            bar_number=updated_lawyer.bar_number,
            regulator=updated_lawyer.regulator,
            regulator_other=updated_lawyer.regulator_other,
            admitted_date_solicitor=updated_lawyer.admitted_date_solicitor,
            called_date_barrister=updated_lawyer.called_date_barrister,
            admitted_date_cliex=updated_lawyer.admitted_date_cliex,
            joined_at=updated_lawyer.joined_at,
            left_at=updated_lawyer.left_at,
            about=updated_lawyer.about,
            photo_urls=photos,
            # accredited_specialisations=updated_lawyer.accredited_specialisations,
            testimonial=updated_lawyer.testimonial,
            linkedin_url=updated_lawyer.linkedin_url,
            hourly_rate=updated_lawyer.hourly_rate,
            charge_first_consultation=updated_lawyer.charge_first_consultation,
            conflict_level_disinclination=updated_lawyer.conflict_level_disinclination,
            pi_insurance=updated_lawyer.pi_insurance,
            user_id=str(updated_lawyer.user_id),
            expert_types=expert_types,
            relationship_types=relationship_types,
            matter_types=matter_types,
            dr_preferences=dr_preferences,
            expertises=expertise,
            accredited_specialisms=accredited_specialisms,
            accredited_specialism_other=updated_lawyer.accredited_specialism_other,
            created_at=updated_lawyer.created_at,
            updated_at=updated_lawyer.updated_at,
            experience=calculate_lawyer_experience(updated_lawyer),
            lawfirms=LawFirmData(id=str(lawfirm.id), name=lawfirm.name, logos=logos) if lawfirm else None,
            needs_password_setup=not bool(updated_lawyer.user.password),
        )

        # Prepare success messages
        messages = [ResponseMessage(success=True, message="Expert updated successfully")]

        # Add photo processing status message only if photo was provided
        if request_data.photo_url:
            if not photo_processing_success:
                logger.error(f"Expert updated successfully, but photo processing failed for expert ID: {updated_lawyer.id}")
        return BaseResponse(
            success=True,
            message=messages,
            data=lawyer_response,
        )
    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Failed to update expert: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to update expert"},
        ) from e


@router.get(
    "/lawyer",
    response_model=BaseResponse[LawyerListResponse],
    summary="Search experts",
    description="Search experts with filters, pagination, and ordering using query parameters",
)
async def search_lawyers_endpoint(
    search_request: LawyerSearchRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BaseResponse[LawyerListResponse]:
    """Search experts with filters and pagination using GET method."""
    try:
        lawyers, total_count = search_lawyer_service(
            db, search_request
        )

        lawyer_responses = [_build_lawyer_response(lawyer) for lawyer in lawyers]

        if total_count == 0:
            message = "No data found"
        else:
            message = f"Found {total_count} expert(s)"

        return BaseResponse(
            success=True,
            message=[ResponseMessage(success=True, message=message)],
            data=LawyerListResponse(
                total_count=total_count,
                records_in_page=len(lawyer_responses),
                items=lawyer_responses,
            ),
        )
    except HTTPException as e1:
        logging.exception(f"Failed to search lawyers HTTPException: {e1!s}")        
        raise
    except Exception as e:
        logging.exception(f"Failed to search experts: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to search experts"},
        ) from e


@router.get(
    "/lawyer/{lawyer_id}",
    response_model=BaseResponse[LawyerResponse],
    summary="Get expert by ID",
    description="Get a specific expert by their ID",
)
async def get_lawyer_by_id_endpoint(
    lawyer_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BaseResponse[LawyerResponse]:
    """Get a lawyer by ID."""
    try:
        # Decrypt the ID
        from app.utils.encryption import decrypt_id

        decrypted_id = decrypt_id(lawyer_id)
        if not decrypted_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Invalid expert ID format"},
            )

        lawyer = get_lawyer_by_id_service(db, decrypted_id, current_user)
        lawyer_response = _build_lawyer_response(lawyer)

        return BaseResponse(
            success=True,
            message=[
                ResponseMessage(success=True, message="Expert retrieved successfully")
            ],
            data=lawyer_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Failed to get expert: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to get Expert"},
        ) from e


@router.get(
    "/lawyer-cards",
    response_model=BaseResponse[LawyerListResponse],
    summary="Fetch lawyer cards",
    description=(
        "Fetch up to 4 unique active expert profiles for home page cards. "
        "Profiles are chosen at random and shuffled. At least one male expert "
        "is included when an active male profile exists."
    ),
)
async def fetch_lawyer_cards_endpoint(
    db: Session = Depends(get_db),
) -> BaseResponse[LawyerListResponse]:
    """Fetch lawyer details for home page cards."""
    try:
        lawyers = get_lawyer_cards_service(db)
        lawyer_responses = [_build_lawyer_response(lawyer) for lawyer in lawyers]
        total_count = len(lawyer_responses)

        if total_count == 0:
            message = "No data found"
        else:
            message = f"Found {total_count} expert(s)"

        return BaseResponse(
            success=True,
            message=[ResponseMessage(success=True, message=message)],
            data=LawyerListResponse(
                total_count=total_count,
                records_in_page=len(lawyer_responses),
                items=lawyer_responses,
            ),
        )
    except HTTPException as e1:
        logging.exception(f"Failed to fetch lawyers HTTPException: {e1!s}")        
        raise
    except Exception as e:
        logging.exception(f"Failed to fetch lawyers: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to fetch lawyers"},
        ) from e