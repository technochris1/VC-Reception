"""empty message

Revision ID: 500357835a47
Revises: 1c69d19813a0
Create Date: 2024-09-16 16:18:51.424749

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '500357835a47'
down_revision = '1c69d19813a0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('guest', schema=None) as batch_op:
        batch_op.add_column(sa.Column('allow_qrcode_refresh', sa.Boolean(), nullable=True))

    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.drop_column('allow_qrcode_refresh')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.add_column(sa.Column('allow_qrcode_refresh', sa.BOOLEAN(), nullable=True))

    with op.batch_alter_table('guest', schema=None) as batch_op:
        batch_op.drop_column('allow_qrcode_refresh')

    # ### end Alembic commands ###
