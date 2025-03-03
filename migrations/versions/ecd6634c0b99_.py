"""empty message

Revision ID: ecd6634c0b99
Revises: ca1aa71efc3c
Create Date: 2025-02-27 17:31:38.324607

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ecd6634c0b99'
down_revision = 'ca1aa71efc3c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('setting_roles')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('setting_roles',
    sa.Column('setting_id', sa.INTEGER(), nullable=True),
    sa.Column('role_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.ForeignKeyConstraint(['setting_id'], ['setting.id'], )
    )
    # ### end Alembic commands ###
