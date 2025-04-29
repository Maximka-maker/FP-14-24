from typing import Generator

test = "пары"

def generate_trip() -> Generator[str, str, str]:
    yield "поступили в университет"
    yield f"отправились на {test}"
    yield "покинули университет"

route = generate_trip()
print("test")
for i in range(3):
    print(next(route))