import multiprocessing

def worker(num):
    print('Worker:', num)

if __name__ == '__main__':
    for i in range(20*20):
        p = multiprocessing.Process(target=worker, args=(i,))
        p.start()

def my_decorator(func):
    def wrapper(*args,**kwargs):
        print("Хуй да не хуй")
        result = func(*args, **kwargs)
        print(f'ARGS: {args}')
        print(f'KWARGS: {kwargs}')
        print("Любой код, исполняющийся после вызова функции")
        return result

    return wrapper

@my_decorator
def sumcha(a: int, b: int) -> int:
    return a*2+b


sumcha(2, 2)
