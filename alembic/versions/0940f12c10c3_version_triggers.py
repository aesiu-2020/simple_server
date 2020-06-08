"""version triggers

Revision ID: 0940f12c10c3
Revises: 1040bb9df6cb
Create Date: 2020-06-07 18:37:47.006355

"""
from alembic import op

from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0940f12c10c3'
down_revision = '1040bb9df6cb'
branch_labels = None
depends_on = None

Session = sessionmaker()

def upgrade():
	bind = op.get_bind()
	session = Session(bind=bind)
	# sets up sql triggers to handle versioning,
	# this comes with some up sides like ensuring that history is always tracked even through manual sql
	# although does create some difficulties when altering the schemas and has no innate linkings into orm
	# There should be some additional versioning orm plugins that would prove more scalable in the long term
	session.execute("""
CREATE OR REPLACE FUNCTION update_history() RETURNS trigger AS
$$
  BEGIN
  	IF(TG_OP = 'DELETE') THEN
  	    INSERT INTO person_history (id, version, update_timestamp) VALUES (OLD.id, OLD.version+1, now());
  	ELSEIF (NEW.* IS DISTINCT FROM OLD.*) THEN
  		INSERT INTO person_history VALUES (NEW.*);
    END IF;
    RETURN NEW;
  END;
$$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION track_version() RETURNS trigger AS
$$
  BEGIN
    NEW.update_timestamp = now();
    NEW.version = OLD.version+1;
    RETURN NEW;

  END;
$$
LANGUAGE plpgsql;


create trigger update_person_history after insert or update or delete  on person
for each row
execute procedure update_history();
create trigger update_person_version before update on person
for each row
execute procedure track_version();""")


def downgrade():
	bind = op.get_bind()
	session = Session(bind=bind)
	session.execute("""
drop trigger update_person_history on person;
drop trigger update_person_version on person;""")
