from flask import Flask, g, Blueprint, abort, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import IntegrityError, DataError
from models.person_entity import Person
from psycopg2.errors import UniqueViolation
from uuid import UUID, uuid4

import os

person_blueprint = Blueprint('person_blueprint', __name__, url_prefix='/rest/person')
engine = create_engine(os.getenv('DB_CONNECTION'))
Session = scoped_session(sessionmaker(bind=engine))

app = Flask(__name__)

# BASIC CRUD APIs: just a get, post, put and delete
@person_blueprint.route("/<uuid>", methods=['GET'])
def get_by_uuid(uuid):
	return fetch_person_by_uuid(uuid).toResp()

@person_blueprint.route("", methods=['POST'])
def create_person():
	person_entity = Person(id = uuid4())
	person_entity = populate_person(person_entity, request.get_json())
	get_db().add(person_entity)
	commit()
	return person_entity.toResp()

@person_blueprint.route("/<uuid>", methods=['PUT'])
def update_person(uuid):
	person_entity = fetch_person_by_uuid(uuid)
	populate_person(person_entity, request.get_json())
	commit()
	return person_entity.toResp()

@person_blueprint.route("/<uuid>", methods=['DELETE'])
def delete_person(uuid):
	get_db().delete(fetch_person_by_uuid(uuid))
	commit()
	return {"deletion": "ok"}

# get by version api
@person_blueprint.route("/<uuid>/version/<version>", methods=['GET'])
def get_historic_by_uuid(uuid, version):
	'''
	This implementation access history via raw sql returns it to the user
	The reason for this is that I'd prefer to not tie a class to the history 
	object itself with the understanding that the pervious versions of this table may have
	carried ideas and schemas that are no longer properly represented and keeping track
	of all possible historical scenerios within a class could prove dangerous,
	so splitting them off here acts to reduce complexity by not having this seep into the entity layer
	'''
	validate_uuid(uuid)
	if (not version.isdigit()):
		abort(400, "version must be numeric")
	results = get_db().execute(
		'select * from person_history where id = \'{uuid}\' and version = {version}'
		.format(uuid = uuid, version = version))
	count = results.rowcount;
	if (count == 0):
		abort(404, "Could not find person {uuid} at version {version}"
			.format(uuid = uuid, version = version))
	elif(count > 1):
		abort(500, "Found multiple person {uuid} at version {version} entries, THIS SHOULD NOT HAPPPEN"
			.format(uuid = uuid, version = version))
	return dict(results.first())


# some orchestration logic TODO, consider service layer if it gets complex
def populate_person(person_entity, req_json):
	try:
		person_entity.first_name = req_json.get('firstName'),
		person_entity.middle_name = req_json.get('middleName'),
		person_entity.last_name = req_json.get('lastName'),
		person_entity.date_of_birth = req_json.get('dateOfBirth'),
		person_entity.email = req_json.get('email')
	except ValueError as e:
		app.logger.warn('%s ValueError, could not create person', e)
		abort(400, "Data Error, could not create person")
	return person_entity

def validate_uuid(val):
	try:
		return UUID(str(val))
	except ValueError:
		abort(400, description="invalid uuid {}".format(val))

def fetch_person_by_uuid(uuid):
	app.logger.info('%s fetching person', uuid)
	validate_uuid(uuid)
	try:
		return get_db().query(Person).filter(Person.id == uuid).one()
	except MultipleResultsFound:
		abort(500, description = "Multiple person {} records found, SHOULD NOT BE POSSIBLE".format(uuid))
	except NoResultFound:
		abort(404, description = "Person {} not found".format(uuid))


## Session stuff
def commit():
	try: 
		get_db().commit()
	except IntegrityError as e:
		app.logger.warn('%s not committing data', e)
		if isinstance(e.orig, UniqueViolation):
			abort(409, "Uniqueness violation detected")
		# consider pulling more out of e for a better message
		abort(400, "Integrity Error, have you provided all fields?")
	except DataError as e:
		app.logger.warn('%s DataError, not committing data', e)
		abort(400, "Data Error, could not save data given")

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db_session'):
    	g.db_session = Session # save session in the request context
    return g.db_session

@app.teardown_appcontext
def shutdown_session(exception=None):
	''' Enable Flask to automatically remove database sessions at the
	end of the request or when the application shuts down.
	Ref: http://flask.pocoo.org/docs/patterns/sqlalchemy/
	'''
	if hasattr(g, 'db_session'):
		g.db_session.remove()


