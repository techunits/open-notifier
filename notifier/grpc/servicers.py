import traceback
from uuid import UUID
from django.test.client import Client

from notifier.grpc.protoc import connector_pb2, connector_pb2_grpc

# override default JSON encoder
import json
from json import JSONEncoder

JSONEncoder_default = JSONEncoder.default


def JSONEncoder_override_default(self, o):
    if isinstance(o, UUID):
        return str(o)
    elif isinstance(o, set):
        return list(o)
    return JSONEncoder_default(self, o)


JSONEncoder.default = JSONEncoder_override_default


class ConnectorServicer(connector_pb2_grpc.Connector):
    @property
    def request_method(self):
        """
        return self.client.post()/get()/delete() etc method
        returned method depends on self.request_method_name
        """
        return getattr(self.client, self.request_method_name)

    def setup_client(self, request):
        self.client = Client(HTTP_HOST="gRPC-local")

    def getResponse(self, request, context):
        self.setup_client(request)
        self.request_method_name = request.request_method.lower()
        payload = json.loads(
            "{}" if len(getattr(request, "payload")) == 0 else request.payload
        )
        incoming_headers = json.loads(
            "{}" if len(getattr(request, "headers")) == 0 else request.headers
        )
        headers = dict()
        for key in incoming_headers:
            val = incoming_headers[key]
            key = f"HTTP_{key.upper()}"
            headers[key] = val

        response = self.request_method(
            request.endpoint,
            payload,
            # content_type="application/json"
            **headers,
        )
        try:
            response_data = json.dumps(response.data)
        except AttributeError:
            response_data = response.content.decode("utf8")
        except:
            traceback.print_exc()

        return connector_pb2.GenericResponse(
            status_code=response.status_code, data=response_data
        )
