import functools

from toolz import valfilter


def ignore_nones(fn):
    """Decorator which calls `fn` with `*args, **kwargs`, but pops all items of
    `kwargs`, which are `None` (`foo(bar=None)` becomes `foo()`).

    This is useful when using boto3, since it often doesn't allow passing
    `None` as a not-specified value.

    ::

        @ignore_nones
        def foo(bar=42):
            return bar

        assert foo(None) == 42
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        kwargs = valfilter(lambda val: val is not None, kwargs)
        return fn(*args, **kwargs)

    return wrapper
