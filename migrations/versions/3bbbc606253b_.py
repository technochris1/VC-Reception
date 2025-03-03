"""empty message

Revision ID: 3bbbc606253b
Revises: d09e9aab1b86
Create Date: 2025-02-25 23:41:48.393733

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3bbbc606253b'
down_revision = 'd09e9aab1b86'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('triggered_email_event', schema=None) as batch_op:
        batch_op.drop_column('role')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('triggered_email_event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.INTEGER(), nullable=True))

    # ### end Alembic commands ###
