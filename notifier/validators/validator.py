import uuid
import re
import json
from django.core.validators import validate_email, URLValidator
from django.core.exceptions import ValidationError


class ValidateHandler:
	@staticmethod
	def is_valid_uuid(val):
		try:
			return uuid.UUID(str(val))
		except ValueError:
			return None

	@staticmethod
	def is_valid_email(email):
		try:
			validate_email(email)
			return True
		except ValidationError:
			return False

	@staticmethod
	def is_valid_phone(phno):
		phno_check = re.compile(r"^(\+\d{1,3}[- ]?)?\d{10}$")
		if phno_check.search(phno) is None:
			return False
		else:
			return True

	@staticmethod
	def is_valid_url(url):
		msg = "Cannot validate this website: %s" % url
		validate = URLValidator(message=msg)
		try:
			validate(url)
			return True
		except ValidationError:
			return False

	@staticmethod
	def is_number(value):
		try:
			int(value)
			return True
		except:
			return False

	@staticmethod
	def is_special_character(value):
		string_check = re.compile("[@_!#$%^&*()<>?/\|}{~:]")

		if string_check.search(value) is None:
			return False
		else:
			return True

	@staticmethod
	def is_valid_json(json_obj):
		try:
			json_obj = json.loads(str(json_obj))
			return json_obj
		except ValueError as e:
			return None
		

