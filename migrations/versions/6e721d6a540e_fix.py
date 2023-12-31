"""Fix

Revision ID: 6e721d6a540e
Revises: b9940d7b1091
Create Date: 2023-11-20 14:25:50.228934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e721d6a540e'
down_revision: Union[str, None] = 'b9940d7b1091'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('comments_image_id_fkey', 'comments', type_='foreignkey')
    op.create_foreign_key(None, 'comments', 'images', ['image_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('image_tags_image_id_fkey', 'image_tags', type_='foreignkey')
    op.create_foreign_key(None, 'image_tags', 'images', ['image_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('likes_image_id_fkey', 'likes', type_='foreignkey')
    op.create_foreign_key(None, 'likes', 'images', ['image_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'likes', type_='foreignkey')
    op.create_foreign_key('likes_image_id_fkey', 'likes', 'images', ['image_id'], ['id'])
    op.drop_constraint(None, 'image_tags', type_='foreignkey')
    op.create_foreign_key('image_tags_image_id_fkey', 'image_tags', 'images', ['image_id'], ['id'])
    op.drop_constraint(None, 'comments', type_='foreignkey')
    op.create_foreign_key('comments_image_id_fkey', 'comments', 'images', ['image_id'], ['id'])
    # ### end Alembic commands ###
