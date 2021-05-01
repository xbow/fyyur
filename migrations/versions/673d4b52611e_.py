"""empty message

Revision ID: 673d4b52611e
Revises: 4a10b1149ed1
Create Date: 2021-05-01 14:27:54.436750

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '673d4b52611e'
down_revision = '4a10b1149ed1'
branch_labels = None
depends_on = None


def upgrade():
  op.execute('ALTER TABLE "artist" ALTER COLUMN genres TYPE varchar[] USING genres::character varying[]')
  op.execute('ALTER TABLE "venue" ALTER COLUMN genres TYPE varchar[] USING genres::character varying[]')

def downgrade():
  op.alter_column('artist', 'genres', existing_type=sa.ARRAY(sa.String()), type_=sa.String(length=120))
  op.alter_column('venue', 'genres', existing_type=sa.ARRAY(sa.String()), type_=sa.String(length=120))
