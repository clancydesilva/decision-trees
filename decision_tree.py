from itertools import permutations
from math import factorial
from tracked_list import TrackedList
from algorithms import ALL_ALGORITHMS, ALGORITHM_INFO

MAX_FULL_TREE_N = 7


def isSortedOutput(input_perm, output_seq):
    # Default leaf validator verifying that the output is a sorted permutation of the input
    return list(output_seq) == sorted(input_perm)


def isValidMaxHeap(input_perm, output_seq):
    # Validator for heap construction algorithms verifying permutation conservation and max-heap order
    if sorted(output_seq) != sorted(input_perm):
        return False
    n = len(output_seq)
    for idx in range(n // 2):
        left = 2 * idx + 1
        right = 2 * idx + 2
        if left < n and output_seq[idx] < output_seq[left]:
            return False
        if right < n and output_seq[idx] < output_seq[right]:
            return False
    return True


class DecisionLeaf:
    # Terminal leaf in the decision tree representing a set of inputs following identical comparison paths
    __slots__ = ('permutations',)

    def __init__(self):
        self.permutations = []

    def add(self, input_perm, output, swaps):
        # Store input permutation, resulting array output, and replayed swap sequence
        self.permutations.append({
            'input': tuple(input_perm),
            'output': tuple(output),
            'swaps': list(swaps),
        })

    @property
    def isLeaf(self):
        return True

    def verify(self, validator_fn=None):
        # Verify that replaying recorded swaps on each input permutation satisfies the target property
        check_fn = validator_fn or isSortedOutput
        for p in self.permutations:
            replayed = list(p['input'])
            for i, j in p['swaps']:
                replayed[i], replayed[j] = replayed[j], replayed[i]
            if tuple(replayed) != p['output']:
                return False
            if not check_fn(p['input'], replayed):
                return False
        return True

    def depth(self):
        return 0

    def leafCount(self):
        return 1

    def nodeCount(self):
        return 1

    def allLeafDepths(self, current_depth=0):
        # Return depth list repeated for each permutation arriving at this leaf
        return [current_depth] * len(self.permutations)

    def leaves(self):
        yield self

    def toDict(self, branch_label=None):
        # Serialise leaf data into structured dict for tree visualisation
        inputs = [list(p['input']) for p in self.permutations]
        attrs = {'type': 'leaf', 'count': len(self.permutations)}
        if branch_label is not None:
            attrs['branch'] = branch_label
        if len(inputs) == 1:
            attrs['input'] = str(inputs[0])
            attrs['output'] = str(list(self.permutations[0]['output']))
        elif len(inputs) > 1:
            attrs['input'] = f"{inputs[0]} (+{len(inputs) - 1} more)"
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
    # Internal decision node representing a binary comparison a[i] < a[j]
    __slots__ = ('i', 'j', 'true_child', 'false_child')

    def __init__(self, i, j):
        self.i = i
        self.j = j
        self.true_child = None   # branch where a[i] < a[j] is True
        self.false_child = None  # branch where a[i] < a[j] is False

    @property
    def isLeaf(self):
        return False

    def depth(self):
        # Recursively compute maximum height of the subtree
        td = self.true_child.depth() if self.true_child else 0
        fd = self.false_child.depth() if self.false_child else 0
        return 1 + max(td, fd)

    def leafCount(self):
        # Total number of leaves under this node
        c = 0
        if self.true_child:
            c += self.true_child.leafCount()
        if self.false_child:
            c += self.false_child.leafCount()
        return c

    def nodeCount(self):
        # Total count of all internal nodes and leaves under this node
        c = 1
        if self.true_child:
            c += self.true_child.nodeCount()
        if self.false_child:
            c += self.false_child.nodeCount()
        return c

    def allLeafDepths(self, current_depth=0):
        # Collect leaf depths for all branches beneath this node
        depths = []
        if self.true_child:
            depths.extend(self.true_child.allLeafDepths(current_depth + 1))
        if self.false_child:
            depths.extend(self.false_child.allLeafDepths(current_depth + 1))
        return depths

    def leaves(self):
        if self.true_child:
            yield from self.true_child.leaves()
        if self.false_child:
            yield from self.false_child.leaves()

    def toDict(self, branch_label=None):
        # Serialise node data into dict representation
        attrs = {'type': 'comparison', 'i': self.i, 'j': self.j}
        if branch_label is not None:
            attrs['branch'] = branch_label
        children = []
        if self.true_child:
            children.append(self.true_child.toDict(branch_label='Yes'))
        if self.false_child:
            children.append(self.false_child.toDict(branch_label='No'))
        return {
            'name': f'a[{self.i}] < a[{self.j}]?',
            'attributes': attrs,
            'children': children,
        }

    def __repr__(self):
        return f"Node(a[{self.i}] < a[{self.j}]?)"


class DecisionTree:
    # Full decision tree built from executing an algorithm across all n! permutations
    def __init__(self, algorithm, n, validator_fn=None):
        if n < 1 or n > MAX_FULL_TREE_N:
            raise ValueError(
                f"Input size n={n} is rejected. Full decision trees are hard-capped at n={MAX_FULL_TREE_N}."
            )
        self.algorithm = algorithm
        self.algorithm_name = ALGORITHM_INFO.get(algorithm, {}).get(
            'name', algorithm.__name__
        )
        self.n = n
        self.validator_fn = validator_fn or isSortedOutput
        self.root = None
        self._build()

    def _build(self):
        # Run algorithm on every permutation of size n and merge comparison logs into the tree
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
        # Insert a single permutation trace into the decision tree trie
        if not comparisons:
            if self.root is None:
                self.root = DecisionLeaf()
            self.root.add(input_perm, output, swaps)
            return

        i0, j0, _ = comparisons[0]
        if self.root is None:
            self.root = DecisionNode(i0, j0)

        node = self.root
        for step, (i, j, result) in enumerate(comparisons):
            if node.isLeaf:
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

            if result:
                # Follow or create True branch
                if is_last:
                    if node.true_child is None:
                        node.true_child = DecisionLeaf()
                    if not node.true_child.isLeaf:
                        raise ValueError(
                            f"Path for {input_perm} ends at step {step} "
                            f"(True branch) but an internal node already exists there."
                        )
                    node.true_child.add(input_perm, output, swaps)
                else:
                    next_i, next_j, _ = comparisons[step + 1]
                    if node.true_child is None:
                        node.true_child = DecisionNode(next_i, next_j)
                    node = node.true_child

            else:
                # Follow or create False branch
                if is_last:
                    if node.false_child is None:
                        node.false_child = DecisionLeaf()
                    if not node.false_child.isLeaf:
                        raise ValueError(
                            f"Path for {input_perm} ends at step {step} "
                            f"(False branch) but an internal node already exists there."
                        )
                    node.false_child.add(input_perm, output, swaps)
                else:
                    next_i, next_j, _ = comparisons[step + 1]
                    if node.false_child is None:
                        node.false_child = DecisionNode(next_i, next_j)
                    node = node.false_child

    def depth(self):
        return self.root.depth() if self.root else 0

    def leafCount(self):
        return self.root.leafCount() if self.root else 0

    def nodeCount(self):
        return self.root.nodeCount() if self.root else 0

    def internalNodeCount(self):
        return self.nodeCount() - self.leafCount()

    def averageDepth(self):
        # Compute mean comparison path length across all permutations
        if not self.root:
            return 0.0
        depths = self.root.allLeafDepths()
        return sum(depths) / len(depths) if depths else 0.0

    def minDepth(self):
        # Shortest comparison path to any leaf
        depths = self.root.allLeafDepths() if self.root else []
        return min(depths) if depths else 0

    def maxDepth(self):
        # Longest comparison path to any leaf
        return self.depth()

    def leaves(self):
        if self.root:
            yield from self.root.leaves()

    def verifyAllLeaves(self, validator_fn=None):
        # Ensure all leaves satisfy the verification predicate for every input permutation
        check_fn = validator_fn or self.validator_fn
        return all(leaf.verify(check_fn) for leaf in self.leaves())

    def printTree(self, max_depth=None):
        # Print textual tree representation up to optional max_depth
        if self.root is None:
            print("(empty tree)")
            return
        if self.root.isLeaf:
            for p in self.root.permutations:
                print(f"LEAF: {p['input']} → {p['output']}")
            return
        print(f"a[{self.root.i}] < a[{self.root.j}]?")
        self._printChildren(self.root, "", 1, max_depth)

    def _printChildren(self, node, prefix, depth, max_depth):
        # Recursively format child branches for console output
        branches = []
        if node.true_child is not None:
            branches.append(("Y", node.true_child))
        if node.false_child is not None:
            branches.append(("N", node.false_child))

        for idx, (label, child) in enumerate(branches):
            is_last = (idx == len(branches) - 1)
            connector = "`-- " if is_last else "|-- "
            extension = "    " if is_last else "|   "

            if child.isLeaf:
                inputs = ", ".join(str(p['input']) for p in child.permutations)
                print(f"{prefix}{connector}{label}: LEAF [{inputs}]")

            elif max_depth is not None and depth >= max_depth:
                lc = child.leafCount()
                print(f"{prefix}{connector}{label}: a[{child.i}] < a[{child.j}]? "
                      f"(... {lc} leaves below)")

            else:
                print(f"{prefix}{connector}{label}: a[{child.i}] < a[{child.j}]?")
                self._printChildren(
                    child, prefix + extension, depth + 1, max_depth
                )

    def summary(self):
        # Formatted string summary of tree statistics
        return (
            f"DecisionTree: {self.algorithm_name}, n={self.n}\n"
            f"  Permutations:     {factorial(self.n)}\n"
            f"  Leaves:           {self.leafCount()}\n"
            f"  Internal nodes:   {self.internalNodeCount()}\n"
            f"  Total nodes:      {self.nodeCount()}\n"
            f"  Min depth:        {self.minDepth()}\n"
            f"  Max depth:        {self.maxDepth()}\n"
            f"  Avg depth:        {self.averageDepth():.2f}\n"
            f"  All leaves valid: {self.verifyAllLeaves()}"
        )

    def toDict(self):
        # Convert tree structure and summary metrics to a dictionary
        tree_data = self.root.toDict() if self.root else {'name': '(empty)'}
        return {
            'algorithm': self.algorithm_name,
            'n': self.n,
            'stats': {
                'permutations': factorial(self.n),
                'leaves': self.leafCount(),
                'internal_nodes': self.internalNodeCount(),
                'total_nodes': self.nodeCount(),
                'min_depth': self.minDepth(),
                'max_depth': self.maxDepth(),
                'avg_depth': round(self.averageDepth(), 2),
                'all_valid': self.verifyAllLeaves(),
            },
            'tree': tree_data,
        }

    def __repr__(self):
        return (f"DecisionTree({self.algorithm_name}, n={self.n}, "
                f"leaves={self.leafCount()}, depth={self.depth()})")


def buildAllTrees(n, algorithms=None, validator_fn=None):
    # Construct decision trees for all specified algorithms on permutations of size n
    if algorithms is None:
        algorithms = ALL_ALGORITHMS
    return {algo: DecisionTree(algo, n, validator_fn=validator_fn) for algo in algorithms}
