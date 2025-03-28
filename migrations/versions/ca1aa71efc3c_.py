"""empty message

Revision ID: ca1aa71efc3c
Revises: 70d5cf6e2cff
Create Date: 2025-02-26 19:14:56.213240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca1aa71efc3c'
down_revision = '70d5cf6e2cff'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('setting_roles',
    sa.Column('setting_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.ForeignKeyConstraint(['setting_id'], ['setting.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('setting_roles')
    # ### end Alembic commands ###
