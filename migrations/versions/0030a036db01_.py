"""empty message

Revision ID: 0030a036db01
Revises: d7667412ebe7
Create Date: 2024-09-18 21:36:07.771470

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0030a036db01'
down_revision = 'd7667412ebe7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('start', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('end', sa.Integer(), nullable=True))
        batch_op.drop_column('eventName')
        batch_op.drop_column('eventEndDate')
        batch_op.drop_column('eventStartDate')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('eventStartDate', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('eventEndDate', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('eventName', sa.VARCHAR(length=100), nullable=True))
        batch_op.drop_column('end')
        batch_op.drop_column('start')
        batch_op.drop_column('title')

    # ### end Alembic commands ###
