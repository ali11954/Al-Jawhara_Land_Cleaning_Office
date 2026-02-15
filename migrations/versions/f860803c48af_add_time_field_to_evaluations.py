"""add time field to evaluations

Revision ID: f860803c48af
Revises:
Create Date: 2024-xx-xx xx:xx:xx.xxxxxx

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f860803c48af'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ✅ البديل: إضافة العمود مع قيمة افتراضية أولاً، ثم تعديله ليكون NOT NULL
    with op.batch_alter_table('cleaning_evaluations', schema=None) as batch_op:
        # 1. إضافة العمود مع قيمة افتراضية وقابل للNULL
        batch_op.add_column(sa.Column('time', sa.Integer(), nullable=True, server_default='3'))

    # 2. تحديث جميع الصفوف الموجودة لتعيين قيمة افتراضية
    op.execute("UPDATE cleaning_evaluations SET time = 3 WHERE time IS NULL")

    # 3. تعديل العمود ليكون NOT NULL
    with op.batch_alter_table('cleaning_evaluations', schema=None) as batch_op:
        batch_op.alter_column('time', existing_type=sa.Integer(), nullable=False)


def downgrade():
    # في حالة التراجع، نحذف العمود
    with op.batch_alter_table('cleaning_evaluations', schema=None) as batch_op:
        batch_op.drop_column('time')