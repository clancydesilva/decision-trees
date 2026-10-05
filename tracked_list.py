class TrackedList:
    # Wraps a list so every comparison and swap an algorithm makes is recorded
    def __init__(self, array):
        self.array = list(array)      # working copy the algorithm mutates
        self.original = list(array)   # untouched input, used for replay verification
        self.comparisons = []         # (i, j, result) where result is array[i] < array[j]
        self.swaps = []               # (i, j) in the order they were applied
        self.events = []              # interleaved log: ('cmp', i, j, result) or ('swap', i, j)

    def compare(self, i, j):
        # The only sanctioned way for an algorithm to compare two elements
        result = self.array[i] < self.array[j]
        self.comparisons.append((i, j, result))
        self.events.append(('cmp', i, j, result))
        return result

    def swap(self, i, j):
        # The only sanctioned way for an algorithm to move elements
        self.array[i], self.array[j] = self.array[j], self.array[i]
        self.swaps.append((i, j))
        self.events.append(('swap', i, j))

    def reset(self):
        # Restore the original input and clear all recorded history
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
    def comparisonCount(self):
        # Total number of tracked comparisons performed
        return len(self.comparisons)

    @property
    def swapCount(self):
        # Total number of tracked swaps performed
        return len(self.swaps)