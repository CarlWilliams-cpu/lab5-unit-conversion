import grpc
import conversion_pb2
import conversion_pb2_grpc
from concurrent import futures
import os
 
# Conversion factors to a common base unit per category.
# Length base: meters | Weight base: kilograms
# Temperature: handled separately (non-linear)
# Speed base: meters per second | Volume base: liters
 
CONVERSIONS = {
    # Length (base: meters)
    "meters":     ("length", 1.0),
    "km":         ("length", 1000.0),
    "cm":         ("length", 0.01),
    "mm":         ("length", 0.001),
    "miles":      ("length", 1609.344),
    "yards":      ("length", 0.9144),
    "feet":       ("length", 0.3048),
    "inches":     ("length", 0.0254),
    # Weight (base: kilograms)
    "kg":         ("weight", 1.0),
    "grams":      ("weight", 0.001),
    "mg":         ("weight", 0.000001),
    "lbs":        ("weight", 0.453592),
    "ounces":     ("weight", 0.0283495),
    "tons":       ("weight", 907.185),
    # Speed (base: meters per second)
    "mps":        ("speed", 1.0),
    "kph":        ("speed", 0.277778),
    "mph":        ("speed", 0.44704),
    "knots":      ("speed", 0.514444),
    # Volume (base: liters)
    "liters":     ("volume", 1.0),
    "ml":         ("volume", 0.001),
    "gallons":    ("volume", 3.78541),
    "quarts":     ("volume", 0.946353),
    "cups":       ("volume", 0.236588),
    "fl_oz":      ("volume", 0.0295735),
}
 
TEMPERATURE_UNITS = {"celsius", "fahrenheit", "kelvin"}
 
def to_celsius(value, unit):
    if unit == "celsius":    return value
    if unit == "fahrenheit": return (value - 32) * 5 / 9
    if unit == "kelvin":     return value - 273.15
 
def from_celsius(value, unit):
    if unit == "celsius":    return value
    if unit == "fahrenheit": return value * 9 / 5 + 32
    if unit == "kelvin":     return value + 273.15
 
def convert_temperature(value, from_unit, to_unit):
    celsius = to_celsius(value, from_unit)
    result  = from_celsius(celsius, to_unit)
    return round(result, 6), "temperature", f"convert via Celsius"
 
def convert_linear(value, from_unit, to_unit):
    from_cat, from_factor = CONVERSIONS[from_unit]
    to_cat,   to_factor   = CONVERSIONS[to_unit]
    base   = value * from_factor
    result = base / to_factor
    formula = f"multiply by {from_factor / to_factor:.6g}"
    return round(result, 6), from_cat, formula
 
class ConversionEngineServicer(conversion_pb2_grpc.ConversionEngineServicer):
 
    def Convert(self, request, context):
        v, f, t = request.value, request.from_unit.lower(), request.to_unit.lower()
        print(f"Convert: {v} {f} -> {t}")
 
        is_temp_from = f in TEMPERATURE_UNITS
        is_temp_to   = t in TEMPERATURE_UNITS
 
        if is_temp_from != is_temp_to:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Cannot mix temperature and non-temperature units")
            return conversion_pb2.ConversionResult()
 
        if is_temp_from:
            result, category, formula = convert_temperature(v, f, t)
        elif f in CONVERSIONS and t in CONVERSIONS:
            from_cat = CONVERSIONS[f][0]
            to_cat   = CONVERSIONS[t][0]
            if from_cat != to_cat:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(f"Cannot convert {f} ({from_cat}) to {t} ({to_cat})")
                return conversion_pb2.ConversionResult()
            result, category, formula = convert_linear(v, f, t)
        else:
            unknown = f if f not in CONVERSIONS and f not in TEMPERATURE_UNITS else t
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Unknown unit: {unknown}")
            return conversion_pb2.ConversionResult()
 
        print(f"  Result: {result} {t}  ({formula})")
        return conversion_pb2.ConversionResult(
            result=result,
            original_value=v,
            from_unit=f,
            to_unit=t,
            category=category,
            formula=formula
        )
 
def serve():
    port = os.environ.get("PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    conversion_pb2_grpc.add_ConversionEngineServicer_to_server(
        ConversionEngineServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Conversion Engine listening on port {port}")
    server.wait_for_termination()
 
if __name__ == "__main__":
    serve()
