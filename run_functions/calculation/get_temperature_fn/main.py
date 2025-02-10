import functions_framework
from shared.calculation.calculator import Calculator


@functions_framework.http
def main(request):
    data = request.get_json(silent=True)
    calculator = Calculator()
    calculator.multiply(data["x"], data["y"])
    return str(calculator.result)