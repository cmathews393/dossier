"""
Consolidated initial schema for dossier

Revision ID: 20250911_init
Revises: 
Create Date: 2025-09-11 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '20250911_init'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('profile_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('api_key', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_api_key'), 'users', ['api_key'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table('people',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('address', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('socials', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('alternate_phones', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('alternate_emails', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_people_email'), 'people', ['email'], unique=True)
    op.create_index(op.f('ix_people_id'), 'people', ['id'], unique=False)

    op.create_table('sherlock_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('person_id', sa.String(length=36), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('sites', sa.JSON(), nullable=True),
        sa.Column('timeout', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', name='sherlockjobstatus'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('sherlock_jobs')
    op.drop_index(op.f('ix_people_id'), table_name='people')
    op.drop_index(op.f('ix_people_email'), table_name='people')
    op.drop_table('people')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_api_key'), table_name='users')
    op.drop_table('users')
