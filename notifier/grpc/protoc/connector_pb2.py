# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: connector.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x0f\x63onnector.proto\x12\x10GenericConnector"\\\n\x0eGenericRequest\x12\x16\n\x0erequest_method\x18\x01 \x01(\t\x12\x10\n\x08\x65ndpoint\x18\x02 \x01(\t\x12\x0f\n\x07payload\x18\x03 \x01(\t\x12\x0f\n\x07headers\x18\x04 \x01(\t"4\n\x0fGenericResponse\x12\x13\n\x0bstatus_code\x18\x01 \x01(\x05\x12\x0c\n\x04\x64\x61ta\x18\x02 \x01(\t2a\n\tConnector\x12T\n\x0bgetResponse\x12 .GenericConnector.GenericRequest\x1a!.GenericConnector.GenericResponse"\x00\x62\x06proto3'
)

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "connector_pb2", globals())
if _descriptor._USE_C_DESCRIPTORS == False:
    DESCRIPTOR._options = None
    _GENERICREQUEST._serialized_start = 37
    _GENERICREQUEST._serialized_end = 129
    _GENERICRESPONSE._serialized_start = 131
    _GENERICRESPONSE._serialized_end = 183
    _CONNECTOR._serialized_start = 185
    _CONNECTOR._serialized_end = 282
# @@protoc_insertion_point(module_scope)
