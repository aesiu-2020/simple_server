from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

Base = declarative_base()

class Person(Base):
	__tablename__ = 'person'
	id = Column(UUID(as_uuid = True), primary_key=True)
	first_name = Column(String)
	middle_name = Column(String)
	last_name = Column(String)
	date_of_birth = Column(Date)
	email = Column(String, unique = True)


	@validates('email')
	def validate_email(self, key, value):
		# stolen email regex
		# https://stackoverflow.com/questions/8022530/how-to-check-for-valid-email-address
		if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
			raise(ValueError("Invalid email format"))
		return value

	def toResp(self):
		# basic serializer
		return {
			"id": self.id,
			"firstName": self.first_name,
			"middleName": self.middle_name,
			"lastName": self.last_name,
			"age": relativedelta(datetime.now(), self.date_of_birth).years,
			"email": self.email
		}
	


	def __str__(self):
		return "Person(id:'%s', name'%s %s', dob:'%s')>" % (
			self.id, self.first_name, self.last_name, self.date_of_birth)
