from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "requests",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("source_hash", sa.String(length=128), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("authority", sa.String(length=64), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("classification", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_requests_source_hash", "requests", ["source_hash"])
    op.create_index("ix_requests_authority", "requests", ["authority"])
    op.create_index("ix_requests_risk_score", "requests", ["risk_score"])
    op.create_index("ix_requests_status", "requests", ["status"])
    op.create_index("ix_requests_created_by", "requests", ["created_by"])

    op.create_table(
        "responses",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("request_id", sa.String(length=36), sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("final_text", sa.Text(), nullable=True),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("compliance_result", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("approved_by", sa.String(length=36), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_responses_request_id", "responses", ["request_id"])
    op.create_index("ix_responses_status", "responses", ["status"])
    op.create_index("ix_responses_created_by", "responses", ["created_by"])
    op.create_index("ix_responses_approved_by", "responses", ["approved_by"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=True),
        sa.Column("response_id", sa.String(length=36), nullable=True),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=False),
        sa.Column("after_state", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("ix_audit_logs_response_id", "audit_logs", ["response_id"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=True),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_document_chunks_request_id", "document_chunks", ["request_id"])
    op.create_index("ix_document_chunks_source_name", "document_chunks", ["source_name"])
    op.create_index("ix_document_chunks_content_hash", "document_chunks", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_document_chunks_content_hash", table_name="document_chunks")
    op.drop_index("ix_document_chunks_source_name", table_name="document_chunks")
    op.drop_index("ix_document_chunks_request_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_response_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_responses_approved_by", table_name="responses")
    op.drop_index("ix_responses_created_by", table_name="responses")
    op.drop_index("ix_responses_status", table_name="responses")
    op.drop_index("ix_responses_request_id", table_name="responses")
    op.drop_table("responses")

    op.drop_index("ix_requests_created_by", table_name="requests")
    op.drop_index("ix_requests_status", table_name="requests")
    op.drop_index("ix_requests_risk_score", table_name="requests")
    op.drop_index("ix_requests_authority", table_name="requests")
    op.drop_index("ix_requests_source_hash", table_name="requests")
    op.drop_table("requests")

    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

