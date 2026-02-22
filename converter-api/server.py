import os, json, grpc
import conversion_pb2
import conversion_pb2_grpc
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
 
CONVERSION_ENGINE_URL = os.environ.get("CONVERSION_ENGINE_URL", "localhost:50051")
 
UNITS_BY_CATEGORY = {
    "length":  ["meters", "km", "cm", "mm", "miles", "yards", "feet", "inches"],
    "weight":  ["kg", "grams", "mg", "lbs", "ounces", "tons"],
    "temperature": ["celsius", "fahrenheit", "kelvin"],
    "speed":   ["mps", "kph", "mph", "knots"],
    "volume":  ["liters", "ml", "gallons", "quarts", "cups", "fl_oz"],
}
 
# Flat lookup: unit -> category
UNIT_CATEGORY = {u: cat for cat, units in UNITS_BY_CATEGORY.items() for u in units}
 
def get_identity_token(audience):
    url = ("http://metadata.google.internal/computeMetadata/v1/instance"
           f"/service-accounts/default/identity?audience={audience}")
    req = urllib.request.Request(url, headers={"Metadata-Flavor": "Google"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode("utf-8")
 
class GrpcAuthPlugin(grpc.AuthMetadataPlugin):
    def __init__(self, token):
        self._token = token
    def __call__(self, context, callback):
        callback([(b"authorization", f"Bearer {self._token}".encode())], None)
 
def call_engine(value, from_unit, to_unit):
    host = CONVERSION_ENGINE_URL.replace("https://", "").replace("http://", "")
    if ":" not in host:
        host += ":443"
    token      = get_identity_token(CONVERSION_ENGINE_URL)
    ssl_creds  = grpc.ssl_channel_credentials()
    auth_creds = grpc.metadata_call_credentials(GrpcAuthPlugin(token))
    creds      = grpc.composite_channel_credentials(ssl_creds, auth_creds)
    with grpc.secure_channel(host, creds) as channel:
        stub = conversion_pb2_grpc.ConversionEngineStub(channel)
        req  = conversion_pb2.ConversionRequest(
            value=float(value), from_unit=from_unit, to_unit=to_unit)
        return stub.Convert(req, timeout=10)
 
class Handler(BaseHTTPRequestHandler):
 
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
 
        if parsed.path == "/health":
            self._send(200, {"status": "ok"})
 
        elif parsed.path == "/units":
            self._send(200, UNITS_BY_CATEGORY)
 
        elif parsed.path == "/convert":
            value     = params.get("value",    [None])[0]
            from_unit = params.get("from",     [None])[0]
            to_unit   = params.get("to",       [None])[0]
 
            if not all([value, from_unit, to_unit]):
                self._send(400, {"error": "Missing required parameters: value, from, to"})
                return
            try:
                float(value)
            except ValueError:
                self._send(400, {"error": f"Invalid value: {value} -- must be a number"})
                return
 
            from_unit = from_unit.lower()
            to_unit   = to_unit.lower()
            from_cat  = UNIT_CATEGORY.get(from_unit)
            to_cat    = UNIT_CATEGORY.get(to_unit)
 
            if not from_cat:
                self._send(400, {"error": f"Unknown unit: {from_unit}",
                    "hint": "Call /units to see all supported units"})
                return
            if not to_cat:
                self._send(400, {"error": f"Unknown unit: {to_unit}",
                    "hint": "Call /units to see all supported units"})
                return
            if from_cat != to_cat:
                self._send(400, {"error":
                    f"Cannot convert {from_unit} ({from_cat}) to {to_unit} ({to_cat})",
                    "hint": "Units must be in the same category"})
                return
 
            try:
                r = call_engine(value, from_unit, to_unit)
                self._send(200, {
                    "original_value": r.original_value,
                    "from_unit":      r.from_unit,
                    "result":         r.result,
                    "to_unit":        r.to_unit,
                    "category":       r.category,
                    "formula":        r.formula,
                    "engine":         "Conversion Engine (via gRPC)"
                })
            except grpc.RpcError as e:
                self._send(503, {"error": "Conversion engine unavailable",
                                 "detail": str(e)})
        else:
            self._send(404, {"error": f"Unknown endpoint: {parsed.path}",
                "available": ["/convert", "/units", "/health"]})
 
    def _send(self, code, body):
        data = json.dumps(body, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)
 
    def log_message(self, fmt, *args):
        print(f"[HTTP] {fmt % args}")
 
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Converter API on port {port}")
    print(f"CONVERSION_ENGINE_URL = {CONVERSION_ENGINE_URL}")
    HTTPServer(("", port), Handler).serve_forever()
