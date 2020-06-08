from flask import Flask, g, Blueprint, abort, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from models.person_entity import Person
from uuid import UUID, uuid4
from app.person_routes import person_blueprint

import os

app = Flask(__name__)

app.register_blueprint(person_blueprint)

if __name__ == "__main__":
    app.run()
