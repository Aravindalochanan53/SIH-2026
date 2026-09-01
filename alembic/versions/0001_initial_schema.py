"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-30 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Unicode(length=150), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='teacher'),
        sa.Column('preferred_source_lang', sa.String(length=10), server_default='ta'),
        sa.Column('preferred_target_lang', sa.String(length=10), server_default='ml'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. languages
    op.create_table(
        'languages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.Unicode(length=100), nullable=False),
        sa.Column('native_name', sa.Unicode(length=100), nullable=False),
        sa.Column('script', sa.Unicode(length=50), nullable=False),
        sa.Column('region', sa.Unicode(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_languages_code'), 'languages', ['code'], unique=True)

    # 3. translations
    op.create_table(
        'translations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('source_text', sa.UnicodeText(), nullable=False),
        sa.Column('target_text', sa.UnicodeText(), nullable=False),
        sa.Column('engine', sa.String(length=50), server_default='indictrans2'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('category', sa.String(length=50), server_default='general'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_translations_source_language'), 'translations', ['source_language'], unique=False)
    op.create_index(op.f('ix_translations_target_language'), 'translations', ['target_language'], unique=False)

    # 4. translation_history
    op.create_table(
        'translation_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('source_language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('source_text', sa.UnicodeText(), nullable=False),
        sa.Column('translated_text', sa.UnicodeText(), nullable=False),
        sa.Column('input_type', sa.String(length=20), nullable=False, server_default='text'),
        sa.Column('model_used', sa.String(length=100), server_default='TRANSLARA-NMT-v1'),
        sa.Column('model_version', sa.String(length=50), server_default='1.0'),
        sa.Column('latency_ms', sa.Float(), server_default='0.0'),
        sa.Column('offline_used', sa.Boolean(), server_default='0'),
        sa.Column('validation_passed', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_translation_history_user_id'), 'translation_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_translation_history_session_id'), 'translation_history', ['session_id'], unique=False)

    # 5. chat_sessions
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.Unicode(length=255), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='ta'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_id'), 'chat_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)

    # 6. chat_messages
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('message', sa.UnicodeText(), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='ta'),
        sa.Column('model_used', sa.String(length=100), server_default='TRANSLARA-Edu'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)

    # 7. video_jobs
    op.create_table(
        'video_jobs',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('original_filename', sa.Unicode(length=255), nullable=False),
        sa.Column('source_language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Float(), server_default='0.0'),
        sa.Column('input_path', sa.String(length=500), nullable=True),
        sa.Column('output_path', sa.String(length=500), nullable=True),
        sa.Column('transcript_path', sa.String(length=500), nullable=True),
        sa.Column('subtitle_path', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.UnicodeText(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_jobs_id'), 'video_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_video_jobs_user_id'), 'video_jobs', ['user_id'], unique=False)

    # 8. worksheets
    op.create_table(
        'worksheets',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.Unicode(length=255), nullable=False),
        sa.Column('grade', sa.String(length=20), nullable=False, server_default='1'),
        sa.Column('subject', sa.Unicode(length=50), nullable=False, server_default='FLN'),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_worksheets_id'), 'worksheets', ['id'], unique=False)

    # 9. flashcards
    op.create_table(
        'flashcards',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('deck_name', sa.Unicode(length=100), nullable=False, server_default='FLN Classroom Deck'),
        sa.Column('word', sa.Unicode(length=255), nullable=False),
        sa.Column('translation', sa.Unicode(length=255), nullable=False),
        sa.Column('source_language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('category', sa.Unicode(length=50), nullable=False, server_default='General'),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flashcards_id'), 'flashcards', ['id'], unique=False)

    # 10. classroom_phrases
    op.create_table(
        'classroom_phrases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('source_language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('source_text', sa.UnicodeText(), nullable=False),
        sa.Column('target_text', sa.UnicodeText(), nullable=False),
        sa.Column('audio_path', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_classroom_phrases_category'), 'classroom_phrases', ['category'], unique=False)
    op.create_index(op.f('ix_classroom_phrases_source_language'), 'classroom_phrases', ['source_language'], unique=False)
    op.create_index(op.f('ix_classroom_phrases_target_language'), 'classroom_phrases', ['target_language'], unique=False)

    # 11. entities
    op.create_table(
        'entities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Unicode(length=255), nullable=False),
        sa.Column('kind', sa.String(length=50), nullable=False, server_default='PERSON'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='all'),
        sa.Column('phonetic_hint', sa.Unicode(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entities_name'), 'entities', ['name'], unique=False)

    # 12. model_usage
    op.create_table(
        'model_usage',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('service_name', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('character_or_token_count', sa.Integer(), server_default='0'),
        sa.Column('latency_ms', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('model_usage')
    op.drop_table('entities')
    op.drop_table('classroom_phrases')
    op.drop_table('flashcards')
    op.drop_table('worksheets')
    op.drop_table('video_jobs')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('translation_history')
    op.drop_table('translations')
    op.drop_table('languages')
    op.drop_table('users')
