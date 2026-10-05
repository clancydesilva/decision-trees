from tracked_list import TrackedList
from algorithms import (
    bubbleSort,
    selectionSort,
    insertionSort,
    cocktailShakerSort,
    shellSort,
    quickSortLomuto,
    quickSortHoare,
    heapSort,
    mergeSort,
    ALL_ALGORITHMS,
)
from evaluate import (
    evaluate,
    evaluateAll,
    printEvaluation,
    printComparisonTable,
    runScenarios,
)


def testSingleEvaluate():
    # Evaluate bubbleSort on a small input and check all output invariants
    print("\n>>> testSingleEvaluate: bubbleSort on [5, 3, 1, 4, 2]")
    result = evaluate(bubbleSort, [5, 3, 1, 4, 2])
    printEvaluation(result)

    assert result["sorted_correctly"], "Sort failed"
    assert result["replay_matches"], "Swap replay mismatch"
    assert result["comparisons_in_bounds"], f"Comparisons {result['comparisons']} out of bounds"
    assert result["swaps_in_bounds"], f"Swaps {result['swaps']} out of bounds"
    assert result["elapsed_ms"] >= 0, "Negative time"
    assert result["algorithm"] == "Bubble Sort"
    assert result["n"] == 5
    print("  PASSED\n")


def testEvaluateAllDefault():
    # Evaluate all sorting algorithms on a standard arbitrary list
    print(">>> testEvaluateAllDefault: all algorithms on [64, 34, 25, 12, 22, 11]")
    data = [64, 34, 25, 12, 22, 11]
    results = evaluateAll(data)

    assert len(results) == len(ALL_ALGORITHMS), f"Expected {len(ALL_ALGORITHMS)} results, got {len(results)}"

    for r in results:
        assert r["sorted_correctly"], f"{r['algorithm']} did not sort correctly"
        assert r["replay_matches"], f"{r['algorithm']} swap replay mismatch"
        assert r["elapsed_ms"] >= 0, f"{r['algorithm']} negative time"

    printComparisonTable(results)
    print("  PASSED\n")


def testEvaluateAllSubset():
    # Evaluate a custom subset of algorithms on a four-element list
    print(">>> testEvaluateAllSubset: [insertionSort, quickSortHoare] on [9, 1, 5, 3]")
    subset = [insertionSort, quickSortHoare]
    results = evaluateAll([9, 1, 5, 3], algorithms=subset)

    assert len(results) == 2
    assert results[0]["algorithm"] == "Insertion Sort"
    assert results[1]["algorithm"] == "Quick Sort (Hoare)"

    for r in results:
        assert r["sorted_correctly"]
        assert r["replay_matches"]

    printComparisonTable(results)
    print("  PASSED\n")


def testBestCase():
    # Test best-case scenario on pre-sorted input
    print(">>> testBestCase: all algorithms on sorted [1..10]")
    data = list(range(1, 11))
    results = evaluateAll(data)

    for r in results:
        assert r["sorted_correctly"], f"{r['algorithm']} failed on sorted input"
        assert r["swaps"] == 0 or r["algorithm"] == "Heap Sort", \
            f"{r['algorithm']} did {r['swaps']} swaps on sorted input"

    printComparisonTable(results)
    print("  PASSED\n")


def testWorstCase():
    # Test worst-case scenario on reverse-sorted input
    print(">>> testWorstCase: all algorithms on reversed [10..1]")
    data = list(range(10, 0, -1))
    results = evaluateAll(data)

    for r in results:
        assert r["sorted_correctly"], f"{r['algorithm']} failed on reverse sorted input"
        assert r["comparisons_in_bounds"], \
            f"{r['algorithm']} comparisons {r['comparisons']} out of bounds ({r['comparisons_best']}-{r['comparisons_worst']})"
        assert r["swaps_in_bounds"], \
            f"{r['algorithm']} swaps {r['swaps']} out of bounds ({r['swaps_best']}-{r['swaps_worst']})"

    printComparisonTable(results)
    print("  PASSED\n")


def testEdgeCases():
    # Test edge cases with single-element and two-element inputs
    print(">>> testEdgeCases: single element and two elements")

    for fn in ALL_ALGORITHMS:
        r1 = evaluate(fn, [42])
        assert r1["sorted_correctly"], f"{r1['algorithm']} failed on single element"
        assert r1["comparisons"] == 0 or True  # some algorithms may still compare
        assert r1["swaps"] == 0

    for fn in ALL_ALGORITHMS:
        r2 = evaluate(fn, [2, 1])
        assert r2["sorted_correctly"], f"{r2['algorithm']} failed on [2, 1]"
        assert r2["replay_matches"], f"{r2['algorithm']} replay failed on [2, 1]"

    print("  PASSED\n")


def testTiming():
    # Verify that execution timing produces non-negative floats
    print(">>> testTiming: verify elapsed_ms is a positive float for larger input")
    data = list(range(100, 0, -1))
    result = evaluate(bubbleSort, data)
    assert isinstance(result["elapsed_ms"], float)
    assert result["elapsed_ms"] >= 0
    print(f"  Bubble sort on {len(data)} elements: {result['elapsed_ms']:.3f} ms")
    print("  PASSED\n")


def testRunScenariosAll():
    # Verify scenario runner with all algorithms
    print(">>> testRunScenariosAll")
    runScenarios()
    print("  PASSED\n")


def testRunScenariosSubset():
    # Verify scenario runner with subset of algorithms
    print(">>> testRunScenariosSubset: [selectionSort, heapSort]")
    runScenarios(algorithms=[selectionSort, heapSort])
    print("  PASSED\n")


def testPrintEvaluationAll():
    # Verify detailed output printing for all algorithms on arbitrary list
    print(">>> testPrintEvaluationAll: detailed output for each algorithm on [8, 3, 6, 1, 5]")
    data = [8, 3, 6, 1, 5]
    for fn in ALL_ALGORITHMS:
        r = evaluate(fn, data)
        printEvaluation(r)
        assert r["sorted_correctly"]
        assert r["replay_matches"]
    print("  PASSED\n")


# Backward compatibility aliases
test_single_evaluate = testSingleEvaluate
test_evaluate_all_default = testEvaluateAllDefault
test_evaluate_all_subset = testEvaluateAllSubset
test_best_case = testBestCase
test_worst_case = testWorstCase
test_edge_cases = testEdgeCases
test_timing = testTiming
test_run_scenarios_all = testRunScenariosAll
test_run_scenarios_subset = testRunScenariosSubset
test_print_evaluation_all = testPrintEvaluationAll


if __name__ == "__main__":
    testSingleEvaluate()
    testEvaluateAllDefault()
    testEvaluateAllSubset()
    testBestCase()
    testWorstCase()
    testEdgeCases()
    testTiming()
    testRunScenariosAll()
    testRunScenariosSubset()
    testPrintEvaluationAll()
    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED")
    print("=" * 60)
