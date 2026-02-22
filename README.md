# Lab 5: Unit Conversion Microservices on Google Cloud Run
 
Two Python microservices communicating via gRPC, deployed on Google Cloud Run. 

This is just an overall README file but not to be used for your instructions. See Lab 5 instructions and continue to follow them.
 
## Services
 
- **Conversion Engine** -- private gRPC server. Accepts a value, from-unit, and to-unit.
  Returns the converted result with category and formula. Supports length, weight,
  temperature, speed, and volume.
- **Converter API** -- public HTTP server. Validates the request, confirms units are
  compatible, then calls the Conversion Engine via authenticated gRPC.
 
## Architecture
 
```
Client (HTTP) to Converter API (public) (gRPC+auth) to  Conversion Engine (private)
```
 
## Quick Start (Google Cloud Shell)
 
```bash
# 1. Clone the repository
git clone https://github.com/CarlWilliams-cpu/lab5-unit-conversion.git
 
# 2. Activate your Python virtual environment (see lab instructions)
source ~/lab5/venv/bin/activate
 
# 3. Generate gRPC stubs from the proto file
cd lab5-unit-conversion
bash setup.sh
```
 
## Repository Structure
 
```
proto/                    <- gRPC contract (source of truth)
  conversion.proto
conversion-engine/        <- private gRPC server
  server.py
  requirements.txt
  Dockerfile
converter-api/            <- public HTTP + gRPC client
  server.py
  requirements.txt
  Dockerfile
setup.sh                  <- generates pb2 stubs after cloning
```
 
## Supported Units
 
| Category    | Units |
|-------------|-------|
| Length      | meters, km, cm, mm, miles, yards, feet, inches |
| Weight      | kg, grams, mg, lbs, ounces, tons |
| Temperature | celsius, fahrenheit, kelvin |
| Speed       | mps, kph, mph, knots |
| Volume      | liters, ml, gallons, quarts, cups, fl_oz |
 
## Note on Generated Files
 
The `conversion_pb2.py` and `conversion_pb2_grpc.py` files are not stored
in this repository. They are generated from `proto/conversion.proto` by
running `bash setup.sh`. The proto file is the source of truth.
