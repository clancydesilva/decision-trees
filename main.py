import json
from itertools import permutations
from math import factorial
from tracked_list import TrackedList
from algorithms import ALL_ALGORITHMS, ALGORITHM_INFO


class DecisionLeaf:
    __slots__ = ('permutations',)

    def __init__(self):
        self.permutations = []

    def add(self, input_perm, output, swaps):
        self.permutations.append({
            'input': tuple(input_perm),
            'output': tuple(output),
            'swaps': list(swaps),
        })

    @property
    def is_leaf(self):
        return True

    def verify(self):
        for p in self.permutations:
            replayed = list(p['input'])
            for i, j in p['swaps']:
                replayed[i], replayed[j] = replayed[j], replayed[i]
            if tuple(replayed) != p['output']:
                return False
            if replayed != sorted(p['input']):
                return False
        return True

    def depth(self):
        return 0

    def leaf_count(self):
        return 1

    def node_count(self):
        return 1

    def all_leaf_depths(self, current_depth=0):
        return [current_depth] * len(self.permutations)

    def leaves(self):
        yield self

    def to_dict(self, branch_label=None):
        inputs = [list(p['input']) for p in self.permutations]
        attrs = {'type': 'leaf', 'count': len(self.permutations)}
        if branch_label is not None:
            attrs['branch'] = branch_label
        if len(inputs) == 1:
            attrs['input'] = str(inputs[0])
            attrs['output'] = str(list(self.permutations[0]['output']))
        return {
            'name': f"Leaf ({len(inputs)})",
            'attributes': attrs,
            'permutations': [
                {
                    'input': list(p['input']),
                    'output': list(p['output']),
                    'swaps': p['swaps'],
                }
                for p in self.permutations
            ],
        }

    def __repr__(self):
        inputs = [p['input'] for p in self.permutations]
        return f"Leaf({inputs})"


class DecisionNode:
    __slots__ = ('i', 'j', 'true_child', 'false_child')

    def __init__(self, i, j):
        self.i = i
        self.j = j
        self.true_child = None   # a[i] < a[j] is True
        self.false_child = None  # a[i] < a[j] is False

    @property
    def is_leaf(self):
        return False

    def depth(self):
        td = self.true_child.depth() if self.true_child else 0
        fd = self.false_child.depth() if self.false_child else 0
        return 1 + max(td, fd)

    def leaf_count(self):
        c = 0
        if self.true_child:
            c += self.true_child.leaf_count()
        if self.false_child:
            c += self.false_child.leaf_count()
        return c

    def node_count(self):
        c = 1
        if self.true_child:
            c += self.true_child.node_count()
        if self.false_child:
            c += self.false_child.node_count()
        return c

    def all_leaf_depths(self, current_depth=0):
        depths = []
        if self.true_child:
            depths.extend(self.true_child.all_leaf_depths(current_depth + 1))
        if self.false_child:
            depths.extend(self.false_child.all_leaf_depths(current_depth + 1))
        return depths

    def leaves(self):
        if self.true_child:
            yield from self.true_child.leaves()
        if self.false_child:
            yield from self.false_child.leaves()

    def to_dict(self, branch_label=None):
        attrs = {'type': 'comparison', 'i': self.i, 'j': self.j}
        if branch_label is not None:
            attrs['branch'] = branch_label
        children = []
        if self.true_child:
            children.append(self.true_child.to_dict(branch_label='Yes'))
        if self.false_child:
            children.append(self.false_child.to_dict(branch_label='No'))
        return {
            'name': f'a[{self.i}] < a[{self.j}]?',
            'attributes': attrs,
            'children': children,
        }

    def __repr__(self):
        return f"Node(a[{self.i}] < a[{self.j}]?)"


class DecisionTree:
    def __init__(self, algorithm, n):
        self.algorithm = algorithm
        self.algorithm_name = ALGORITHM_INFO[algorithm]['name']
        self.n = n
        self.root = None
        self._build()

    def _build(self):
        for perm in permutations(range(1, self.n + 1)):
            tracker = TrackedList(list(perm))
            self.algorithm(tracker)
            self._insert(
                tracker.comparisons,
                list(perm),
                list(tracker.array),
                list(tracker.swaps),
            )

    def _insert(self, comparisons, input_perm, output, swaps):
        if not comparisons:  # zero comparisons (n <= 1)
            if self.root is None:
                self.root = DecisionLeaf()
            self.root.add(input_perm, output, swaps)
            return

        i0, j0, _ = comparisons[0]
        if self.root is None:
            self.root = DecisionNode(i0, j0)

        node = self.root
        for step, (i, j, result) in enumerate(comparisons):
            if node.is_leaf:
                raise ValueError(
                    f"Hit a leaf at step {step}, but the path for input "
                    f"{input_perm} has more comparisons remaining."
                )
            if (node.i, node.j) != (i, j):
                raise ValueError(
                    f"Comparison mismatch at step {step}: tree expects "
                    f"a[{node.i}]<a[{node.j}] but this run produced "
                    f"a[{i}]<a[{j}] (input={input_perm})."
                )

            is_last = (step == len(comparisons) - 1)

            if result:  # true branch
                if is_last:
                    if node.true_child is None:
                        node.true_child = DecisionLeaf()
                    if not node.true_child.is_leaf:
                        raise ValueError(
                            f"Path for {input_perm} ends at step {step} "
                            f"(True branch) but an internal node already "
                            f"exists there."
                        )
                    node.true_child.add(input_perm, output, swaps)
                else:
                    next_i, next_j, _ = comparisons[step + 1]
                    if node.true_child is None:
                        node.true_child = DecisionNode(next_i, next_j)
                    node = node.true_child

            else:  # false branch
                if is_last:
                    if node.false_child is None:
                        node.false_child = DecisionLeaf()
                    if not node.false_child.is_leaf:
                        raise ValueError(
                            f"Path for {input_perm} ends at step {step} "
                            f"(False branch) but an internal node already "
                            f"exists there."
                        )
                    node.false_child.add(input_perm, output, swaps)
                else:
                    next_i, next_j, _ = comparisons[step + 1]
                    if node.false_child is None:
                        node.false_child = DecisionNode(next_i, next_j)
                    node = node.false_child

    def depth(self):
        return self.root.depth() if self.root else 0

    def leaf_count(self):
        return self.root.leaf_count() if self.root else 0

    def node_count(self):
        return self.root.node_count() if self.root else 0

    def internal_node_count(self):
        return self.node_count() - self.leaf_count()

    def average_depth(self):
        if not self.root:
            return 0.0
        depths = self.root.all_leaf_depths()
        return sum(depths) / len(depths) if depths else 0.0

    def min_depth(self):
        depths = self.root.all_leaf_depths() if self.root else []
        return min(depths) if depths else 0

    def max_depth(self):
        return self.depth()

    def leaves(self):
        if self.root:
            yield from self.root.leaves()

    def verify_all_leaves(self):
        return all(leaf.verify() for leaf in self.leaves())

    def print_tree(self, max_depth=None):
        if self.root is None:
            print("(empty tree)")
            return
        if self.root.is_leaf:
            for p in self.root.permutations:
                print(f"LEAF: {p['input']} → {p['output']}")
            return
        print(f"a[{self.root.i}] < a[{self.root.j}]?")
        self._print_children(self.root, "", 1, max_depth)

    def _print_children(self, node, prefix, depth, max_depth):
        branches = []
        if node.true_child is not None:
            branches.append(("Y", node.true_child))
        if node.false_child is not None:
            branches.append(("N", node.false_child))

        for idx, (label, child) in enumerate(branches):
            is_last = (idx == len(branches) - 1)
            connector = "`-- " if is_last else "|-- "
            extension = "    " if is_last else "|   "

            if child.is_leaf:
                inputs = ", ".join(str(p['input']) for p in child.permutations)
                print(f"{prefix}{connector}{label}: LEAF [{inputs}]")

            elif max_depth is not None and depth >= max_depth:
                lc = child.leaf_count()
                print(f"{prefix}{connector}{label}: a[{child.i}] < a[{child.j}]? "
                      f"(... {lc} leaves below)")

            else:
                print(f"{prefix}{connector}{label}: a[{child.i}] < a[{child.j}]?")
                self._print_children(
                    child, prefix + extension, depth + 1, max_depth
                )

    def summary(self):
        return (
            f"DecisionTree: {self.algorithm_name}, n={self.n}\n"
            f"  Permutations:     {factorial(self.n)}\n"
            f"  Leaves:           {self.leaf_count()}\n"
            f"  Internal nodes:   {self.internal_node_count()}\n"
            f"  Total nodes:      {self.node_count()}\n"
            f"  Min depth:        {self.min_depth()}\n"
            f"  Max depth:        {self.max_depth()}\n"
            f"  Avg depth:        {self.average_depth():.2f}\n"
            f"  All leaves valid: {self.verify_all_leaves()}"
        )

    def to_dict(self):
        tree_data = self.root.to_dict() if self.root else {'name': '(empty)'}
        return {
            'algorithm': self.algorithm_name,
            'n': self.n,
            'stats': {
                'permutations': factorial(self.n),
                'leaves': self.leaf_count(),
                'internal_nodes': self.internal_node_count(),
                'total_nodes': self.node_count(),
                'min_depth': self.min_depth(),
                'max_depth': self.max_depth(),
                'avg_depth': round(self.average_depth(), 2),
                'all_valid': self.verify_all_leaves(),
            },
            'tree': tree_data,
        }

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), **kwargs)

    def __repr__(self):
        return (f"DecisionTree({self.algorithm_name}, n={self.n}, "
                f"leaves={self.leaf_count()}, depth={self.depth()})")


def build_all_trees(n, algorithms=None):
    if algorithms is None:
        algorithms = ALL_ALGORITHMS
    return {algo: DecisionTree(algo, n) for algo in algorithms}


if __name__ == "__main__":
    from algorithms import insertion_sort

    n = 3
    print("=" * 60)
    print(f"  Insertion Sort — n={n} ({factorial(n)} permutations)")
    print("=" * 60)
    tree = DecisionTree(insertion_sort, n)
    tree.print_tree()
    print()
    print(tree.summary())

    n = 4
    print("\n" + "=" * 60)
    print(f"  All algorithms — n={n} ({factorial(n)} permutations)")
    print("=" * 60)
    trees = build_all_trees(n)

    header = (f"{'Algorithm':<28} {'Leaves':>6} {'Internal':>8} "
              f"{'Depth':>5} {'Min':>4} {'Avg':>7} {'Valid':>5}")
    print(header)
    print("-" * len(header))
    for algo, t in trees.items():
        valid = "Y" if t.verify_all_leaves() else "N"
        print(f"{t.algorithm_name:<28} {t.leaf_count():>6} "
              f"{t.internal_node_count():>8} {t.max_depth():>5} "
              f"{t.min_depth():>4} {t.average_depth():>7.2f} {valid:>5}")
