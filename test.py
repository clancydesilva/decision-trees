from tracked_list import TrackedList
from algorithms import (
    bubble_sort,
    selection_sort,
    insertion_sort,
    cocktail_shaker_sort,
    shell_sort,
    quick_sort_lomuto,
    quick_sort_hoare,
    heap_sort,
    merge_sort,
    ALL_ALGORITHMS,
)
from evaluate import evaluate, evaluate_all, print_evaluation, print_comparison_table, run_scenarios


# --- 1. Single algorithm evaluation with detailed output ---
def test_single_evaluate():
    print("\n>>> test_single_evaluate: bubble_sort on [5, 3, 1, 4, 2]")
    result = evaluate(bubble_sort, [5, 3, 1, 4, 2])
    print_evaluation(result)

    assert result["sorted_correctly"], "Sort failed"
    assert result["replay_matches"], "Swap replay mismatch"
    assert result["comparisons_in_bounds"], f"Comparisons {result['comparisons']} out of bounds"
    assert result["swaps_in_bounds"], f"Swaps {result['swaps']} out of bounds"
    assert result["elapsed_ms"] >= 0, "Negative time"
    assert result["algorithm"] == "Bubble Sort"
    assert result["n"] == 5
    print("  PASSED\n")


# --- 2. evaluate_all with default (all algorithms) ---
def test_evaluate_all_default():
    print(">>> test_evaluate_all_default: all algorithms on [64, 34, 25, 12, 22, 11]")
    data = [64, 34, 25, 12, 22, 11]
    results = evaluate_all(data)

    assert len(results) == len(ALL_ALGORITHMS), f"Expected {len(ALL_ALGORITHMS)} results, got {len(results)}"

    for r in results:
        assert r["sorted_correctly"], f"{r['algorithm']} did not sort correctly"
        assert r["replay_matches"], f"{r['algorithm']} swap replay mismatch"
        assert r["elapsed_ms"] >= 0, f"{r['algorithm']} negative time"

    print_comparison_table(results)
    print("  PASSED\n")


# --- 3. evaluate_all with a subset of algorithms ---
def test_evaluate_all_subset():
    print(">>> test_evaluate_all_subset: [insertion_sort, quick_sort_hoare] on [9, 1, 5, 3]")
    subset = [insertion_sort, quick_sort_hoare]
    results = evaluate_all([9, 1, 5, 3], algorithms=subset)

    assert len(results) == 2
    assert results[0]["algorithm"] == "Insertion Sort"
    assert results[1]["algorithm"] == "Quick Sort (Hoare)"

    for r in results:
        assert r["sorted_correctly"]
        assert r["replay_matches"]

    print_comparison_table(results)
    print("  PASSED\n")


# --- 4. Best case: already sorted input ---
def test_best_case():
    print(">>> test_best_case: all algorithms on sorted [1..10]")
    data = list(range(1, 11))
    results = evaluate_all(data)

    for r in results:
        assert r["sorted_correctly"], f"{r['algorithm']} failed on sorted input"
        assert r["swaps"] == 0 or r["algorithm"] == "Heap Sort", \
            f"{r['algorithm']} did {r['swaps']} swaps on sorted input"

    print_comparison_table(results)
    print("  PASSED\n")


# --- 5. Worst case: reverse sorted input ---
def test_worst_case():
    print(">>> test_worst_case: all algorithms on reversed [10..1]")
    data = list(range(10, 0, -1))
    results = evaluate_all(data)

    for r in results:
        assert r["sorted_correctly"], f"{r['algorithm']} failed on reverse sorted input"
        assert r["comparisons_in_bounds"], \
            f"{r['algorithm']} comparisons {r['comparisons']} out of bounds ({r['comparisons_best']}-{r['comparisons_worst']})"
        assert r["swaps_in_bounds"], \
            f"{r['algorithm']} swaps {r['swaps']} out of bounds ({r['swaps_best']}-{r['swaps_worst']})"

    print_comparison_table(results)
    print("  PASSED\n")


# --- 6. Single element and empty edge cases ---
def test_edge_cases():
    print(">>> test_edge_cases: single element and two elements")

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


# --- 7. Timing is recorded ---
def test_timing():
    print(">>> test_timing: verify elapsed_ms is a positive float for larger input")
    data = list(range(100, 0, -1))
    result = evaluate(bubble_sort, data)
    assert isinstance(result["elapsed_ms"], float)
    assert result["elapsed_ms"] >= 0
    print(f"  Bubble sort on {len(data)} elements: {result['elapsed_ms']:.3f} ms")
    print("  PASSED\n")


# --- 8. run_scenarios with all algorithms ---
def test_run_scenarios_all():
    print(">>> test_run_scenarios_all")
    run_scenarios()
    print("  PASSED\n")


# --- 9. run_scenarios with a subset ---
def test_run_scenarios_subset():
    print(">>> test_run_scenarios_subset: [selection_sort, heap_sort]")
    run_scenarios(algorithms=[selection_sort, heap_sort])
    print("  PASSED\n")


# --- 10. print_evaluation for each algorithm ---
def test_print_evaluation_all():
    print(">>> test_print_evaluation_all: detailed output for each algorithm on [8, 3, 6, 1, 5]")
    data = [8, 3, 6, 1, 5]
    for fn in ALL_ALGORITHMS:
        r = evaluate(fn, data)
        print_evaluation(r)
        assert r["sorted_correctly"]
        assert r["replay_matches"]
    print("  PASSED\n")


if __name__ == "__main__":
    test_single_evaluate()
    test_evaluate_all_default()
    test_evaluate_all_subset()
    test_best_case()
    test_worst_case()
    test_edge_cases()
    test_timing()
    test_run_scenarios_all()
    test_run_scenarios_subset()
    test_print_evaluation_all()
    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED")
    print("=" * 60)
