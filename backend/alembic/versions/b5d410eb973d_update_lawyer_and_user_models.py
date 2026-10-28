"""update_lawyer_and_user_models

Revision ID: b5d410eb973d
Revises: dcaeea9b1b8a
Create Date: 2025-08-28 18:40:21.004919

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b5d410eb973d'
down_revision = 'dcaeea9b1b8a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    
    # Create PostgreSQL enums if they don't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lawyer_status') THEN
                CREATE TYPE lawyer_status AS ENUM ('Active', 'Deactive');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lawyer_regulator') THEN
                CREATE TYPE lawyer_regulator AS ENUM ('SRA', 'BSB', 'CLIEx Regulation', 'Other');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lawyer_conflict_level') THEN
                CREATE TYPE lawyer_conflict_level AS ENUM ('Medium conflict', 'High Conflict', 'Implacable hostility');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'expert_type_enum') THEN
                CREATE TYPE expert_type_enum AS ENUM ('solicitor', 'barrister', 'CILEx', 'Lawyer Mediator', 'Non-Lawyer Mediator', 'Arbitrator', 'Divorce Coach', 'Family Consultant', 'Other');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'relationship_type_enum') THEN
                CREATE TYPE relationship_type_enum AS ENUM ('Married and Civil Partners', 'Cohabitees', 'Parental relationships');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'matter_type_enum') THEN
                CREATE TYPE matter_type_enum AS ENUM ('Financial Claims', 'Children');
            END IF;
        END $$;
    """)
    
    # Create join tables for lawyer multi-select relationships
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lawyer_expert_type') THEN
                CREATE TABLE lawyer_expert_type (
                    lawyer_id INTEGER NOT NULL REFERENCES lawyer(id),
                    expert_type expert_type_enum NOT NULL,
                    PRIMARY KEY (lawyer_id, expert_type)
                );
                CREATE INDEX ix_lawyer_expert_type_lawyer_id ON lawyer_expert_type(lawyer_id);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lawyer_matter_type') THEN
                CREATE TABLE lawyer_matter_type (
                    lawyer_id INTEGER NOT NULL REFERENCES lawyer(id),
                    matter_type matter_type_enum NOT NULL,
                    PRIMARY KEY (lawyer_id, matter_type)
                );
                CREATE INDEX ix_lawyer_matter_type_lawyer_id ON lawyer_matter_type(lawyer_id);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lawyer_relationship_type') THEN
                CREATE TABLE lawyer_relationship_type (
                    lawyer_id INTEGER NOT NULL REFERENCES lawyer(id),
                    relationship_type relationship_type_enum NOT NULL,
                    PRIMARY KEY (lawyer_id, relationship_type)
                );
                CREATE INDEX ix_lawyer_relationship_type_lawyer_id ON lawyer_relationship_type(lawyer_id);
            END IF;
        END $$;
    """)
    
    # Add new columns to lawyer table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='address_line_1') THEN
                ALTER TABLE lawyer ADD COLUMN address_line_1 VARCHAR(255);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='address_line_2') THEN
                ALTER TABLE lawyer ADD COLUMN address_line_2 VARCHAR(255);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='county') THEN
                ALTER TABLE lawyer ADD COLUMN county VARCHAR(100);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='sra_number') THEN
                ALTER TABLE lawyer ADD COLUMN sra_number VARCHAR(100);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='bar_number') THEN
                ALTER TABLE lawyer ADD COLUMN bar_number VARCHAR(100);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='admitted_date_solicitor') THEN
                ALTER TABLE lawyer ADD COLUMN admitted_date_solicitor DATE;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='called_date_barrister') THEN
                ALTER TABLE lawyer ADD COLUMN called_date_barrister DATE;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='admitted_date_cliex') THEN
                ALTER TABLE lawyer ADD COLUMN admitted_date_cliex DATE;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='accredited_specialisations') THEN
                ALTER TABLE lawyer ADD COLUMN accredited_specialisations TEXT;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='testimonial') THEN
                ALTER TABLE lawyer ADD COLUMN testimonial TEXT;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='hourly_rate') THEN
                ALTER TABLE lawyer ADD COLUMN hourly_rate FLOAT DEFAULT 0;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='charge_first_consultation') THEN
                ALTER TABLE lawyer ADD COLUMN charge_first_consultation FLOAT DEFAULT 0;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='conflict_level_disinclination') THEN
                ALTER TABLE lawyer ADD COLUMN conflict_level_disinclination lawyer_conflict_level;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='pi_insurance') THEN
                ALTER TABLE lawyer ADD COLUMN pi_insurance VARCHAR(100);
            END IF;
        END $$;
    """)
    
    # Add missing columns required by the Lawyer model
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='city') THEN
                ALTER TABLE lawyer ADD COLUMN city VARCHAR(100);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='postal_code') THEN
                ALTER TABLE lawyer ADD COLUMN postal_code VARCHAR(20);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='joined_at') THEN
                ALTER TABLE lawyer ADD COLUMN joined_at TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lawyer' AND column_name='left_at') THEN
                ALTER TABLE lawyer ADD COLUMN left_at TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
    """)

    
    # Update existing columns to use new enum types with proper casting
    # Update status column to use new enum values
    op.execute("ALTER TABLE lawyer ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE lawyer ALTER COLUMN status TYPE VARCHAR(20)")
    op.execute("UPDATE lawyer SET status = 'Active' WHERE status = 'ACTIVE'")
    op.execute("UPDATE lawyer SET status = 'Deactive' WHERE status = 'INACTIVE'")
    op.execute("ALTER TABLE lawyer ALTER COLUMN status TYPE lawyer_status USING status::lawyer_status")
    op.execute("ALTER TABLE lawyer ALTER COLUMN status SET DEFAULT 'Active'")
    
    # Update regulator column to use new enum values
    op.execute("ALTER TABLE lawyer ALTER COLUMN regulator TYPE VARCHAR(50)")
    op.execute("UPDATE lawyer SET regulator = 'CLIEx Regulation' WHERE regulator = 'CLIEX_REGULATION'")
    op.execute("ALTER TABLE lawyer ALTER COLUMN regulator TYPE lawyer_regulator USING regulator::lawyer_regulator")
    
    # Update other columns
    op.alter_column('lawyer', 'reg_no',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=100),
               existing_nullable=True)
    op.alter_column('lawyer', 'about',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               existing_nullable=True)
    op.alter_column('lawyer', 'photo_url',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.Text(),
               existing_nullable=True)
    op.alter_column('lawyer', 'linkedin_url',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.String(length=255),
               existing_nullable=True)
    
    # Drop obsolete columns
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'lawyer_reg_no_key'
            ) THEN
                ALTER TABLE lawyer DROP CONSTRAINT lawyer_reg_no_key;
            END IF;
        END $$;
    """)
    op.drop_column('lawyer', 'practice_areas')
    op.drop_column('lawyer', 'address_line2')
    op.drop_column('lawyer', 'state')
    op.drop_column('lawyer', 'lawyer_type')
    op.drop_column('lawyer', 'address_line1')
    op.drop_column('lawyer', 'admitted_or_called_date')
    op.drop_column('lawyer', 'qualifications')
    op.drop_column('lawyer', 'country')
    
    # Add gender_other column to user table
    op.add_column('user', sa.Column('gender_other', sa.String(length=50), nullable=True))
    
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    
    # Remove gender_other column from user table
    op.drop_column('user', 'gender_other')
    
    # Restore obsolete columns to lawyer table
    op.add_column('lawyer', sa.Column('country', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.add_column('lawyer', sa.Column('qualifications', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('lawyer', sa.Column('admitted_or_called_date', sa.DATE(), autoincrement=False, nullable=True))
    op.add_column('lawyer', sa.Column('address_line1', sa.VARCHAR(length=255), autoincrement=False, nullable=True))

    op.add_column('lawyer', sa.Column('state', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.add_column('lawyer', sa.Column('address_line2', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('lawyer', sa.Column('practice_areas', sa.TEXT(), autoincrement=False, nullable=True))
    
    # Create unique constraint conditionally to avoid duplicate key errors
    op.execute("""
        DO $$
        BEGIN
            -- Check if there are any duplicate reg_no values
            IF NOT EXISTS (
                SELECT reg_no, COUNT(*) 
                FROM lawyer 
                WHERE reg_no IS NOT NULL 
                GROUP BY reg_no 
                HAVING COUNT(*) > 1
            ) THEN
                -- Only create the constraint if no duplicates exist
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'lawyer_reg_no_key'
                ) THEN
                    ALTER TABLE lawyer ADD CONSTRAINT lawyer_reg_no_key UNIQUE (reg_no);
                END IF;
            ELSE
                -- Log that constraint cannot be created due to duplicates
                RAISE NOTICE 'Cannot create unique constraint on reg_no due to duplicate values';
            END IF;
        END $$;
    """)
    
    # Restore column types to original
    op.alter_column('lawyer', 'linkedin_url',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=500),
               existing_nullable=True)
    op.alter_column('lawyer', 'photo_url',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=500),
               existing_nullable=True)
    op.alter_column('lawyer', 'about',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               existing_nullable=True)
    
    # Update regulator column to use old enum values with proper casting
    op.execute("ALTER TABLE lawyer ALTER COLUMN regulator TYPE VARCHAR(50)")
    op.execute("UPDATE lawyer SET regulator = 'CLIEX_REGULATION' WHERE regulator = 'CLIEx Regulation'")
    op.execute("ALTER TABLE lawyer ALTER COLUMN regulator TYPE regulator_enum USING regulator::regulator_enum")
    
    op.alter_column('lawyer', 'reg_no',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=50),
               existing_nullable=True)
    
    # Update status column to use old enum values with proper casting
    op.execute("ALTER TABLE lawyer ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE lawyer ALTER COLUMN status TYPE VARCHAR(20)")
    op.execute("UPDATE lawyer SET status = 'ACTIVE' WHERE status = 'Active'")
    op.execute("UPDATE lawyer SET status = 'INACTIVE' WHERE status = 'Deactive'")
    op.execute("ALTER TABLE lawyer ALTER COLUMN status TYPE lawyer_status_enum USING status::lawyer_status_enum")
    op.execute("ALTER TABLE lawyer ALTER COLUMN status SET DEFAULT 'ACTIVE'")
    
    # Drop columns added in this migration
    op.drop_column('lawyer', 'left_at')
    op.drop_column('lawyer', 'joined_at')
    op.drop_column('lawyer', 'postal_code')
    op.drop_column('lawyer', 'city')
    op.drop_column('lawyer', 'pi_insurance')
    op.drop_column('lawyer', 'conflict_level_disinclination')
    op.drop_column('lawyer', 'charge_first_consultation')
    op.drop_column('lawyer', 'hourly_rate')
    op.drop_column('lawyer', 'testimonial')
    op.drop_column('lawyer', 'accredited_specialisations')
    op.drop_column('lawyer', 'admitted_date_cliex')
    op.drop_column('lawyer', 'called_date_barrister')
    op.drop_column('lawyer', 'admitted_date_solicitor')
    op.drop_column('lawyer', 'bar_number')
    op.drop_column('lawyer', 'sra_number')
    op.drop_column('lawyer', 'county')
    op.drop_column('lawyer', 'address_line_2')
    op.drop_column('lawyer', 'address_line_1')
    
    # Drop join tables
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lawyer_relationship_type') THEN
                IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_lawyer_relationship_type_lawyer_id') THEN
                    DROP INDEX ix_lawyer_relationship_type_lawyer_id;
                END IF;
                DROP TABLE lawyer_relationship_type;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lawyer_matter_type') THEN
                IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_lawyer_matter_type_lawyer_id') THEN
                    DROP INDEX ix_lawyer_matter_type_lawyer_id;
                END IF;
                DROP TABLE lawyer_matter_type;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lawyer_expert_type') THEN
                IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_lawyer_expert_type_lawyer_id') THEN
                    DROP INDEX ix_lawyer_expert_type_lawyer_id;
                END IF;
                DROP TABLE lawyer_expert_type;
            END IF;
        END $$;
    """)
    
    # Drop enums only after all dependent objects are removed
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'matter_type_enum') THEN
                DROP TYPE matter_type_enum;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'relationship_type_enum') THEN
                DROP TYPE relationship_type_enum;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'expert_type_enum') THEN
                DROP TYPE expert_type_enum;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lawyer_conflict_level') THEN
                DROP TYPE lawyer_conflict_level;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lawyer_regulator') THEN
                DROP TYPE lawyer_regulator;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lawyer_status') THEN
                DROP TYPE lawyer_status;
            END IF;
        END $$;
    """)
    
    # ### end Alembic commands ### 
