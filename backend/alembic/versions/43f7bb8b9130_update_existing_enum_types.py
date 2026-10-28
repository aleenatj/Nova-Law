"""update_existing_enum_types

Revision ID: 43f7bb8b9130
Revises: 7c9a71aa75c8
Create Date: 2026-01-21 11:41:15.473355

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43f7bb8b9130'
down_revision = '7c9a71aa75c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update PostgreSQL enum types to use enum keys instead of values.
    
    Uses ALTER TYPE ... RENAME VALUE to rename enum values directly.
    This automatically updates all referenced records.
    """
    
    # 1. Update relationship_type_enum: values -> keys
    op.execute("""
        DO $$
        BEGIN
            -- Rename enum values to keys
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Married and Civil Partners' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'relationship_type_enum')
            ) THEN
                ALTER TYPE relationship_type_enum RENAME VALUE 'Married and Civil Partners' TO 'MARRIED_CIVIL_PARTNERS';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Cohabitees' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'relationship_type_enum')
            ) THEN
                ALTER TYPE relationship_type_enum RENAME VALUE 'Cohabitees' TO 'COHABITEES';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Parental relationships' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'relationship_type_enum')
            ) THEN
                ALTER TYPE relationship_type_enum RENAME VALUE 'Parental relationships' TO 'PARENTAL_RELATIONSHIPS';
            END IF;
        END $$;
    """)
    
    # 2. Update matter_type_enum: values -> keys
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Financial Claims' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'matter_type_enum')
            ) THEN
                ALTER TYPE matter_type_enum RENAME VALUE 'Financial Claims' TO 'FINANCIAL_CLAIMS';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Children' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'matter_type_enum')
            ) THEN
                ALTER TYPE matter_type_enum RENAME VALUE 'Children' TO 'CHILDREN';
            END IF;
        END $$;
    """)
    
    # 3. Update lawyer_regulator: values -> keys
    op.execute("""
        DO $$
        BEGIN
            -- SRA and BSB stay the same, just ensure they're uppercase
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'SRA' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lawyer_regulator')
            ) THEN
                -- Already correct, no change needed
                NULL;
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'BSB' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lawyer_regulator')
            ) THEN
                -- Already correct, no change needed
                NULL;
            END IF;
            
            -- Rename 'CLIEx Regulation' or 'Cilex Regulation' to 'CILEX'
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'CLIEx Regulation' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lawyer_regulator')
            ) THEN
                ALTER TYPE lawyer_regulator RENAME VALUE 'CLIEx Regulation' TO 'CILEX';
            ELSIF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Cilex Regulation' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lawyer_regulator')
            ) THEN
                ALTER TYPE lawyer_regulator RENAME VALUE 'Cilex Regulation' TO 'CILEX';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Other' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lawyer_regulator')
            ) THEN
                ALTER TYPE lawyer_regulator RENAME VALUE 'Other' TO 'OTHER';
            END IF;
        END $$;
    """)
    
    # 4. Update lawyer_conflict_level: values -> keys
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Medium conflict' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lawyer_conflict_level')
            ) THEN
                ALTER TYPE lawyer_conflict_level RENAME VALUE 'Medium conflict' TO 'MEDIUM_CONFLICT';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'High Conflict' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lawyer_conflict_level')
            ) THEN
                ALTER TYPE lawyer_conflict_level RENAME VALUE 'High Conflict' TO 'HIGH_CONFLICT';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Implacable hostility' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lawyer_conflict_level')
            ) THEN
                ALTER TYPE lawyer_conflict_level RENAME VALUE 'Implacable hostility' TO 'IMPLACABLE_HOSTILITY';
            END IF;
        END $$;
    """)
    
    # 5. Update gender_enum: values -> keys and add new values
    op.execute("""
        DO $$
        BEGIN
            -- Rename existing values
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'MALE' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'gender_enum')
            ) THEN
                -- Already uppercase, no change needed
                NULL;
            ELSIF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Male' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'gender_enum')
            ) THEN
                ALTER TYPE gender_enum RENAME VALUE 'Male' TO 'MALE';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'FEMALE' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'gender_enum')
            ) THEN
                -- Already uppercase, no change needed
                NULL;
            ELSIF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Female' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'gender_enum')
            ) THEN
                ALTER TYPE gender_enum RENAME VALUE 'Female' TO 'FEMALE';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'OTHER' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'gender_enum')
            ) THEN
                ALTER TYPE gender_enum RENAME VALUE 'OTHER' TO 'NON_BINARY';
                NULL;
            ELSIF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Other' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'gender_enum')
            ) THEN
                ALTER TYPE gender_enum RENAME VALUE 'Other' TO 'NON_BINARY';
            END IF;
            
            -- Add new values if they don't exist
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'NON_BINARY' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'gender_enum')
            ) THEN
                ALTER TYPE gender_enum ADD VALUE 'NON_BINARY';
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'PREFER_NOT_TO_SAY' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'gender_enum')
            ) THEN
                ALTER TYPE gender_enum ADD VALUE 'PREFER_NOT_TO_SAY';
            END IF;
        END $$;
    """)
    
    # 6. Update expert_type_enum: values -> keys
    op.execute("""
        DO $$
        BEGIN
            -- Rename lowercase/incorrect case to proper keys
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'solicitor' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'solicitor' TO 'SOLICITOR';
            ELSIF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Solicitor' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'Solicitor' TO 'SOLICITOR';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'barrister' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'barrister' TO 'BARRISTER';
            ELSIF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Barrister' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'Barrister' TO 'BARRISTER';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'CILEx' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'CILEx' TO 'CILEX';
            ELSIF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Cilex' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'Cilex' TO 'CILEX';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Lawyer Mediator' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'Lawyer Mediator' TO 'LAWYER_MEDIATOR';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Non-Lawyer Mediator' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'Non-Lawyer Mediator' TO 'MEDIATOR';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Arbitrator' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'Arbitrator' TO 'ARBITRATOR';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Divorce Coach' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'Divorce Coach' TO 'DIVORCE_COACH';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Family Consultant' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'Family Consultant' TO 'FAMILY_CONSULTANT';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Other' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'expert_type_enum')
            ) THEN
                ALTER TYPE expert_type_enum RENAME VALUE 'Other' TO 'OTHER';
            END IF;
        END $$;
    """)
    
    # 7. Update dr_preference_enum: values -> keys
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Direct Negotiation' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Direct Negotiation' TO 'DIRECT_NEGOTIATION';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Mediation' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Mediation' TO 'MEDIATION';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'One Lawyer One Couple' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'One Lawyer One Couple' TO 'ONE_LAWYER_ONE_COUPLE';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Collaborative' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Collaborative' TO 'COLLABORATIVE';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Hybrid Mediation-Support' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Hybrid Mediation-Support' TO 'HYBRID_MEDIATION_SUPPORT';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Hybrid Mediation-Mediator' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Hybrid Mediation-Mediator' TO 'HYBRID_MEDIATION_MEDIATOR';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Lawyer Negotiation' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Lawyer Negotiation' TO 'LAWYER_NEGOTIATION';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Early Neutral Evaluation/Private FDR-Support' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Early Neutral Evaluation/Private FDR-Support' TO 'EARLY_NEUTRAL_EVALUATION_SUPPORT';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Early Neutral Evaluation/Private FDR-Evaluator' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Early Neutral Evaluation/Private FDR-Evaluator' TO 'EARLY_NEUTRAL_EVALUATION_EVALUATOR';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Arbitration-Support' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Arbitration-Support' TO 'ARBITRATION_SUPPORT';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Arbitration-Arbitrator' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Arbitration-Arbitrator' TO 'ARBITRATION_ARBITRATOR';
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'Court' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dr_preference_enum')
            ) THEN
                ALTER TYPE dr_preference_enum RENAME VALUE 'Court' TO 'COURT';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Note: Downgrading would require reversing all the RENAME VALUE operations.
    
    This would involve renaming all keys back to their original values.
    For safety, this downgrade is left as a no-op.
    """
    pass
