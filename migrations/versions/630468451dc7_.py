"""empty message

Revision ID: 630468451dc7
Revises: e38202f7f34c
Create Date: 2024-10-01 16:26:52.567634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '630468451dc7'
down_revision = 'e38202f7f34c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('addon',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=True),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('cost', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('guest_addons',
    sa.Column('guest_id', sa.Integer(), nullable=True),
    sa.Column('addon_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['addon_id'], ['addon.id'], ),
    sa.ForeignKeyConstraint(['guest_id'], ['guest.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('guest_addons')
    op.drop_table('addon')
    # ### end Alembic commands ###
