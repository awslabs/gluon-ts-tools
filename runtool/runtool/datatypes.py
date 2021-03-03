from collections import UserDict, UserList
from typing import Any, Iterable, List, Type, Union
from toolz.dicttoolz import valmap


class DotDict(dict):
    """
    The `DotDict` class allows accessing items in a dict using a
    dot syntax.

    >>> dotdict = DotDict({"a":{"b":"hello"}})
    >>> dotdict.a.b
    'hello'
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, init_data: dict = {}):
        for key, value in init_data.items():
            if hasattr(value, "keys"):
                if isinstance(value, DotDict):
                    self[key] = value
                else:
                    self[key] = DotDict(value)
            else:
                self[key] = value

    def as_dict(self) -> dict:
        """
        Converts the DotDict into a python `dict` recursively.

        >>> dotdict = DotDict({"a": {"b": {"c": [0, DotDict({"d": 1})]}}})
        >>> type(dotdict)
        <class 'runtool.datatypes.DotDict'>
        >>> type(dotdict.a.b.c[1])
        <class 'runtool.datatypes.DotDict'>
        >>> as_dict = dotdict.as_dict()
        >>> type(as_dict)
        <class 'dict'>
        >>> type(as_dict["a"]["b"]["c"][1])
        <class 'dict'>
        """

        def convert(value: Any) -> Any:
            if isinstance(value, DotDict):
                return value.as_dict()
            elif isinstance(value, list):
                return list(map(convert, value))
            else:
                return value

        return {key: convert(value) for key, value in self.items()}


class ListNode(UserList):
    """
    A `ListNode` is a python list which can be added and multiplied
    with other `Node` and `ListNode` objects.

    NOTE:
        The `ListNode` is meant to be subclassed by the
        `Algorithms`, `Datasets` and `Experiments` classes.

    A `ListNode` plus a `ListNode` or `Node` results in a new `ListNode` with
    the contents of the two.

    >>> my_listnode = ListNode([Node({"hi": "there"})])
    >>> my_listnode + my_listnode
    ListNode([Node({'hi': 'there'}), Node({'hi': 'there'})])

    >>> my_listnode + Node({})
    ListNode([Node({'hi': 'there'}), Node({})])

    The addition is not commutative so the order matters.
    >>> Node({}) + my_listnode
    ListNode([Node({}), Node({'hi': 'there'})])

    If two `ListNodes` are multiplied they generate an `Experiments` object
    containing the cartesian product of all the items within the two `ListNodes`.
    The same is true when multiplying a `ListNode` with a `Node`.

    NOTE:
        The generated `Experiments` objects consists of multiple `Experiment`
        objects. Each`Experiment` objects requires an `Algorithm` and a `Dataset`
        object to be passed to them during initialization, otherwise an error
        is thrown. In order to satisfy this requirement, one of the ListNodes
        being multiplied needs to contain only `Algorithm` object and one of the
        ListNodes needs to contain only `Dataset` objects.

        Please refer to the documentation for `Algorithm`,
        `Dataset`, `Experiment` and `Experiments` for more details.

    Example:
    Multiplying a `ListNode` containing `Algorithm` objects with a `ListNode`
    containing `Dataset` objects. This generates an `Experiments` object.

    >>> algorithms = ListNode(
    ...     [
    ...         Algorithm({"image": "1", "instance": "1"}),
    ...         Algorithm({"image": "2", "instance": "2"}),
    ...     ]
    ... )
    >>> datasets = ListNode(
    ...     [
    ...         Dataset({"path": {"1": "1"}}),
    ...         Dataset({"path": {"2": "2"}}),
    ...     ]
    ... )
    >>> algorithms * datasets == Experiments(
    ...     [
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "1", "instance": "1"}),
    ...             Dataset({"path": {"1": "1"}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "1", "instance": "1"}),
    ...             Dataset({"path": {"2": "2"}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "2", "instance": "2"}),
    ...             Dataset({"path": {"1": "1"}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "2", "instance": "2"}),
    ...             Dataset({"path": {"2": "2"}}),
    ...         ),
    ...     ]
    ... )
    True
    """

    def __repr__(self) -> str:
        child_names = ", ".join([str(child) for child in self])
        return f"{type(self).__name__}([{child_names}])"

    def __add__(self, other: Union["Node", "ListNode"]) -> Any:
        """
        Returns a new `ListNode` (or any subclass) with `other` appended to `self`.
        """
        if isinstance(other, type(self)):
            return type(self)(list(self) + list(other))
        elif isinstance(other, Node):
            return type(self)(list(self) + [other])

        raise TypeError

    def __mul__(self, other: Union["Node", "ListNode"]) -> "Experiments":
        """
        Calculates the cartesian product of items in
        `self` and `other` and returns an `Experiment` object
        with the results.
        """
        if isinstance(other, ListNode) and not isinstance(
            other, (Experiments, Experiment)
        ):
            return Experiments(
                [
                    Experiment.from_nodes(node_1, node_2)
                    for node_1 in self
                    for node_2 in other
                ]
            )
        elif isinstance(other, Node):
            return Experiments(
                [Experiment.from_nodes(item, other) for item in self]
            )

        raise TypeError


class Experiments(ListNode):
    """
    The `Experiments` class contains a set of `Experiment` objects.
    Essentially, this class corresponds to a set of experiments one
    wish to execute.

    Since `Experiments` inherits from ListNode, they can be added.
    However, `Experiments` cannot be multiplied.

    >>> experiments = Experiments(
    ...     [
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "1", "instance": "1"}),
    ...             Dataset({"path": {"1": "1"}}),
    ...         )
    ...     ]
    ... )
    >>> len(experiments + experiments)
    2
    >>> type(experiments + experiments)
    <class 'runtool.datatypes.Experiments'>
    """

    def __init__(
        self, experiments: Union[Iterable[dict], Iterable["Experiment"]]
    ):
        if not self.verify(experiments):
            raise TypeError

        super().__init__(
            item if isinstance(item, Experiment) else Experiment(item)
            for item in experiments
        )

    @classmethod
    def verify(cls, data: Iterable) -> bool:
        """
        Check if the data has the correct structure to instantiate an
        experiment. Any iterable containing valid `Experiment` objects
        are valid `Experiments` object.
        """
        return data and all(map(Experiment.verify, data))

    __mul__ = None  # Experiments cannot be multiplied


class Datasets(ListNode):
    """
    The Datasets class contains a set of `Dataset` objects.
    >>> datasets = Datasets([Dataset({"path": {}})])
    >>> len(datasets)
    1

    A `Datasets` object can be added with another `Datasets` object
    to merge them into a new `Datasets` object.
    >>> len(datasets + datasets)
    2

    `Dataset` objects can be added to a `Datasets` object.
    >>> len(datasets + datasets + Dataset({"path": {}}))
    3

    `Datasets` can be multiplied with `Algorithms` and `Algorithm` objects to
    form `Experiments`.

    >>> algorithms = Algorithms(
    ...     [
    ...         Algorithm({"image": "1", "instance": "1"}),
    ...         Algorithm({"image": "2", "instance": "2"}),
    ...     ]
    ... )
    >>> datasets = Datasets(
    ...     [
    ...         Dataset({"path": {"1": "1"}}),
    ...         Dataset({"path": {"2": "2"}}),
    ...     ]
    ... )
    >>> datasets * algorithms == Experiments(
    ...     [
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "1", "instance": "1"}),
    ...             Dataset({"path": {"1": "1"}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "2", "instance": "2"}),
    ...             Dataset({"path": {"1": "1"}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "1", "instance": "1"}),
    ...             Dataset({"path": {"2": "2"}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "2", "instance": "2"}),
    ...             Dataset({"path": {"2": "2"}}),
    ...         ),
    ...     ]
    ... )
    True

    Upon instantiating a `Datasets` object with an iterable
    the Datasets.verify method checks that the iterable has the
    correct structure. If it does not, a TypeError is raised.

    >>> Datasets([Dataset({"smth": 1})])
    Traceback (most recent call last):
        ...
    TypeError
    >>> Datasets([Dataset({"path": {}})])
    Datasets([Dataset({'path': {}})])

    """

    def __init__(self, iterable: Iterable):
        if not self.verify(iterable):
            raise TypeError
        super().__init__(map(Dataset, iterable))

    @classmethod
    def verify(cls, data: Iterable) -> bool:
        """
        Any non empty iterable with valid `Dataset`
        objects is a valid `Datasets` object.
        """
        return data and all(map(Dataset.verify, data))


class Algorithms(ListNode):
    """
    The `Algorithms` class contains a set of `Algorithm` objects.
    >>> algorithms = Algorithms([Algorithm({"image": "", "instance": ""})])
    >>> len(algorithms)
    1

    A `Algorithms` object can be added with another `Algorithms` object
    to merge them into a new `Algorithms` object.
    >>> len(algorithms + algorithms)
    2

    `Algorithm` objects can be added to an `Algorithm` object.
    >>> len(algorithms + algorithms + Algorithm({"image": "", "instance": ""}))
    3

    `Algorithms` can be multiplied with `Datasets` and `Dataset` objects to
    form `Experiments` objects.

    >>> algorithms = Algorithms(
    ...     [
    ...         Algorithm({"image": "1", "instance": "1"}),
    ...         Algorithm({"image": "2", "instance": "2"}),
    ...     ]
    ... )
    >>> datasets = Datasets(
    ...     [
    ...         Dataset({"path": {"1": "1"}}),
    ...         Dataset({"path": {"2": "2"}}),
    ...     ]
    ... )
    >>> algorithms * datasets == Experiments(
    ...     [
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "1", "instance": "1"}),
    ...             Dataset({"path": {"1": "1"}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "1", "instance": "1"}),
    ...             Dataset({"path": {"2": "2"}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "2", "instance": "2"}),
    ...             Dataset({"path": {"1": "1"}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "2", "instance": "2"}),
    ...             Dataset({"path": {"2": "2"}}),
    ...         ),
    ...     ]
    ... )
    True

    Upon instantiating a `Algorithms` object with an iterable
    the Algorithms.verify method checks that the iterable has the
    correct structure. If it does not, a TypeError is raised.

    >>> Algorithms([{"a": "1"}])
    Traceback (most recent call last):
        ...
    TypeError
    >>> Algorithms([Algorithm({"image": "", "instance": ""})])
    Algorithms([Algorithm({'image': '', 'instance': ''})])

    """

    def __init__(self, data):
        if not self.verify(data):
            raise TypeError

        super().__init__(map(Algorithm, data))

    @classmethod
    def verify(cls, data: Iterable) -> bool:
        """
        Any non empty iterable containing valid `Algorithm`
        objects is a valid `Algorithms` object.
        """
        return data and all(map(Algorithm.verify, data))


class Node(UserDict):
    """
    A `Node` is a dictionary which can be added and multiplied with
    `Node` and `ListNode` objects.

    NOTE:
        This class is meant to be subclassed by the:
        `Algorithm`, `Dataset` and `Experiment` classes.

    >>> my_node = Node({"hello": "world"})

    Per default, a node added to another node produces a ListNode
    containing the two nodes.

    >>> my_node + my_node
    ListNode([Node({'hello': 'world'}), Node({'hello': 'world'})])

    However, this can be overriden by setting the `result_type` variable
    of the `Node`. This is especially useful when subclassing the `Node` class.

    >>> class my_class(Node):
    ...     result_type = tuple
    >>> my_class({}) + my_class({"hi": 1})
    (my_class({}), my_class({'hi': 1}))

    A `Node` can be multiplied with either a `Node` or `ListNode` object.
    When multiplied, the results will be an `Experiments` object.

    NOTE:
        The `Experiment` class requires an `Algorithm` and `Dataset` object,
        upon instantiation otherwise an error is thrown.
        Please refer to the documentation for `Algorithm` and
        `Dataset` for examples of multiplication of `Node` objects.
    """

    # This variable determines what datatype __add__ returns
    result_type: Iterable = ListNode

    def __repr__(self) -> str:
        return f"{type(self).__name__}({dict(self)})"

    def __mul__(self, other) -> "Experiments":
        """
        Calculates the cartesian product combining a `Node` with a `Node` or `ListNode`
        and returns an `Experiments` object containing the result.
        """
        if isinstance(other, Node):
            return Experiments([Experiment.from_nodes(self, other)])
        if isinstance(other, ListNode):
            return Experiments(
                [Experiment.from_nodes(self, item) for item in other]
            )

        raise TypeError(f"Unable to multiply {type(self)} with {type(other)}")

    def __add__(self, other) -> Any:
        """
        Merges multiple instances of the same Node type into an instance of
        the class stored in the `self.result_type` variable.
        This allows any classes inheriting from `Node` to customize the
        return type of __add__ without redefining the logic.
        """
        if isinstance(other, type(self)):
            return self.result_type([self, other])
        elif isinstance(other, self.result_type):
            return self.result_type([self]) + other

        raise TypeError


class Algorithm(Node):
    """
    The `Algorithm` class represents a single algorithm in a config file.
    The class contains rules for identifying if an object has the
    correct structure to be an `Algorithm`, see the `verify` method.

    Two `Algorithm` objects can be added together to form an
    `Algorithms` object.

    >>> algorithm = Algorithm({"image": "", "instance": ""})
    >>> algorithm + algorithm == Algorithms([algorithm, algorithm])
    True

    An `Algorithm` can be multiplied with a `Dataset` object to form an
    `Experiments` object.

    >>> dataset = Dataset({"path": {}})
    >>> algorithm * dataset == Experiments(
    ...     [Experiment.from_nodes(algorithm, dataset)]
    ... )
    True

    An Algorithm can also be multiplied with a `Datasets` object in order to
    form several `Experiment` objects at once.
    >>> algorithm * Datasets(
    ...     [{"path": {"1": ""}}, {"path": {"2": ""}}]
    ... ) == Experiments(
    ...     [
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "", "instance": ""}),
    ...             Dataset({"path": {"1": ""}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "", "instance": ""}),
    ...             Dataset({"path": {"2": ""}}),
    ...         ),
    ...     ]
    ... )
    True
    """

    # __add__ returns an Algorithms object
    result_type = Algorithms

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not Algorithm.verify(self):
            raise TypeError

    @classmethod
    def verify(cls, data: dict) -> bool:
        """
        Determines if data has the structure needed to be an Algorithm.
        An Algorithm is defined as being a dictionary with atleast
        these two key-value pairs:

        - image: String
        - instance: String
        - hyperparameters: Optional[Dict]

        >>> Algorithm.verify({"a": "b"})
        False
        >>> Algorithm.verify({"image": "", "instance": ""})
        True
        >>> Algorithm.verify({"image": "", "instance": "", "hyperparameters": ""})
        False
        >>> Algorithm.verify({"image": "", "instance": "", "hyperparameters": {}})
        True
        """
        return (
            isinstance(data.get("image"), str)
            and isinstance(data.get("instance"), str)
            and isinstance(data.get("hyperparameters", {}), dict)
        )


class Dataset(Node):
    """
    The `Dataset` class represents a single dataset in a config file.
    The class contains rules for identifying if an object has the
    correct structure to be a `Dataset`, see the `verify` method.

    Two `Dataset` objects can be added together to form a
    `Datasets` object.

    >>> dataset = Dataset({"path": {}})
    >>> dataset + dataset
    Datasets([Dataset({'path': {}}), Dataset({'path': {}})])

    An `Algorithm` can be multiplied with a `Dataset` object
    to form an `Experiments` object.

    >>> algorithm = Algorithm({"image": "", "instance": ""})
    >>> dataset * algorithm == (
    ...     Experiments([Experiment.from_nodes(algorithm, dataset)])
    ... )
    True

    A `Dataset` can also be multiplied with an `Algorithms` object in order to
    form several `Experiment` objects at once.

    >>> dataset * Algorithms(
    ...     [
    ...         {"image": "1", "instance": "1"},
    ...         {"image": "2", "instance": "2"},
    ...     ]
    ... ) == Experiments(
    ...     [
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "1", "instance": "1"}),
    ...             Dataset({"path": {}}),
    ...         ),
    ...         Experiment.from_nodes(
    ...             Algorithm({"image": "2", "instance": "2"}),
    ...             Dataset({"path": {}}),
    ...         ),
    ...     ]
    ... )
    True

    Upon instantiating a `Dataset` object the `Dataset.verify` method checks
    that the parameter has the correct structure. If it does not, a TypeError
    is raised.

    >>> Dataset({"a": 1})
    Traceback (most recent call last):
        ...
    TypeError
    >>> Dataset({"path": {}})
    Dataset({'path': {}})
    """

    # __add__ should return a Datasets object
    result_type = Datasets

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not Dataset.verify(self):
            raise TypeError

    @classmethod
    def verify(cls, data: dict) -> bool:
        """
        Determines if the data parameter has the structure needed
        to be a `Dataset`. An Algorithm is defined as being a
        dictionary with atleast the following key-value pairs:

        - path: Dict
        - meta: Optional[Dict]
        """
        return isinstance(data.get("path"), dict) and isinstance(
            data.get("meta", {}), dict
        )


class Experiment(Node):
    """
    The Experiment class represents an `Algorithm`, `Dataset` combination.
    The class contains rules for identifying if an object has the
    correct structure to be an `Experiment`, see the `verify` method.

    Two experiments can be added to form an `Experiments` object.

    >>> experiment = Experiment(
    ...     {
    ...         "algorithm": {"image": "", "instance": ""},
    ...         "dataset": {"path": {}}
    ...     }
    ... )
    >>> type(experiment + experiment)
    <class 'runtool.datatypes.Experiments'>

    Upon instantiating a `Experiment` object the `Experiment.verify` method checks
    that the parameter has the correct structure. If it does not, a TypeError
    is raised.
    """

    # __add__ should return an Experiments object
    result_type = Experiments

    def __init__(self, node: dict):
        super().__init__(node)
        if not Experiment.verify(self):
            raise TypeError(
                "An Experiment requires a dict containing a valid "
                f"Dataset and an Algorithm, got: {dict(self)}"
            )

    def to_dict(self):
        return dict(valmap(dict, self))

    @classmethod
    def from_nodes(cls, node_1: dict, node_2: dict) -> "Experiment":
        """
        Given two dictionaries tries to generate an Experiment object.
        If not exactly one node is a valid Dataset and one exactly node
        is a valid Algorithm this raises a TypeError.
        """
        try:
            return cls({"algorithm": node_1, "dataset": node_2})
        except TypeError:
            pass

        try:
            return cls({"algorithm": node_2, "dataset": node_1})
        except TypeError:
            raise TypeError(
                "An Experiment requires one Dataset and one Algorithm, got: "
                f"{node_1} and {node_2}"
            )

    @classmethod
    def verify(cls, data: dict) -> bool:
        """
        Any dict with the following structure is a valid Experiment object
        {
            "algorithm": Algorithm,
            "dataset": Dataset
        }
        """
        return Algorithm.verify(data.get("algorithm", {})) and Dataset.verify(
            data.get("dataset", {})
        )

    __mul__ = None  # An Experiment cannot be multiplied
