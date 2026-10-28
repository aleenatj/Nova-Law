"""add_expertise_enum_type

Revision ID: cfad85f0c5bf
Revises: 43f7bb8b9130
Create Date: 2026-01-21 10:55:40.407777

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cfad85f0c5bf'
down_revision = '43f7bb8b9130'
branch_labels = None
depends_on = None


from sqlalchemy.dialects.postgresql import ENUM

def upgrade() -> None:
    # Create PostgreSQL enum type for expertise if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'expertise_enum') THEN
                CREATE TYPE expertise_enum AS ENUM (
                    'DIVORCE_AND_SEPARATION',
                    'FINANCIAL_CLAIMS',
                    'OVERSEAS_FINANCIAL_CLAIMS',
                    'CHILD_ARRANGEMENTS',
                    'CHILDREN_DOMESTIC_RELOCATION',
                    'CHILDREN_INTERNATIONAL_RELOCATION',
                    'INHERITANCE_ACT_CLAIMS',
                    'PRE_NUPTIAL_PRE_CIVIL_PARTNERSHIP_AGREEMENTS',
                    'POST_NUPTIAL_POST_CIVIL_PARTNERSHIP_AGREEMENTS',
                    'SEPARATION_AGREEMENTS',
                    'COHABITATION_CHILD_ARRANGEMENTS',
                    'COHABITATION_CHILDREN_DOMESTIC_RELOCATION',
                    'COHABITATION_CHILDREN_INTERNATIONAL_RELOCATION',
                    'COHABITATION_FINANCIAL_CLAIMS',
                    'LIVING_TOGETHER_AGREEMENTS',
                    'SCHEDULE_I_CLAIMS',
                    'COHABITATION_INHERITANCE_ACT_CLAIMS',
                    'OTHER_MARRIED_CIVIL_PARTNERS',
                    'OTHER_COHABITEES'
                );
            END IF;
        END $$;
    """)
    
    expertise_enum = ENUM(
        name="expertise_enum",
        create_type=False,
    )    
    op.create_table('lawyer_expertise',
    sa.Column('lawyer_id', sa.Integer(), nullable=False),
    sa.Column("expertise", expertise_enum, nullable=False),
    sa.ForeignKeyConstraint(['lawyer_id'], ['lawyer.id'], ),
    sa.PrimaryKeyConstraint('lawyer_id', 'expertise')
    )
    op.add_column('lawyer', sa.Column('expert_types_other', sa.String(500), nullable=True))
    op.add_column('lawyer', sa.Column('expertises_other', sa.JSON(), nullable=True))
    op.add_column('lawyer', sa.Column('regulator_other', sa.String(255), nullable=True))
    op.add_column('lawyer', sa.Column('accredited_specialism_other', sa.JSON(), nullable=True))
    op.add_column('lawyer_onboarding', sa.Column('matter_types', sa.JSON(), nullable=True))
    op.add_column('lawyer_onboarding', sa.Column('accredited_specialism_other', sa.JSON(), nullable=True))
    
    # Create PostgreSQL enum type for accredited specialism if it doesn't exist    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'accredited_specialism_enum') THEN
                CREATE TYPE accredited_specialism_enum AS ENUM (
                    'RESOLUTION_ACCREDITED_SPECIALIST',
                    'LAW_SOCIETY_ACCREDITED_SPECIALIST',
                    'FMC_ACCREDITED_MEDIATOR',
                    'CIARB_ACCREDITED_ARBITRATOR',
                    'OTHER'
                );
            END IF;
        END $$;
    """)
    accredited_specialism_enum = ENUM(
        name="accredited_specialism_enum",
        create_type=False,
    )
    op.create_table('lawyer_accredited_specialism',
    sa.Column('lawyer_id', sa.Integer(), nullable=False),
    sa.Column("accredited_specialism", accredited_specialism_enum, nullable=False),
    sa.ForeignKeyConstraint(['lawyer_id'], ['lawyer.id'], ),
    sa.PrimaryKeyConstraint('lawyer_id', 'accredited_specialism')
    )
    
    # Migrate data from accredited_specialisations to lawyer_expertise and expertises_other
    op.execute("""
        DO $$
        DECLARE
            lawyer_rec RECORD;
            specialisation_value TEXT;
            specialisation_array TEXT[];
            matched_expertise TEXT;
            other_values TEXT[] := ARRAY[]::TEXT[];
            has_other_values BOOLEAN := FALSE;
            current_expertises_other JSONB;
            normalized_value TEXT;
            enum_name TEXT;
            -- Array of all expertise enum names
            expertise_enum_names TEXT[] := ARRAY[
                'DIVORCE_AND_SEPARATION',
                'FINANCIAL_CLAIMS',
                'OVERSEAS_FINANCIAL_CLAIMS',
                'CHILD_ARRANGEMENTS',
                'CHILDREN_DOMESTIC_RELOCATION',
                'CHILDREN_INTERNATIONAL_RELOCATION',
                'INHERITANCE_ACT_CLAIMS',
                'PRE_NUPTIAL_PRE_CIVIL_PARTNERSHIP_AGREEMENTS',
                'POST_NUPTIAL_POST_CIVIL_PARTNERSHIP_AGREEMENTS',
                'SEPARATION_AGREEMENTS',
                'COHABITATION_CHILD_ARRANGEMENTS',
                'COHABITATION_CHILDREN_DOMESTIC_RELOCATION',
                'COHABITATION_CHILDREN_INTERNATIONAL_RELOCATION',
                'COHABITATION_FINANCIAL_CLAIMS',
                'LIVING_TOGETHER_AGREEMENTS',
                'SCHEDULE_I_CLAIMS',
                'COHABITATION_INHERITANCE_ACT_CLAIMS',
                'OTHER_MARRIED_CIVIL_PARTNERS',
                'OTHER_COHABITEES'
            ];
        BEGIN
            -- Loop through each lawyer with non-null accredited_specialisations
            FOR lawyer_rec IN 
                SELECT id, accredited_specialisations, expertises_other
                FROM lawyer
                WHERE accredited_specialisations IS NOT NULL 
                AND accredited_specialisations != ''
            LOOP
                -- Reset variables for each lawyer
                other_values := ARRAY[]::TEXT[];
                has_other_values := FALSE;
                current_expertises_other := COALESCE(lawyer_rec.expertises_other::JSONB, '{"married_civil_partners": [], "cohabitees": []}'::JSONB);
                
                -- Split accredited_specialisations by comma
                specialisation_array := string_to_array(TRIM(lawyer_rec.accredited_specialisations), ',');
                
                -- Loop through each specialisation value
                FOREACH specialisation_value IN ARRAY specialisation_array
                LOOP
                    specialisation_value := TRIM(specialisation_value);
                    
                    IF specialisation_value = '' THEN
                        CONTINUE;
                    END IF;
                    
                    -- Normalize the value for matching (uppercase, replace spaces/hyphens/special chars with underscores)
                    normalized_value := UPPER(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(specialisation_value, '[\\s-]', '_', 'g'), '[&]', 'AND', 'g'), '[^A-Z0-9_]', '', 'g'));
                    
                    -- Check if the normalized value matches any expertise enum name
                    matched_expertise := NULL;
                    FOREACH enum_name IN ARRAY expertise_enum_names
                    LOOP
                        IF normalized_value = enum_name THEN
                            matched_expertise := enum_name;
                            EXIT;
                        END IF;
                    END LOOP;
                    
                    -- If match found, insert into lawyer_expertise (avoid duplicates)
                    IF matched_expertise IS NOT NULL THEN
                        BEGIN
                            INSERT INTO lawyer_expertise (lawyer_id, expertise)
                            VALUES (lawyer_rec.id, matched_expertise::expertise_enum)
                            ON CONFLICT (lawyer_id, expertise) DO NOTHING;
                        EXCEPTION
                            WHEN OTHERS THEN
                                -- If enum value doesn't exist or table doesn't exist, treat as no match
                                matched_expertise := NULL;
                        END;
                    END IF;
                    
                    -- If no match found, add to other_values
                    IF matched_expertise IS NULL THEN
                        other_values := array_append(other_values, specialisation_value);
                        has_other_values := TRUE;
                    END IF;
                END LOOP;
                
                -- If there are other values, update expertises_other
                IF has_other_values THEN
                    -- Merge with existing married_civil_partners array
                    current_expertises_other := jsonb_set(
                        current_expertises_other,
                        '{married_civil_partners}',
                        COALESCE(current_expertises_other->'married_civil_partners', '[]'::JSONB) || to_jsonb(other_values),
                        TRUE
                    );
                    
                    -- Update the lawyer record
                    UPDATE lawyer
                    SET expertises_other = current_expertises_other
                    WHERE id = lawyer_rec.id;
                    
                    -- Add OTHER_MARRIED_CIVIL_PARTNERS to lawyer_expertise if not already present
                    BEGIN
                        INSERT INTO lawyer_expertise (lawyer_id, expertise)
                        VALUES (lawyer_rec.id, 'OTHER_MARRIED_CIVIL_PARTNERS'::expertise_enum)
                        ON CONFLICT (lawyer_id, expertise) DO NOTHING;
                    EXCEPTION
                        WHEN OTHERS THEN
                            -- If enum doesn't exist or table doesn't exist, skip
                            NULL;
                    END;
                END IF;
            END LOOP;
        END $$;
    """)
    
    op.drop_column('lawyer', 'accredited_specialisations')

def downgrade() -> None:
    
    # Drop the enum type
    # Note: This will fail if any columns are using this enum type
    # You need to drop all columns/tables using this type first
    op.drop_column('lawyer', 'expertises_other')
    op.drop_column('lawyer', 'expert_types_other')
    op.drop_column('lawyer', 'regulator_other')
    op.drop_column('lawyer', 'accredited_specialism_other')
    op.drop_column('lawyer_onboarding', 'matter_types')
    op.drop_column('lawyer_onboarding', 'accredited_specialism_other')
    op.drop_table('lawyer_expertise')
    op.execute("DROP TYPE IF EXISTS expertise_enum;")
    # Reverse migration: combine lawyer_expertise enum values and expertises_other
    # back into accredited_specialisations as comma-separated values
    op.add_column('lawyer', sa.Column('accredited_specialisations', sa.Text(), nullable=True))
    op.execute("""
        DO $$
        DECLARE
            lawyer_rec RECORD;
            expertise_value TEXT;
            expertise_values TEXT[] := ARRAY[]::TEXT[];
            other_values TEXT[] := ARRAY[]::TEXT[];
            combined_values TEXT[];
            enum_value_mapping JSONB := '{
                "DIVORCE_AND_SEPARATION": "Divorce and Separation",
                "FINANCIAL_CLAIMS": "Financial Claims",
                "OVERSEAS_FINANCIAL_CLAIMS": "Overseas Financial claims",
                "CHILD_ARRANGEMENTS": "Child arrangements",
                "CHILDREN_DOMESTIC_RELOCATION": "Children domestic relocation",
                "CHILDREN_INTERNATIONAL_RELOCATION": "Children international relocation",
                "INHERITANCE_ACT_CLAIMS": "Inheritance Act claims",
                "PRE_NUPTIAL_PRE_CIVIL_PARTNERSHIP_AGREEMENTS": "Pre-nuptial & pre-civil partnership agreements",
                "POST_NUPTIAL_POST_CIVIL_PARTNERSHIP_AGREEMENTS": "Post-nuptial and post-civil partnership agreements",
                "SEPARATION_AGREEMENTS": "Separation agreements",
                "COHABITATION_CHILD_ARRANGEMENTS": "Cohabitation - Child arrangements",
                "COHABITATION_CHILDREN_DOMESTIC_RELOCATION": "Cohabitation - Children domestic relocation",
                "COHABITATION_CHILDREN_INTERNATIONAL_RELOCATION": "Cohabitation - Children international relocation",
                "COHABITATION_FINANCIAL_CLAIMS": "Cohabitation - Financial Claims",
                "LIVING_TOGETHER_AGREEMENTS": "Living together agreements",
                "SCHEDULE_I_CLAIMS": "Schedule I claims",
                "COHABITATION_INHERITANCE_ACT_CLAIMS": "Cohabitation - Inheritance Act claims",
                "OTHER_MARRIED_CIVIL_PARTNERS": "Other (Married and Civil Partners)",
                "OTHER_COHABITEES": "Other (Cohabitees)"
            }'::JSONB;
            mapped_value TEXT;
        BEGIN
            -- Loop through each lawyer that has expertises or expertises_other
            FOR lawyer_rec IN 
                SELECT l.id, l.expertises_other
                FROM lawyer l
                WHERE EXISTS (
                    SELECT 1 FROM lawyer_expertise le WHERE le.lawyer_id = l.id
                ) OR l.expertises_other IS NOT NULL
            LOOP
                -- Reset arrays for each lawyer
                expertise_values := ARRAY[]::TEXT[];
                other_values := ARRAY[]::TEXT[];
                
                -- Get expertise enum values from lawyer_expertise table
                -- Exclude OTHER_MARRIED_CIVIL_PARTNERS and OTHER_COHABITEES as they are special "Other" values
                FOR expertise_value IN 
                    SELECT expertise::TEXT
                    FROM lawyer_expertise
                    WHERE lawyer_id = lawyer_rec.id
                    AND expertise::TEXT NOT IN ('OTHER_MARRIED_CIVIL_PARTNERS', 'OTHER_COHABITEES')
                LOOP
                    -- Map enum name to enum value using the mapping
                    mapped_value := enum_value_mapping->>expertise_value;
                    
                    -- If mapping exists, use it; otherwise use the enum name as fallback
                    IF mapped_value IS NOT NULL THEN
                        expertise_values := array_append(expertise_values, mapped_value);
                    ELSE
                        expertise_values := array_append(expertise_values, expertise_value);
                    END IF;
                END LOOP;
                
                -- Get other values from expertises_other->married_civil_partners
                IF lawyer_rec.expertises_other IS NOT NULL THEN
                    SELECT ARRAY(
                        SELECT jsonb_array_elements_text(
                            COALESCE((lawyer_rec.expertises_other::JSONB)->'married_civil_partners', '[]'::JSONB)
                        )
                    ) INTO other_values;
                END IF;
                
                -- Combine expertise values and other values
                combined_values := expertise_values || other_values;
                
                -- Update accredited_specialisations with comma-separated values
                IF array_length(combined_values, 1) > 0 THEN
                    UPDATE lawyer
                    SET accredited_specialisations = array_to_string(combined_values, ', ')
                    WHERE id = lawyer_rec.id;
                END IF;
            END LOOP;
        END $$;
    """)
    op.drop_table('lawyer_accredited_specialism')
    op.execute("DROP TYPE IF EXISTS accredited_specialism_enum;")
