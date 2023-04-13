import uuid
import logging
import json
import time

class TracerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        trace_id = request.headers.get('X-Trace-Id', None)
        request.trace_id = trace_id if trace_id is not None else f'{str(uuid.uuid4())}-{int(time.time())}'  

        response = self.get_response(request)

        # add trace_id to response
        try:
            body = json.loads(response.content)
            body['trace_id'] = request.trace_id
            response.content = bytes(json.dumps(body), encoding='utf-8')
        except Exception:
            pass
        
        return response


class TraceIdFilter(logging.Filter):
    def filter(self, record):
        # print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        # print(hasattr(record, 'request'))
        # print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        if hasattr(record, 'request') is not False:
            trace_id = record.request.trace_id
        else:
            trace_id = 'GLOBAL'
        record.trace_id = trace_id
        return True