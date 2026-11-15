from math import factorial
from algorithms import insertionSort
from decision_tree import (
    DecisionLeaf,
    DecisionNode,
    DecisionTree,
    buildAllTrees,
    isSortedOutput,
    isValidMaxHeap,
)


if __name__ == "__main__":
    # CLI entry point demonstrating decision tree construction and verification
    n = 3
    print("=" * 60)
    print(f"  Insertion Sort — n={n} ({factorial(n)} permutations)")
    print("=" * 60)
    tree = DecisionTree(insertionSort, n)
    tree.printTree()
    print()
    print(tree.summary())

    n = 4
    print("\n" + "=" * 60)
    print(f"  All algorithms — n={n} ({factorial(n)} permutations)")
    print("=" * 60)
    trees = buildAllTrees(n)

    header = (f"{'Algorithm':<28} {'Leaves':>6} {'Internal':>8} "
              f"{'Depth':>5} {'Min':>4} {'Avg':>7} {'Valid':>5}")
    print(header)
    print("-" * len(header))
    for algo, t in trees.items():
        valid = "Y" if t.verifyAllLeaves() else "N"
        print(f"{t.algorithm_name:<28} {t.leafCount():>6} "
              f"{t.internalNodeCount():>8} {t.maxDepth():>5} "
              f"{t.minDepth():>4} {t.averageDepth():>7.2f} {valid:>5}")
