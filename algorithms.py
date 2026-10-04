from typing import Optional
from math import log2, ceil
from tracked_list import TrackedList


def bubble_sort(arr: TrackedList) -> TrackedList:
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr.compare(j + 1, j):  # arr[j] > arr[j + 1]
                arr.swap(j, j + 1)      # swap out of order pair
                swapped = True
        if not swapped:
            break
    return arr


def selection_sort(arr: TrackedList) -> TrackedList:
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr.compare(j, min_idx):  # arr[j] < arr[min_idx]
                min_idx = j
        if min_idx != i:
            arr.swap(i, min_idx)  # move minimum to sorted position
    return arr


def insertion_sort(arr: TrackedList) -> TrackedList:
    n = len(arr)
    for i in range(1, n):
        j = i
        while j > 0 and arr.compare(j, j - 1):  # arr[j] < arr[j - 1]
            arr.swap(j, j - 1)                  # shift element left
            j -= 1
    return arr


def cocktail_shaker_sort(arr: TrackedList) -> TrackedList:
    start = 0
    end = len(arr) - 1
    swapped = True

    while swapped:
        swapped = False
        for i in range(start, end):
            if arr.compare(i + 1, i):  # arr[i] > arr[i + 1]
                arr.swap(i, i + 1)      # bubble larger right
                swapped = True

        if not swapped:
            break

        swapped = False
        end -= 1

        for i in range(end - 1, start - 1, -1):
            if arr.compare(i + 1, i):  # arr[i] > arr[i + 1]
                arr.swap(i, i + 1)      # bubble smaller left
                swapped = True
        start += 1

    return arr


def shell_sort(arr: TrackedList) -> TrackedList:
    n = len(arr)
    gap = n // 2

    while gap > 0:
        for i in range(gap, n):
            j = i
            while j >= gap and arr.compare(j, j - gap):  # arr[j] < arr[j - gap]
                arr.swap(j, j - gap)                     # swap across gap
                j -= gap
        gap //= 2

    return arr


def quick_sort_lomuto(arr: TrackedList, low: int = 0, high: Optional[int] = None) -> TrackedList:
    if high is None:
        high = len(arr) - 1

    if low < high:
        pi = _lomuto_partition(arr, low, high)
        quick_sort_lomuto(arr, low, pi - 1)
        quick_sort_lomuto(arr, pi + 1, high)

    return arr


def _lomuto_partition(arr: TrackedList, low: int, high: int) -> int:
    pivot_idx = high
    i = low - 1

    for j in range(low, high):
        if arr.compare(j, pivot_idx):  # arr[j] < arr[pivot]
            i += 1
            if i != j:
                arr.swap(i, j)  # swap smaller element into left boundary

    if i + 1 != high:
        arr.swap(i + 1, high)   # place pivot in final position
    return i + 1


def quick_sort_hoare(arr: TrackedList, low: int = 0, high: Optional[int] = None) -> TrackedList:
    if high is None:
        high = len(arr) - 1

    if low < high:
        pi = _hoare_partition(arr, low, high)
        quick_sort_hoare(arr, low, pi)
        quick_sort_hoare(arr, pi + 1, high)

    return arr


def _hoare_partition(arr: TrackedList, low: int, high: int) -> int:
    pivot_idx = low
    i = low - 1
    j = high + 1

    while True:
        i += 1
        while arr.compare(i, pivot_idx):  # arr[i] < arr[pivot] — scan right
            i += 1

        j -= 1
        while arr.compare(pivot_idx, j):  # arr[pivot] < arr[j] — scan left
            j -= 1

        if i >= j:
            return j

        arr.swap(i, j)  # swap elements on wrong sides of pivot
        # if we moved the pivot, update its tracked index
        if i == pivot_idx:
            pivot_idx = j
        elif j == pivot_idx:
            pivot_idx = i


def heap_sort(arr: TrackedList) -> TrackedList:
    n = len(arr)

    for i in range(n // 2 - 1, -1, -1):
        _heapify(arr, n, i)

    for i in range(n - 1, 0, -1):
        arr.swap(0, i)       # move max root to sorted end
        _heapify(arr, i, 0)

    return arr


def _heapify(arr: TrackedList, n: int, root: int) -> None:
    largest = root
    left = 2 * root + 1
    right = 2 * root + 2

    if left < n and arr.compare(largest, left):    # arr[left] > arr[largest]
        largest = left

    if right < n and arr.compare(largest, right):  # arr[right] > arr[largest]
        largest = right

    if largest != root:
        arr.swap(root, largest)                    # swap root with larger child
        _heapify(arr, n, largest)


def merge_sort(arr: TrackedList, left: int = 0, right: Optional[int] = None) -> TrackedList:
    if right is None:
        right = len(arr) - 1

    if left < right:
        mid = (left + right) // 2
        merge_sort(arr, left, mid)
        merge_sort(arr, mid + 1, right)
        _in_place_merge(arr, left, mid, right)

    return arr


def _in_place_merge(arr: TrackedList, start: int, mid: int, end: int) -> None:
    start2 = mid + 1

    if not arr.compare(start2, mid):  # already sorted across halves
        return

    while start <= mid and start2 <= end:
        if arr.compare(start, start2) or arr[start] == arr[start2]:  # arr[start] <= arr[start2]
            start += 1
        else:
            idx = start2
            while idx != start:
                arr.swap(idx, idx - 1)  # rotate smaller element into position
                idx -= 1
            start += 1
            mid += 1
            start2 += 1


# ---------------------------------------------------------------------------
# Algorithm metadata: complexity strings and theoretical bound formulas
# Each entry: bounds are lambda n -> int (exact or tight upper bound)
# ---------------------------------------------------------------------------

ALGORITHM_INFO = {
    bubble_sort: {
        "name": "Bubble Sort",
        "time_best": "O(n)",
        "time_avg": "O(n²)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: n - 1,                  # one pass, no swaps → early exit
        "comparisons_worst": lambda n: n * (n - 1) // 2,      # every pair compared
        "swaps_best": lambda n: 0,                             # already sorted
        "swaps_worst": lambda n: n * (n - 1) // 2,            # reverse sorted → swap every pair
    },
    selection_sort: {
        "name": "Selection Sort",
        "time_best": "O(n²)",
        "time_avg": "O(n²)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: n * (n - 1) // 2,       # always scans full unsorted suffix
        "comparisons_worst": lambda n: n * (n - 1) // 2,
        "swaps_best": lambda n: 0,                             # already sorted
        "swaps_worst": lambda n: n - 1,                        # one swap per position
    },
    insertion_sort: {
        "name": "Insertion Sort",
        "time_best": "O(n)",
        "time_avg": "O(n²)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: n - 1,                   # sorted → one compare per element
        "comparisons_worst": lambda n: n * (n - 1) // 2,      # reverse sorted
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 2,
    },
    cocktail_shaker_sort: {
        "name": "Cocktail Shaker Sort",
        "time_best": "O(n)",
        "time_avg": "O(n²)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: n - 1,
        "comparisons_worst": lambda n: n * (n - 1) // 2,
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 2,
    },
    shell_sort: {
        "name": "Shell Sort",
        "time_best": "O(n log n)",
        "time_avg": "O(n^1.25)",                               # depends on gap sequence
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: max(0, n - 1),                     # sorted → one compare per element per gap
        "comparisons_worst": lambda n: n * (n - 1) // 2,
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 2,
    },
    quick_sort_lomuto: {
        "name": "Quick Sort (Lomuto)",
        "time_best": "O(n log n)",
        "time_avg": "O(n log n)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: max(0, n - 1),                      # best partition splits
        "comparisons_worst": lambda n: n * (n - 1) // 2,       # already sorted → worst pivot
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 2,
    },
    quick_sort_hoare: {
        "name": "Quick Sort (Hoare)",
        "time_best": "O(n log n)",
        "time_avg": "O(n log n)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: max(0, n - 1),
        "comparisons_worst": lambda n: n * (n - 1),            # two-pointer scanning
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 4,             # fewer swaps than Lomuto
    },
    heap_sort: {
        "name": "Heap Sort",
        "time_best": "O(n log n)",
        "time_avg": "O(n log n)",
        "time_worst": "O(n log n)",
        "comparisons_best": lambda n: max(0, int(n * log2(max(n, 1)))),
        "comparisons_worst": lambda n: int(2 * n * log2(max(n, 1))),
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: int(n * log2(max(n, 1))),
    },
    merge_sort: {
        "name": "In-Place Merge Sort",
        "time_best": "O(n log n)",
        "time_avg": "O(n log²n)",                              # in-place merge adds overhead
        "time_worst": "O(n²log n)",
        "comparisons_best": lambda n: max(0, n - 1),               # sorted -> one compare per merge, early exit
        "comparisons_worst": lambda n: int(n * n * log2(max(n, 1))),
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 2,
    },
}

ALL_ALGORITHMS = [
    bubble_sort,
    selection_sort,
    insertion_sort,
    cocktail_shaker_sort,
    shell_sort,
    quick_sort_lomuto,
    quick_sort_hoare,
    heap_sort,
    merge_sort,
]
