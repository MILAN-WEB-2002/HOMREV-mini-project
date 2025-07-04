"""Create ChatRoom and Message models

Revision ID: 89d69c8ce558
Revises: 
Create Date: 2024-11-10 22:05:38.499537

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89d69c8ce558'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('chat_message')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat_message',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('sender_id', sa.INTEGER(), nullable=False),
    sa.Column('receiver_id', sa.INTEGER(), nullable=False),
    sa.Column('project_id', sa.INTEGER(), nullable=False),
    sa.Column('message', sa.TEXT(), nullable=False),
    sa.Column('timestamp', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['receiver_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
