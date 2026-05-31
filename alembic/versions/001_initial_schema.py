"""
Initial migration: Create all database tables

Revision ID: 001_initial_schema
Creates: conversation_sessions, conversation_messages, clinical_data, audit_logs
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply initial schema"""
    
    # Create conversation_sessions table
    op.create_table(
        'conversation_sessions',
        sa.Column('session_id', sa.String(50), primary_key=True),
        sa.Column('conversation_id', sa.String(100), unique=True, nullable=False),
        sa.Column('patient_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, default=datetime.now, nullable=False),
        sa.Column('updated_at', sa.DateTime, default=datetime.now, nullable=False),
        sa.Column('ended_at', sa.DateTime, nullable=True),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('turn_count', sa.Integer, default=0),
    )
    
    # Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('message_id', sa.String(50), primary_key=True),
        sa.Column('session_id', sa.String(50), sa.ForeignKey('conversation_sessions.session_id'), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('timestamp', sa.DateTime, default=datetime.now, nullable=False),
        sa.Column('turn_number', sa.Integer, nullable=False),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('is_interrupted', sa.Boolean, default=False),
    )
    
    # Create clinical_data table
    op.create_table(
        'clinical_data',
        sa.Column('clinical_data_id', sa.String(50), primary_key=True),
        sa.Column('session_id', sa.String(50), sa.ForeignKey('conversation_sessions.session_id'), unique=True, nullable=False),
        sa.Column('chief_complaint', sa.Text, nullable=True),
        sa.Column('duration', sa.String(100), nullable=True),
        sa.Column('pain_severity', sa.Integer, nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('triggers', sa.JSON, nullable=True),
        sa.Column('current_medications', sa.JSON, nullable=True),
        sa.Column('allergies', sa.JSON, nullable=True),
        sa.Column('medical_conditions', sa.JSON, nullable=True),
        sa.Column('clinical_summary', sa.Text, nullable=True),
        sa.Column('red_flags', sa.JSON, nullable=True),
        sa.Column('urgency_level', sa.String(20), default='MEDIUM'),
        sa.Column('recommended_specialist', sa.String(100), nullable=True),
        sa.Column('confidence_scores', sa.JSON, nullable=True),
        sa.Column('needs_triage', sa.Boolean, default=False),
        sa.Column('pre_scheduled', sa.Boolean, default=True),
        sa.Column('appointment_confirmed', sa.Boolean, default=False),
        sa.Column('doctor_assigned', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.now, nullable=False),
        sa.Column('updated_at', sa.DateTime, default=datetime.now, nullable=False),
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.String(50), primary_key=True),
        sa.Column('timestamp', sa.DateTime, default=datetime.now, nullable=False, index=True),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('session_id', sa.String(50), nullable=True, index=True),
        sa.Column('patient_id', sa.String(50), nullable=True, index=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('status_code', sa.Integer, nullable=False),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
    )
    
    print("✓ Created all tables successfully")


def downgrade() -> None:
    """Revert initial schema"""
    
    # Drop tables in reverse order (due to foreign keys)
    op.drop_table('audit_logs')
    op.drop_table('clinical_data')
    op.drop_table('conversation_messages')
    op.drop_table('conversation_sessions')
    
    print("✓ Dropped all tables successfully")
