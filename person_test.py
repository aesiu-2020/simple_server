import requests
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from flask import Flask
from flask_testing import LiveServerTestCase
from app import app
from app.person_routes import person_blueprint
from uuid import UUID, uuid4
from dateutil.relativedelta import relativedelta

# TODO: move this into a test folder, resolve imports


class PersonTest(LiveServerTestCase):

    def create_app(self):
        engine = create_engine(os.getenv('DB_CONNECTION'))
        session = Session(engine)
        # clean state for testing
        session.execute("truncate person_history")
        session.execute("truncate person")
        session.commit()
        session.close()

        app.register_blueprint(person_blueprint)

        return app

    def test_full_CRUD(self):
        # precheck, get the person list size
        response = requests.get(self.get_server_url() + "/rest/person")
        response_body = response.json()
        self.assertEqual(response.status_code, 200)
        person_list_size = len(response_body)

        # start with create
        # TODO: long test, should be broken up
        basic_request = {
            "firstName": "Homer",
            "lastName": "Simpson",
            "dateOfBirth": "1956-05-12",
            "email": "chunkylover53@aol.com"
        }
        response = requests.post(
            self.get_server_url() + "/rest/person", json=basic_request)
        self.assertEqual(response.status_code, 200)
        response_body = response.json()
        self.assertEqual(response_body['firstName'], "Homer")
        self.assertEqual(response_body['lastName'], "Simpson")
        self.assertEqual(response_body['email'], "chunkylover53@aol.com")
        # TODO: mock today, or calculate email relative to today
        self.assertEqual(response_body['age'], 64)
        self.assertEqual(response_body['middleName'], None)

        # now read
        uuid = response_body['id']
        response = requests.get(self.get_server_url() + "/rest/person/" + uuid)
        response_body = response.json()
        self.assertEqual(response.status_code, 200)
        # simple assertion
        self.assertEqual(response_body['firstName'], "Homer")

        # and see the list of people has grown
        response = requests.get(self.get_server_url() + "/rest/person")
        response_body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(person_list_size + 1, len(response_body))

        # then update
        basic_request['middleName'] = 'Jay'
        response = requests.put(
            self.get_server_url() + "/rest/person/" + uuid, json=basic_request)
        response_body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_body['firstName'], "Homer")
        self.assertEqual(response_body['middleName'], "Jay")

        # and delete
        response = requests.delete(
            self.get_server_url() + "/rest/person/" + uuid)

        # fetch fails
        response = requests.get(self.get_server_url() + "/rest/person/" + uuid)
        self.assertEqual(response.status_code, 404)
        # and list is back to original size
        response = requests.get(self.get_server_url() + "/rest/person")
        response_body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(person_list_size, len(response_body))

        # but history remains
        response = requests.get(
            self.get_server_url() + "/rest/person/" + uuid + "/version/0")
        response_body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_body['first_name'], "Homer")
        self.assertEqual(response_body['middle_name'], None)

        response = requests.get(
            self.get_server_url() + "/rest/person/" + uuid + "/version/1")
        response_body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_body['first_name'], "Homer")
        self.assertEqual(response_body['middle_name'], "Jay")

        # last entry exists to say that this person has no data anymore/was
        # deleted
        response = requests.get(
            self.get_server_url() + "/rest/person/" + uuid + "/version/2")
        response_body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_body['first_name'], None)
        self.assertEqual(response_body['middle_name'], None)

    def test_bad_fetches(self):
        response = requests.get(self.get_server_url() + "/rest/person/hello")
        self.assertEqual(response.status_code, 400)
        response = requests.get(
            self.get_server_url() + "/rest/person/" + str(uuid4()))
        self.assertEqual(response.status_code, 404)
        response = requests.delete(
            self.get_server_url() + "/rest/person/" + str(uuid4()))
        self.assertEqual(response.status_code, 404)
        response = requests.put(
            self.get_server_url() + "/rest/person/" + str(uuid4()))
        self.assertEqual(response.status_code, 404)

    def test_failed_writes(self):
        basic_request = {
            "firstName": "Marge",
            "lastName": "Simpson",
            "dateOfBirth": "1956-11-12",
            "email": "otheremail@aol.com"
        }
        response = requests.post(
            self.get_server_url() + "/rest/person", json=basic_request)
        self.assertEqual(response.status_code, 200)

        response = requests.post(
            self.get_server_url() + "/rest/person", json=basic_request)
        # conflict if it's the same values again
        self.assertEqual(response.status_code, 409)

        basic_request['email'] = "wholenewemail@aol.ca"

        request = basic_request.copy()
        request['firstName'] = None
        response = requests.post(
            self.get_server_url() + "/rest/person", json=request)
        # no name, no go
        self.assertEqual(response.status_code, 400)

        request = basic_request.copy()
        request['dateOfBirth'] = "1999-13-01"
        response = requests.post(
            self.get_server_url() + "/rest/person", json=request)
        # bad date, doesn't work
        self.assertEqual(response.status_code, 400)

        request = basic_request.copy()
        request['email'] = "verygoodemail.valid"
        response = requests.post(
            self.get_server_url() + "/rest/person", json=request)
        # bad email, doesn't work
        self.assertEqual(response.status_code, 400)
