import functions_framework
from shared.common import Greeter
from greeting_specified import Random

def random():
    random = Random()
    return random.random_number

def greeting():
    greeter = Greeter()
    return greeter.name

@functions_framework.http
def main(request):
    common_greeting = greeting()
    random_number = random()
    return "Hello world! " + common_greeting + str(random_number)

