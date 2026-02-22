#!/bin/bash
# setup.sh -- run once after git clone
# Generates gRPC Python stubs from proto/conversion.proto
# and copies them into both service directories.
 
set -e
cd "$(dirname "$0")"
 
echo "Generating gRPC stubs from proto/conversion.proto..."
python3 -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=conversion-engine \
    --grpc_python_out=conversion-engine \
    proto/conversion.proto
 
echo "Copying stubs to converter-api..."
cp conversion-engine/conversion_pb2.py      converter-api/
cp conversion-engine/conversion_pb2_grpc.py converter-api/
 
echo ""
echo "Done. Both services are ready:"
ls conversion-engine/conversion_pb2*.py
ls converter-api/conversion_pb2*.py
