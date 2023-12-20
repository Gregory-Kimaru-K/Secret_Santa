"""Initial migration

Revision ID: f47e894007b6
Revises: 
Create Date: 2023-12-20 13:29:23.140641

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f47e894007b6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pairing', schema=None) as batch_op:
        batch_op.alter_column('chosen_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.create_unique_constraint('uq_chosen_id', ['chosen_id'])
        batch_op.drop_constraint('fk_chosen_id_user', type_='foreignkey')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('chosen_by_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_chosen_by_id_user', 'user', ['chosen_by_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('fk_chosen_by_id_user', type_='foreignkey')
        batch_op.drop_column('chosen_by_id')

    with op.batch_alter_table('pairing', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_chosen_id_user', 'user', ['chosen_id'], ['id'])
        batch_op.drop_constraint('uq_chosen_id', type_='unique')
        batch_op.alter_column('chosen_id', existing_type=sa.INTEGER(), nullable=True)
    # ### end Alembic commands ###
