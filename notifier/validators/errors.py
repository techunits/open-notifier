from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response


def make_error_response_dict(ref, message):
    return {"error": {"ref": ref, "message": message}}


def send_error_response(ref, message, status=status.HTTP_400_BAD_REQUEST):
    return Response(make_error_response_dict(ref, message), status=status)


class ErrorResponseException(APIException):
    '''
    return http response in the format {"error": {
        "ref":"SOME_REFERENCE", "message": "some message"}}
    '''
    def __init__(self, ref, message, status_code=status.HTTP_400_BAD_REQUEST):
        self.detail = make_error_response_dict(ref, message)
        self.status_code = status_code
