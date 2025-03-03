"""empty message

Revision ID: d05fb521fd14
Revises: a5e2e90670ae
Create Date: 2025-02-25 23:25:50.928530

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd05fb521fd14'
down_revision = 'a5e2e90670ae'
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
