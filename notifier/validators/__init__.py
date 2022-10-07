from django.db import transaction
from rest_framework.views import APIView

from notifier.validators.validator import ValidateHandler
from notifier.validators.errors import ErrorResponseException


class URLValidatorView(APIView, ValidateHandler):
    """
    view for running url param & other validations
    validator function example:
        def validate_entity_id(self, kwargs):
            try:
                self.entity = Entity.objects.get(id=kwargs['entity_id'])
            except Exception:
                raise ErrorResponseExceptionn(
                    'INVALID_ENTITY_ID',"Invalid entity id supplied",
                    status.HTTP_404_NOT_FOUND)
    """

    def validate_request_params(self, **kwargs):
        """
        send named paramenters used by validation functions in kwargs
        names in kwargs call the relevant validator fucntion example:
        self.validate_request_params(entity_id=<anything>)
        will call
        self.validate_entity_id(kwargs)

        if validation functions are dependent, pass them in the order of
        execution. example:
        self.validate_request_params(independent_1=<*>, independent_2=None, dependendent_on_independent_1_and_2=<*>)

        """

        if hasattr(self, 'allowed_get_parmas'):
            if not set(self.request.GET.keys()).issubset(
                self.allowed_get_parmas
            ):
                raise ErrorResponseException(
                    'GENERAL_ERROR', 'Invalid get parameter supplied'
                )

        for var_name in kwargs:
            validator_function = getattr(self, "validate_" + var_name)
            validation_response = validator_function(kwargs)
            if validation_response is not None:
                return validation_response


class PayloadValidator(ValidateHandler):
    """
    valdiate payload & save to db
    """

    def __init__(self, instance=None, data=None, context=None):
        self.instance = instance
        self.initial_data = data if data is not None else {}
        self.context = context if context is not None else {}
        self.validated_data = {}

    def validate_dependent_fields(self):
        """
        as the order of fields in payload can have different orders, this
        functionn will be called after all payload fields are independently
        validated.
        use case example: in payload end_date key may be before start_date. So
        it is safer to check if start_date > end_date after both
        validate_start_date & validate_end_date functionns have executed.
        """
        pass

    def validate(self, required_fields=[]):
        """
        if payload contains 'address', function `validate_address` will run
        returns populated `validated_data` for create along with instance,
        for update
        """
        unfiltered_payload = self.initial_data
        if type(unfiltered_payload) is not dict:
            raise ErrorResponseException(
                "INVALID_TYPE", "Payload must be valid json")
        payload = {}
        for field in unfiltered_payload:
            field_value = unfiltered_payload[field]
            """ skipping null value fields """
            if field_value is not None:
                payload[field] = field_value
        if len(payload) < 1:
            raise ErrorResponseException(
                "MISSING_PAYLOAD", "Blank payload supplied")

        no_matching_field_in_payload = True
        for var_name in payload:
            function_name = "validate_" + var_name
            if hasattr(self, function_name):
                no_matching_field_in_payload = False
                validator_function = getattr(self, function_name)
                validation_response = validator_function(payload[var_name])
                if validation_response is not None:
                    return validation_response

        if len(required_fields) > 0:
            for required_field in required_fields:
                if payload.get(required_field, None) is None:
                    err_ref = "MISSING_" + required_field.upper()
                    err_msg = "Missing " + required_field
                    if type(required_fields) is dict:
                        missing_field_dict = required_fields[required_field].\
                            get('missing', None)
                        if missing_field_dict is not None:
                            err_ref = missing_field_dict['ref']
                            err_msg = missing_field_dict['message']
                    raise ErrorResponseException(err_ref, err_msg)

        if not no_matching_field_in_payload:
            self.validate_dependent_fields()

        if no_matching_field_in_payload:
            raise ErrorResponseException(
                "MISSING_PAYLOAD", "Blank payload supplied")

        return (
            (self.instance, self.validated_data)
            if self.instance is not None
            else self.validated_data
        )

    def create(self, validated_data):
        raise NotImplementedError("Write code for create in your own class")

    def update(self, instance, validated_data):
        raise NotImplementedError("Write code for update in your own class")

    def save_actual(self, **kwargs):
        if self.instance is not None:
            self.instance = self.update(self.instance, self.validated_data)
            assert (
                self.instance is not None
            ), "`update()` did not return an object instance."
        else:
            self.instance = self.create(self.validated_data)
            assert (
                self.instance is not None
            ), "`create()` did not return an object instance."
        return self.instance

    def save(self, **kwargs):
        """
        saves `validated_data` to db
        """
        if kwargs.get("use_transaction", False):
            with transaction.atomic():
                # send `fail_gracefully` False for testing
                if kwargs.get("fail_gracefully", True):
                    try:
                        return self.save_actual()
                    except ErrorResponseException as e:
                        raise e
                    except Exception as e:
                        raise ErrorResponseException(
                            "GENERAL_ERROR",
                            "Error while saving to db: " + str(e))
                return self.save_actual()
        else:
            return self.save_actual()
