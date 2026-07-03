# build protoc: connector
python -m grpc_tools.protoc -I./protobuffs --python_out=./protoc/ --grpc_python_out=./protoc/ ./protobuffs/connector.proto