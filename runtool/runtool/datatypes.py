class Versions:
    versions = None

    def __init__(self, versions_to_add):
        assert isinstance(versions_to_add, list)
        self.versions = versions_to_add

    def flatten(self):
        if isinstance(self.versions[0], ListNode):
            # return self.versions
            original_class = self.versions[0].__class__
            new = []
            for version in self.versions:
                new += [item for item in version if item not in new]
            flattened = new
            return original_class(flattened)
        else:
            return self.versions

    def __repr__(self):
        return f"Versions({self.versions})"

    def __getitem__(self, key):
        return self.versions[key]

    def __len__(self):
        return len(self.versions)

    def __mul__(self, other):
        if not isinstance(other, Versions):
            return other * self

        multiplied = [
            item_self * item_other
            for item_self in self.versions
            for item_other in other.versions
        ]

        assert isinstance(
            multiplied[0],
            (
                Experiments,
                Experiment,
            ),
        )
        new = multiplied.pop()
        while len(multiplied) > 0:
            new = new + multiplied.pop()

        return new

    def __add__(self, other):
        raise NotImplementedError


class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, init_data={}):
        assert isinstance(init_data, dict)
        for key, value in init_data.items():
            if hasattr(value, "keys"):
                if isinstance(value, DotDict):
                    self[key] = value
                else:
                    self[key] = DotDict(value)
            else:
                self[key] = value

    def to_dict(self):
        for key, value in self.items():
            if hasattr(value, "keys"):
                self[key] = dict(value)
            else:
                self[key] = value
        return dict(self)

    def get_path(self, path_as_list):
        current = self
        for index in path_as_list:
            current = current[index]
        return current

    def to_base(self):
        new = {}
        for key in self:
            if isinstance(self[key], (DotDict, ListNode)):
                new[key] = self[key].to_base()
            else:
                new[key] = self[key]
        return new


class Node(DotDict):
    def __repr__(self):
        return f"{type(self).__name__}({self.items()})"

    def __hash__(self):
        return hash(str(self))


class ListNode(list):
    def __repr__(self):
        child_names = ", ".join([str(child) for child in self])

        return f"{type(self).__name__}({child_names})"

    def to_base(self):
        return [item.to_base() for item in self]


class Algorithm(Node):
    @classmethod
    def verify(cls, data):
        try:
            assert "image" in data
            assert "instance" in data

            if "hyperparameters" in data:
                assert isinstance(data["hyperparameters"], dict)
            return True
        except Exception:
            return False

    def __mul__(self, other):
        if type(other) is Dataset:
            return Experiments([Experiment(self, other)])
        elif type(other) is Datasets:
            return Experiments([Experiment(self, ds) for ds in other])
        elif type(other) is Versions:
            if isinstance(other[0], Datasets):
                return self * other.flatten()
            elif isinstance(other[0], Dataset):
                return self * Datasets(other.flatten())
            return other * self
        else:
            raise TypeError(f"Unable to multiply Algorithm with {type(other)}")

    def __add__(self, other):
        if type(other) is Algorithm:
            return Algorithms([self, other])
        elif type(other) is Algorithms:
            return Algorithms([self]) + other
        else:
            raise TypeError


class Algorithms(ListNode):
    def __init__(self, data):
        if not self.verify(data):
            raise TypeError

        for algo in data:
            self.append(Algorithm(algo))

    @classmethod
    def verify(cls, data):
        for item in data:
            if not Algorithm.verify(item):
                return False
        return True

    def __add__(self, other):
        if type(other) is Algorithms:
            return Algorithms(self + other)
        elif type(other) is Algorithm:
            return Algorithms(self + [other])
        else:
            raise TypeError

    def __mul__(self, other):
        if type(other) is Datasets:
            return Experiments(
                [
                    Experiment(algorithm=algo, dataset=ds)
                    for algo in self
                    for ds in other
                ]
            )
        elif type(other) is Dataset:
            return Experiments(
                [Experiment(algorithm=algo, dataset=other) for algo in self]
            )
        elif type(other) is Versions:
            if isinstance(other[0], Datasets):
                return self * other.flatten()
            elif isinstance(other[0], Dataset):
                return self * Datasets(other.flatten())

            return other * self
        else:
            raise TypeError


class Dataset(Node):
    @classmethod
    def verify(cls, data):
        try:
            assert len(data["path"]) > 0
            assert isinstance(data["path"], dict)
            if "meta" in data:
                assert isinstance(data["meta"], dict)
            return True
        except Exception:
            return False

    def __mul__(self, other):
        if type(other) is Algorithm:
            return Experiments([Experiment(algorithm=other, dataset=self)])
        elif type(other) is Algorithms:
            return Experiments(
                [Experiment(algorithm=algo, dataset=self) for algo in other]
            )
        elif type(other) is Versions:
            if isinstance(other[0], Algorithms):
                return self * other.flatten()
            elif isinstance(other[0], Algorithm):
                return self * Algorithms(other.flatten())
            return other * self
        else:
            raise TypeError

    def __add__(self, other):
        if type(other) is Dataset:
            return Datasets([self, other])
        elif type(other) is Datasets:
            return Datasets([self]) + other
        else:
            raise TypeError


class Datasets(ListNode):
    def __init__(self, data):
        if not self.verify(data):
            raise TypeError

        for ds in data:
            self.append(Dataset(ds))

    @classmethod
    def verify(cls, data):
        for item in data:
            if not Dataset.verify(item):
                return False
        return True

    def __add__(self, other):
        if type(other) is Datasets:
            return Datasets(self + other)
        elif type(other) is Dataset or type(other) is Generic:
            return Datasets(self + [other])
        else:
            raise TypeError

    def __mul__(self, other):
        if type(other) is Algorithms:
            return Experiments(
                [
                    Experiment(algorithm=algo, dataset=dataset)
                    for algo in other
                    for dataset in self
                ]
            )
        elif type(other) is Algorithm:
            return Experiments(
                [
                    Experiment(algorithm=other, dataset=dataset)
                    for dataset in self
                ]
            )
        elif type(other) is Versions:
            if isinstance(other[0], Algorithms):
                return self * other.flatten()
            elif isinstance(other[0], Algorithm):
                return self * Algorithms(other.flatten())
            return other * self
        else:
            raise TypeError


class Generic(Node):
    @classmethod
    def verify(cls, data):
        return True

    def __add__(self, other):
        if type(other) is Generic:
            return Generics([self, other])
        elif type(other) is Generics:
            return Generics([self]) + other
        else:
            raise TypeError

    def __mul__(self, other):
        if type(other) is Datasets:
            return Experiments(
                [Experiment(algorithm=self, dataset=item) for item in other]
            )
        elif type(other) is Algorithms:
            return Experiments(
                [Experiment(algorithm=item, dataset=self) for item in other]
            )
        elif type(other) is Algorithm:
            return Experiments([Experiment(algorithm=other, dataset=self)])
        elif type(other) is Dataset:
            return Experiments([Experiment(algorithm=self, dataset=other)])
        elif type(other) is Versions:
            if isinstance(
                other[0],
                (
                    Algorithms,
                    Datasets,
                ),
            ):
                return self * other.flatten()
            return other * self
        else:
            raise TypeError

    def __rmul__(self, other):
        return self * other


class Generics(ListNode):
    def __init__(self, data):
        for item in data:
            self.append(Generic(item))

    def __add__(self, other):
        if type(other) is Generics:
            return Generics(self + other)
        elif type(other) is Generic:
            return Generics(self + [other])
        else:
            raise TypeError

    def __mul__(self, other):
        if type(other) is Generics or type(other) is Datasets:
            return Experiments(
                [
                    Experiment(algorithm=algo, dataset=ds)
                    for ds in other
                    for algo in self
                ]
            )
        elif type(other) is Generic or type(other) is Dataset:
            return Experiments(
                [Experiment(algorithm=algo, dataset=other) for algo in self]
            )
        elif type(other) is Algorithm:
            return Experiments(
                [
                    Experiment(algorithm=algo, dataset=ds)
                    for algo in other
                    for ds in self
                ]
            )
        elif type(other) is Algorithm:
            return Experiments(
                [Experiment(algorithm=other, dataset=ds) for ds in self]
            )
        elif type(other) is Versions:
            if isinstance(
                other[0],
                (
                    Algorithms,
                    Datasets,
                ),
            ):
                return self * other.flatten()
            return other * self
        else:
            raise TypeError

    def __rmul__(self, other):
        return self * other


class Experiment(Node):
    def __init__(self, algorithm, dataset):

        self["algorithm"] = algorithm
        self["dataset"] = dataset

        if type(algorithm) is Generic or type(dataset) is Generic:
            try:
                print(
                    "Warning using a Generic in an Experiment is likely going to fail!\n"
                    f"algorithm\t{algorithm}\n"
                    f"dataset:\t{dataset}"
                )
                self.verify(self)
            except:
                raise TypeError(
                    "Unable to convert Generic object to Algorithm or Dataset"
                )

    @classmethod
    def verify(cls, data):
        try:
            assert Algorithm.verify(data["algorithm"])
            assert Dataset.verify(data["dataset"])
            return True
        except Exception:
            return False


class Experiments(ListNode):
    def __init__(self, experiments):
        if not self.verify(experiments):
            raise TypeError

        for item in experiments:
            if not type(item) is Experiment:
                item = Experiment(
                    algorithm=item["algorithm"], dataset=item["dataset"]
                )
            self.append(item)

    @classmethod
    def verify(cls, data):
        for item in data:
            if not Experiment.verify(item):
                print(f"expected an Experiment, found {type(item)}")
                return False
        return True

    def __add__(self, other):
        if type(other) is Experiments:
            return Experiments(list(self) + list(other))
        elif type(other) is Experiment:
            return Experiments(list(self) + [other])
        else:
            raise TypeError
