"""Store a scoped ODK pilot polling configuration."""
from alembic import op
import sqlalchemy as sa

revision = "0002_odk_sync_configs"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("odk_sync_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("form_id", sa.String(200), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id"))
    op.create_index("ix_odk_sync_configs_organization_id", "odk_sync_configs", ["organization_id"])


def downgrade():
    op.drop_index("ix_odk_sync_configs_organization_id", table_name="odk_sync_configs")
    op.drop_table("odk_sync_configs")
