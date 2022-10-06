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
	def validateEmail(email):
		try:
			validate_email(email)
			return True
		except ValidationError:
			return False

	@staticmethod
	def validatePhNumber(phno):
		# phno_check = re.compile(r"^(\+\d{1,3}[- ]?)?\d{10}$")
		# if phno_check.search(phno) is None:
		# 	return False
		# else:
		# 	return True
		return True

	@staticmethod
	def validateURL(url):
		msg = "Cannot validate this website: %s" % url
		validate = URLValidator(message=msg)
		try:
			validate(url)
			return True
		except ValidationError:
			return False

	@staticmethod
	def check_number(value):
		try:
			int(value)
			return True
		except:
			return False

	@staticmethod
	def check_splcharacter(value):
		string_check = re.compile("[@_!#$%^&*()<>?/\|}{~:]")

		if string_check.search(value) is None:
			return False
		else:
			return True

	@staticmethod
	def check_macaddr(mac_address):
		string_check = re.compile(r"^(?:[0-9a-fA-F]:?){12}$")
		if string_check.search(mac_address) is None:
			return False
		else:
			return True

	@staticmethod
	def check_addresses(address):
		string_check = re.compile(r"^[\w\-:,.\s]+$")
		if string_check.search(address) is None:
			return False
		else:
			return True


	@staticmethod
	def check_city(city):
		string_check = re.compile(r"^[\w\s]+$")
		if string_check.search(city) is None:
			return False
		else:
			return True

	@staticmethod
	def check_zipcode(zipcode):
		string_check = re.compile(r"^[A-Za-z0-9]*$")
		if string_check.search(zipcode) is None:
			return False
		else:
			return True


	def check_plain_string(string):
		string_check = re.compile(r"^[\w\-.\s]+$")
		if string_check.search(string) is None:
			return False
		else:
			return True
	
	@staticmethod
	def check_json(json_obj):
		try:
			json_object = json.loads(str(json_obj))
		except ValueError as e:
			return None
		return json_obj


	def password_check(passwd):
	    SpecialSym =['$', '@', '#', '%']
	    val = True
	      
	    if len(passwd) < 6 or len(passwd) > 20:
	        val = False
	          
	    if not any(char.isdigit() for char in passwd):
	        val = False
	          
	    if not any(char.isupper() for char in passwd):
	        val = False
	          
	    if not any(char.islower() for char in passwd):
	        val = False
	          
	    if not any(char in SpecialSym for char in passwd):
	        val = False
	    if val:
	        return val

