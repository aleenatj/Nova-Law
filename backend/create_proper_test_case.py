#!/usr/bin/env python3
"""
Create a proper test case with both KYC and RESOLVE form answers with correct key-value structure.
"""

import sys
import os
import json
from datetime import date, datetime
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import (
    Case,
    CaseCustomer,
    CaseEngage,
    CaseResolve,
    Customer,
    Engage,
    EngageQuestionAnswers,
    QuestionAnswers,
    Resolve,
    ResolveQuestionAnswers,
    User,
)
from app.enums.case import CasePriorityEnum, CaseStatusEnum, CaseTypeEnum
from app.enums.resolve import ResolveStatusEnum
from app.enums.user import StatusEnum
from app.utils.encryption import encrypt_id


def create_proper_test_user(db: Session) -> User:
    """Create a test user with unique email."""
    import time
    timestamp = int(time.time())
    
    user = User(
        email=f"test.customer.{timestamp}@example.com",
        first_name="John",
        last_name="Doe",
        password="hashed_password_123",
        status=StatusEnum.ACTIVE
    )
    db.add(user)
    db.flush()
    return user


def create_proper_test_customer(db: Session, user: User) -> Customer:
    """Create a test customer."""
    customer = Customer(
        user_id=user.id,
        status=StatusEnum.ACTIVE,
        address_line1="123 Test Street",
        city="Test City",
        postal_code="12345",
        country="Test Country"
    )
    db.add(customer)
    db.flush()
    return customer


def create_proper_test_case(db: Session, customer: Customer) -> Case:
    """Create a test case."""
    case = Case(
        start_date=date.today(),
        case_type=CaseTypeEnum.FAMILY_LAW,
        priority=CasePriorityEnum.HIGH,
        status=CaseStatusEnum.OPEN
    )
    db.add(case)
    db.flush()
    
    # Link case to customer
    case_customer = CaseCustomer(
        case_id=case.id,
        customer_id=customer.id
    )
    db.add(case_customer)
    db.flush()
    
    return case


def create_proper_kyc_data(db: Session, case: Case, user: User) -> None:
    """Create proper KYC data with correct key-value structure."""
    # Create Engage
    engage = Engage(user_id=user.id)
    db.add(engage)
    db.flush()
    
    # Link engage to case
    case_engage = CaseEngage(
        case_id=case.id,
        engage_id=engage.id
    )
    db.add(case_engage)
    
    # KYC question answers with proper structure
    kyc_answers = [
        {
            "identifier": 1,
            "answer": [{"value": "John Doe"}],
            "version": "1",
            "order": 1
        },
        {
            "identifier": 2,
            "answer": [{"value": "Jane Smith"}],
            "version": "1",
            "order": 2
        },
        {
            "identifier": 4,
            "answer": [
                {"key": "yes_court_proceedings", "value": "Yes, Court proceedings"},
                {"key": "yes_collaborative_model", "value": "Yes, Collaborative Model"}
            ],
            "version": "1",
            "order": 4
        },
        {
            "identifier": 7,
            "answer": [{"value": "yes"}],
            "version": "1",
            "order": 7
        }
    ]
    
    for ans_data in kyc_answers:
        qa = QuestionAnswers(
            question_identifier=float(ans_data["identifier"]),
            answer=json.dumps(ans_data["answer"]),
            version=ans_data["version"],
            question_order=ans_data["order"]
        )
        db.add(qa)
        db.flush()
        
        eqa = EngageQuestionAnswers(
            engage_id=engage.id,
            question_answer_id=qa.id
        )
        db.add(eqa)


def create_proper_resolve_data(db: Session, case: Case, customer: Customer, user: User) -> None:
    """Create proper RESOLVE data with correct key-value structure."""
    # Create Resolve
    resolve = Resolve(
        resolve_date=date.today(),
        user_id=user.id,
        customer_id=customer.id,
        status=ResolveStatusEnum.COMPLETED,
        result_reference_id="collaborative",
        result_version="1",
        customer_name="John Doe",
        partner_name="Jane Smith"
    )
    db.add(resolve)
    db.flush()
    
    # Link resolve to case
    case_resolve = CaseResolve(
        case_id=case.id,
        resolve_id=resolve.id
    )
    db.add(case_resolve)
    
    # RESOLVE question answers with proper structure
    resolve_answers = [
        {
            "identifier": 6,
            "answer": [{"value": "court_proceedings_in_court"}],
            "version": "1",
            "order": 6,
            "score": 1.0
        },
        {
            "identifier": 13,
            "answer": [{"value": "between_40k_and_75k"}],
            "version": "1",
            "order": 13,
            "score": 3.0
        },
        {
            "identifier": 14,
            "answer": [
                {"key": "disability_or_physical", "value": "Disability or physical/mental health"},
                {"key": "police_or_social_services", "value": "Police or Social Services involvement"}
            ],
            "version": "1",
            "order": 14,
            "score": 2.0
        },
        {
            "identifier": 19,
            "answer": [
                {"key": "business_assets", "value": "Business assets"},
                {"key": "pensions", "value": "Pensions"},
                {"key": "assets_abroad", "value": "Assets abroad"}
            ],
            "version": "1",
            "order": 19,
            "score": 0.0
        },
        {
            "identifier": 16,
            "answer": [
                {"key": "domestic_abuse", "value": "Domestic abuse or coercive control"},
                {"key": "hiding_money", "value": "Hiding money or assets from you or a previous partner"}
            ],
            "version": "1",
            "order": 16,
            "score": 5.0
        }
    ]
    
    for ans_data in resolve_answers:
        qa = QuestionAnswers(
            question_identifier=float(ans_data["identifier"]),
            answer=json.dumps(ans_data["answer"]),
            version=ans_data["version"],
            question_order=ans_data["order"]
        )
        db.add(qa)
        db.flush()
        
        rqa = ResolveQuestionAnswers(
            resolve_id=resolve.id,
            question_answer_id=qa.id,
            score=ans_data["score"]
        )
        db.add(rqa)


def test_case_summary(db: Session, case_id: int):
    """Test the case summary function with the new case."""
    print(f"\n🧪 Testing case summary function with Case ID {case_id}...")
    
    try:
        from app.db.services.general import get_case_summary
        summary = get_case_summary(db, case_id)
        
        print(f"✅ Case summary generated successfully!")
        print(f"   Summary contains {len(summary['questionnaire'])} questions/answers")
        
        # Show the complete summary
        print(f"\n📝 Case Summary for Case ID {case_id}:")
        print("=" * 80)
        
        for i, item in enumerate(summary['questionnaire'], 1):
            print(f"{i:2d}. Q: {item['question']}")
            print(f"    A: {item['answer']}")
            print("-" * 60)
        
        return summary
        
    except Exception as e:
        print(f"❌ Error testing case summary: {e}")
        import traceback
        traceback.print_exc()
        return {}


def main():
    """Main function to create proper test case."""
    print("🏗️  Creating proper test case with correct key-value structure...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create test data
        print("1. Creating test user...")
        user = create_proper_test_user(db)
        print(f"   ✅ User created with ID: {user.id}")
        
        print("2. Creating test customer...")
        customer = create_proper_test_customer(db, user)
        print(f"   ✅ Customer created with ID: {customer.id}")
        
        print("3. Creating test case...")
        case = create_proper_test_case(db, customer)
        print(f"   ✅ Case created with ID: {case.id}, Case Number: {case.case_no}")
        
        print("4. Creating KYC data with proper structure...")
        create_proper_kyc_data(db, case, user)
        print("   ✅ KYC data created with proper key-value structure")
        
        print("5. Creating RESOLVE data with proper structure...")
        create_proper_resolve_data(db, case, customer, user)
        print("   ✅ RESOLVE data created with proper key-value structure")
        
        # Commit all changes
        db.commit()
        print("\n🎉 Proper test case created successfully!")
        print(f"📋 Case ID: {case.id}")
        print(f"📋 Case Number: {case.case_no}")
        print(f"👤 Customer: John Doe")
        print(f"👤 Partner: Jane Smith")
        
        # Test the case summary function
        summary = test_case_summary(db, case.id)
        
        if summary:
            # Get encrypted case ID
            try:
                encrypted_id = encrypt_id(case.id)
                print(f"\n🔐 Encrypted Case ID: {encrypted_id}")
                print(f"   Original Case ID: {case.id}")
                print(f"   Use this encrypted ID for testing!")
            except Exception as e:
                print(f"❌ Error encrypting case ID: {e}")
                print(f"📋 Use Case ID: {case.id} (unencrypted)")
        
    except Exception as e:
        print(f"❌ Error creating test case: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
