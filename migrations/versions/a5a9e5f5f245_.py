"""empty message

Revision ID: a5a9e5f5f245
Revises: 49f653195037
Create Date: 2024-10-04 15:17:02.370438

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5a9e5f5f245'
down_revision = '49f653195037'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('guestlog', schema=None) as batch_op:
        #batch_op.add_column(sa.Column('eventID', sa.Integer(), nullable=True))
        #batch_op.create_foreign_key(None, 'event', ['eventID'], ['id'])
        pass

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('guestlog', schema=None) as batch_op:
        #batch_op.drop_constraint(None, type_='foreignkey')
        #batch_op.drop_column('eventID')
        pass

    # ### end Alembic commands ###
