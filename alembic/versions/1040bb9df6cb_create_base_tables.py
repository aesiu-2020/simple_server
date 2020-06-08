"""create vase tables

Revision ID: 1040bb9df6cb
Revises: 
Create Date: 2020-06-07 18:35:09.441264

"""
from alembic import op

from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '1040bb9df6cb'
down_revision = None
branch_labels = None
depends_on = None

Session = sessionmaker()

def upgrade():
	# basic table creation
	bind = op.get_bind()
	session = Session(bind=bind)
	session.execute("""
create table person (
	id UUID not null primary key,
	first_name varchar not null,
	middle_name varchar,
	last_name varchar not null,
	email varchar not null,
	date_of_birth date not null,
	version int not null default 0,
	create_timestamp timestamp not null default now(),
	update_timestamp timestamp not null default now()
);

create table person_history (
	id UUID,
	first_name varchar,
	middle_name varchar,
	last_name varchar,
	email varchar,
	date_of_birth date,
	version int,
	create_timestamp timestamp,
	update_timestamp timestamp,
	unique(id, version)
);
create unique index on person ((lower(email)));""")


def downgrade():
	bind = op.get_bind()
	session = Session(bind=bind)
	session.execute("""
drop table person;
drop table person_history;""")
