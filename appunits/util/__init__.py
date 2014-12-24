class NOT_SET:
    pass

def to(transform_func, *args, **kwargs):
    '''
    Calls the decorated function (usually, a generator function)
    with `args` and `kwargs` and passes the result to `transform_func`:

        @to(dict)
        def items():
            yield 'key', 'value'

    '''
    def decorate(g):
        return transform_func(g(*args, **kwargs))
    return decorate