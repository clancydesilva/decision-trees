from typing import Optional
from math import log2, ceil
from tracked_list import TrackedList


def bubbleSort(arr: TrackedList) -> TrackedList:
    # Repeatedly step through the list, compare adjacent elements and swap them if out of order
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr.compare(j + 1, j):  # arr[j] > arr[j + 1]
                arr.swap(j, j + 1)      # swap out of order pair
                swapped = True
        if not swapped:
            # Early exit if no swaps occurred during the pass
            break
    return arr


def selectionSort(arr: TrackedList) -> TrackedList:
    # Find the minimum element in the unsorted suffix and place it at the beginning
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr.compare(j, min_idx):  # arr[j] < arr[min_idx]
                min_idx = j
        if min_idx != i:
            arr.swap(i, min_idx)  # move minimum to its sorted position
    return arr


def insertionSort(arr: TrackedList) -> TrackedList:
    # Insert each element into its correct position within the already sorted prefix
    n = len(arr)
    for i in range(1, n):
        j = i
        while j > 0 and arr.compare(j, j - 1):  # arr[j] < arr[j - 1]
            arr.swap(j, j - 1)                  # shift element left into sorted position
            j -= 1
    return arr


def cocktailShakerSort(arr: TrackedList) -> TrackedList:
    # Bidirectional bubble sort passing alternately left-to-right and right-to-left
    start = 0
    end = len(arr) - 1
    swapped = True

    while swapped:
        swapped = False
        # Forward pass: bubble larger elements to the right
        for i in range(start, end):
            if arr.compare(i + 1, i):  # arr[i] > arr[i + 1]
                arr.swap(i, i + 1)      # bubble larger right
                swapped = True

        if not swapped:
            break

        swapped = False
        end -= 1

        # Backward pass: bubble smaller elements to the left
        for i in range(end - 1, start - 1, -1):
            if arr.compare(i + 1, i):  # arr[i] > arr[i + 1]
                arr.swap(i, i + 1)      # bubble smaller left
                swapped = True
        start += 1

    return arr


def shellSort(arr: TrackedList) -> TrackedList:
    # Generalisation of insertion sort allowing exchanges of far-apart elements using decreasing gaps
    n = len(arr)
    gap = n // 2

    while gap > 0:
        # Perform gap-spaced insertion sort
        for i in range(gap, n):
            j = i
            while j >= gap and arr.compare(j, j - gap):  # arr[j] < arr[j - gap]
                arr.swap(j, j - gap)                     # swap across gap
                j -= gap
        gap //= 2

    return arr


def quickSortLomuto(arr: TrackedList, low: int = 0, high: Optional[int] = None) -> TrackedList:
    # Quicksort with Lomuto partition scheme using the rightmost element as pivot
    if high is None:
        high = len(arr) - 1

    if low < high:
        pi = _lomutoPartition(arr, low, high)
        quickSortLomuto(arr, low, pi - 1)
        quickSortLomuto(arr, pi + 1, high)

    return arr


def _lomutoPartition(arr: TrackedList, low: int, high: int) -> int:
    # Partition array around pivot at high index
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


def quickSortHoare(arr: TrackedList, low: int = 0, high: Optional[int] = None) -> TrackedList:
    # Quicksort with Hoare two-pointer partition scheme
    if high is None:
        high = len(arr) - 1

    if low < high:
        pi = _hoarePartition(arr, low, high)
        quickSortHoare(arr, low, pi)
        quickSortHoare(arr, pi + 1, high)

    return arr


def _hoarePartition(arr: TrackedList, low: int, high: int) -> int:
    # Two-pointer partition moving inward until out-of-order elements are found and swapped
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
        # if the pivot element was moved, update its tracked index
        if i == pivot_idx:
            pivot_idx = j
        elif j == pivot_idx:
            pivot_idx = i


def heapSort(arr: TrackedList) -> TrackedList:
    # Build a max-heap and repeatedly extract the maximum root to the sorted suffix
    n = len(arr)

    # Build max heap from bottom up
    for i in range(n // 2 - 1, -1, -1):
        _heapify(arr, n, i)

    # Extract elements one by one from heap
    for i in range(n - 1, 0, -1):
        arr.swap(0, i)       # move max root to sorted end
        _heapify(arr, i, 0)

    return arr


def _heapify(arr: TrackedList, n: int, root: int) -> None:
    # Maintain max-heap property for subtree rooted at root index
    largest = root
    left = 2 * root + 1
    right = 2 * root + 2

    # Compare root with left child
    if left < n and arr.compare(largest, left):    # arr[left] > arr[largest]
        largest = left

    # Compare largest so far with right child
    if right < n and arr.compare(largest, right):  # arr[right] > arr[largest]
        largest = right

    # Swap and continue heapifying if root is not largest
    if largest != root:
        arr.swap(root, largest)                    # swap root with larger child
        _heapify(arr, n, largest)


def mergeSort(arr: TrackedList, left: int = 0, right: Optional[int] = None) -> TrackedList:
    # Recursive in-place merge sort dividing array into halves and merging in-place
    if right is None:
        right = len(arr) - 1

    if left < right:
        mid = (left + right) // 2
        mergeSort(arr, left, mid)
        mergeSort(arr, mid + 1, right)
        _inPlaceMerge(arr, left, mid, right)

    return arr


def _inPlaceMerge(arr: TrackedList, start: int, mid: int, end: int) -> None:
    # Merge two sorted adjacent sublists in-place without raw equality comparisons
    start2 = mid + 1

    # Check if already sorted across the boundary
    if not arr.compare(start2, mid):
        return

    while start <= mid and start2 <= end:
        if arr.compare(start, start2):  # element at start is already in correct relative position
            start += 1
        else:
            # Rotate element at start2 into current position at start
            idx = start2
            while idx != start:
                arr.swap(idx, idx - 1)
                idx -= 1
            start += 1
            mid += 1
            start2 += 1


# Algorithm metadata: complexity strings and theoretical bound formulas
# Each entry: bounds are lambda n -> int (exact or tight upper bound)

ALGORITHM_INFO = {
    bubbleSort: {
        "name": "Bubble Sort",
        "time_best": "O(n)",
        "time_avg": "O(n²)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: n - 1,                  # one pass, no swaps -> early exit
        "comparisons_worst": lambda n: n * (n - 1) // 2,      # every pair compared
        "swaps_best": lambda n: 0,                             # already sorted
        "swaps_worst": lambda n: n * (n - 1) // 2,            # reverse sorted -> swap every pair
    },
    selectionSort: {
        "name": "Selection Sort",
        "time_best": "O(n²)",
        "time_avg": "O(n²)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: n * (n - 1) // 2,       # always scans full unsorted suffix
        "comparisons_worst": lambda n: n * (n - 1) // 2,
        "swaps_best": lambda n: 0,                             # already sorted
        "swaps_worst": lambda n: n - 1,                        # one swap per position
    },
    insertionSort: {
        "name": "Insertion Sort",
        "time_best": "O(n)",
        "time_avg": "O(n²)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: n - 1,                   # sorted -> one compare per element
        "comparisons_worst": lambda n: n * (n - 1) // 2,      # reverse sorted
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 2,
    },
    cocktailShakerSort: {
        "name": "Cocktail Shaker Sort",
        "time_best": "O(n)",
        "time_avg": "O(n²)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: n - 1,
        "comparisons_worst": lambda n: n * (n - 1) // 2,
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 2,
    },
    shellSort: {
        "name": "Shell Sort",
        "time_best": "O(n log n)",
        "time_avg": "O(n^1.25)",                               # depends on gap sequence
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: max(0, n - 1),                     # sorted -> one compare per element per gap
        "comparisons_worst": lambda n: n * (n - 1) // 2,
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 2,
    },
    quickSortLomuto: {
        "name": "Quick Sort (Lomuto)",
        "time_best": "O(n log n)",
        "time_avg": "O(n log n)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: max(0, n - 1),                      # best partition splits
        "comparisons_worst": lambda n: n * (n - 1) // 2,       # already sorted -> worst pivot
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 2,
    },
    quickSortHoare: {
        "name": "Quick Sort (Hoare)",
        "time_best": "O(n log n)",
        "time_avg": "O(n log n)",
        "time_worst": "O(n²)",
        "comparisons_best": lambda n: max(0, n - 1),
        "comparisons_worst": lambda n: n * (n - 1),            # two-pointer scanning
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: n * (n - 1) // 4,             # fewer swaps than Lomuto
    },
    heapSort: {
        "name": "Heap Sort",
        "time_best": "O(n log n)",
        "time_avg": "O(n log n)",
        "time_worst": "O(n log n)",
        "comparisons_best": lambda n: max(0, int(n * log2(max(n, 1)))),
        "comparisons_worst": lambda n: int(2 * n * log2(max(n, 1))),
        "swaps_best": lambda n: 0,
        "swaps_worst": lambda n: int(n * log2(max(n, 1))),
    },
    mergeSort: {
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
    bubbleSort,
    selectionSort,
    insertionSort,
    cocktailShakerSort,
    shellSort,
    quickSortLomuto,
    quickSortHoare,
    heapSort,
    mergeSort,
]

# Backward compatibility aliases
bubble_sort = bubbleSort
selection_sort = selectionSort
insertion_sort = insertionSort
cocktail_shaker_sort = cocktailShakerSort
shell_sort = shellSort
quick_sort_lomuto = quickSortLomuto
_lomuto_partition = _lomutoPartition
quick_sort_hoare = quickSortHoare
_hoare_partition = _hoarePartition
heap_sort = heapSort
merge_sort = mergeSort
_in_place_merge = _inPlaceMerge

# Register backward compatible aliases in ALGORITHM_INFO
for _new_fn, _old_fn in [
    (bubbleSort, bubble_sort),
    (selectionSort, selection_sort),
    (insertionSort, insertion_sort),
    (cocktailShakerSort, cocktail_shaker_sort),
    (shellSort, shell_sort),
    (quickSortLomuto, quick_sort_lomuto),
    (quickSortHoare, quick_sort_hoare),
    (heapSort, heap_sort),
    (mergeSort, merge_sort),
]:
    ALGORITHM_INFO[_old_fn] = ALGORITHM_INFO[_new_fn]
