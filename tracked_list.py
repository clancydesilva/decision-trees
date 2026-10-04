class TrackedList:
    def __init__(self, array):
        self.array = list(array)      
        self.original = list(array)   
        self.comparisons = []         
        self.swaps = []
        self.events = []  # interleaved log: ('cmp', i, j, result) or ('swap', i, j)

    def compare(self, i, j):
        result = self.array[i] < self.array[j]
        self.comparisons.append((i, j, result))
        self.events.append(('cmp', i, j, result))
        return result

    def swap(self, i, j):
        self.array[i], self.array[j] = self.array[j], self.array[i]
        self.swaps.append((i, j))
        self.events.append(('swap', i, j))

    def reset(self):
        self.array = list(self.original)
        self.comparisons.clear()
        self.swaps.clear()
        self.events.clear()

    def __len__(self):
        return len(self.array)

    def __getitem__(self, index):
        return self.array[index]

    def __iter__(self):
        return iter(self.array)

    def __eq__(self, other):
        if isinstance(other, TrackedList):
            return self.array == other.array
        return self.array == other

    def __repr__(self):
        return f"TrackedList({self.array})"

    def __str__(self):
        return str(self.array)

    @property
    def comparison_count(self):
        return len(self.comparisons)

    @property
    def swap_count(self):
        return len(self.swaps)