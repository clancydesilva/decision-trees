from time import perf_counter
from tracked_list import TrackedList
from algorithms import ALGORITHM_INFO, ALL_ALGORITHMS


def evaluate(sort_fn, data):
    # Run a sorting algorithm on data and return metrics including bounds and verification
    info = ALGORITHM_INFO[sort_fn]
    n = len(data)
    tracker = TrackedList(data)

    # Measure execution time
    t0 = perf_counter()
    sort_fn(tracker)
    elapsed_ms = (perf_counter() - t0) * 1000

    # Verify if array sorted correctly
    sorted_correctly = tracker.array == sorted(data)

    # Replay recorded swaps on untouched original list to verify correctness
    replayed = list(tracker.original)
    for i, j in tracker.swaps:
        replayed[i], replayed[j] = replayed[j], replayed[i]
    replay_matches = replayed == tracker.array

    # Calculate theoretical comparison and swap bounds for input size n
    cmp_best = info["comparisons_best"](n)
    cmp_worst = info["comparisons_worst"](n)
    swap_best = info["swaps_best"](n)
    swap_worst = info["swaps_worst"](n)

    return {
        "algorithm": info["name"],
        "time_best": info["time_best"],
        "time_avg": info["time_avg"],
        "time_worst": info["time_worst"],
        "n": n,
        "elapsed_ms": elapsed_ms,
        "comparisons": tracker.comparisonCount,
        "comparisons_best": cmp_best,
        "comparisons_worst": cmp_worst,
        "comparisons_in_bounds": cmp_best <= tracker.comparisonCount <= cmp_worst,
        "swaps": tracker.swapCount,
        "swaps_best": swap_best,
        "swaps_worst": swap_worst,
        "swaps_in_bounds": swap_best <= tracker.swapCount <= swap_worst,
        "sorted_correctly": sorted_correctly,
        "replay_matches": replay_matches,
        "original": tracker.original,
        "result": tracker.array,
        "comparison_log": tracker.comparisons,
        "swap_log": tracker.swaps,
    }


def evaluateAll(data, algorithms=None):
    # Run all (or selected) algorithms on identical input data and return result dicts
    if algorithms is None:
        algorithms = ALL_ALGORITHMS
    return [evaluate(fn, data) for fn in algorithms]


def printEvaluation(result):
    # Pretty-print a single algorithm evaluation result
    r = result
    print(f"\n{'=' * 60}")
    print(f"  {r['algorithm']}")
    print(f"  Complexity: Best {r['time_best']} | Avg {r['time_avg']} | Worst {r['time_worst']}")
    print(f"{'=' * 60}")
    print(f"  Input (n={r['n']}): {r['original']}")
    print(f"  Output:      {r['result']}")
    print(f"  Sorted correctly: {r['sorted_correctly']}")
    print(f"  Replay matches:   {r['replay_matches']}")
    print(f"  Time: {r['elapsed_ms']:.3f} ms")
    print(f"{'-' * 60}")
    print(f"  Comparisons: {r['comparisons']:>6}   (bounds: {r['comparisons_best']} - {r['comparisons_worst']})")
    in_cmp = "YES" if r["comparisons_in_bounds"] else "NO - OUT OF BOUNDS"
    print(f"  Within bounds: {in_cmp}")
    print(f"  Swaps:       {r['swaps']:>6}   (bounds: {r['swaps_best']} - {r['swaps_worst']})")
    in_swp = "YES" if r["swaps_in_bounds"] else "NO - OUT OF BOUNDS"
    print(f"  Within bounds: {in_swp}")
    print(f"{'=' * 60}")


def printTrace(sort_fn, data):
    # Print an interleaved step-by-step trace of comparisons and swaps
    info = ALGORITHM_INFO[sort_fn]
    tracker = TrackedList(list(data))
    sort_fn(tracker)

    print(f"\n{'=' * 60}")
    print(f"  {info['name']} - Step-by-step trace")
    print(f"{'=' * 60}")
    print(f"  Start: {list(data)}\n")

    arr = list(data)  # replay from original
    step = 0
    for event in tracker.events:
        step += 1
        if event[0] == 'cmp':
            _, i, j, result = event
            op = "<" if result else ">="
            print(f"  {step}. Compare a[{i}] vs a[{j}]: {arr[i]} {op} {arr[j]}")
        elif event[0] == 'swap':
            _, i, j = event
            print(f"  {step}. Swap    a[{i}] <> a[{j}]: {arr[i]} <> {arr[j]}")
            arr[i], arr[j] = arr[j], arr[i]
            print(f"     -> {arr}")

    print(f"\n  Result: {arr}")
    print(f"{'=' * 60}")


def printComparisonTable(results):
    # Print a formatted table comparing performance across multiple algorithms
    print(f"\n{'Algorithm':<24} | {'Cmp':<6} | {'Cmp Range':<16} | {'Swp':<6} | {'Swp Range':<16} | {'Time (ms)':<10} | {'Complexity':<12} | {'OK'}")
    print("-" * 125)
    for r in results:
        cmp_range = f"{r['comparisons_best']}-{r['comparisons_worst']}"
        swp_range = f"{r['swaps_best']}-{r['swaps_worst']}"
        ok = "PASS" if (r["comparisons_in_bounds"] and r["swaps_in_bounds"] and r["sorted_correctly"]) else "FAIL"
        print(
            f"{r['algorithm']:<24} | {r['comparisons']:<6} | {cmp_range:<16} | {r['swaps']:<6} | {swp_range:<16} | {r['elapsed_ms']:<10.3f} | {r['time_avg']:<12} | {ok}"
        )


def runScenarios(algorithms=None):
    # Run algorithms against sorted, reversed, and pseudo-random inputs
    if algorithms is None:
        algorithms = ALL_ALGORITHMS

    n = 12
    scenarios = {
        "Already Sorted (Best)": list(range(1, n + 1)),
        "Reverse Sorted (Worst)": list(range(n, 0, -1)),
        "Random-ish": [64, 34, 25, 12, 22, 11, 90, 88, 45, 50, 15, 3],
    }

    for label, data in scenarios.items():
        print(f"\n{'#' * 60}")
        print(f"  Scenario: {label}")
        print(f"  Input: {data}")
        print(f"{'#' * 60}")
        results = evaluateAll(data, algorithms)
        printComparisonTable(results)


# Backward compatibility aliases
evaluate_all = evaluateAll
print_evaluation = printEvaluation
print_trace = printTrace
print_comparison_table = printComparisonTable
run_scenarios = runScenarios


if __name__ == "__main__":
    from algorithms import insertionSort, bubbleSort

    runScenarios()
    printTrace(insertionSort, [3, 2, 1])
    printTrace(bubbleSort, [5, 3, 1, 4, 2])
