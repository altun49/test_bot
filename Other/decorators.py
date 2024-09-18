# есть функция, которая принимает список из целых положительных чисел и возвращает только чётные значения
# написать собственный декоратор который будет менять поведение функции
# декоратор должен поменять поведение функции так, чтобы функция возвращала только четные отрицательные значения

num = [1, 3, -2, 56, -123, 94, 87, 45, -44, 90001, -1]


def my_decorator(func):
    def wrapper(*args):
        result = func(*args)
        return [x for x in result if x < 0 and x % 2 == 0]
    return wrapper


@my_decorator
def get_even_number(numbers: list[int]):
    return [element for element in numbers if element % 2 == 0]


result_decorator = get_even_number(num)
print(result_decorator)
