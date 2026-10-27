import React, { useState } from "react";

// Default catalog of all supported sorting algorithms
const DEFAULT_ALGORITHMS = [
  { id: "bubbleSort", name: "Bubble Sort" },
  { id: "selectionSort", name: "Selection Sort" },
  { id: "insertionSort", name: "Insertion Sort" },
  { id: "cocktailShakerSort", name: "Cocktail Shaker Sort" },
  { id: "shellSort", name: "Shell Sort" },
  { id: "quickSortLomuto", name: "Quick Sort (Lomuto)" },
  { id: "quickSortHoare", name: "Quick Sort (Hoare)" },
  { id: "heapSort", name: "Heap Sort" },
  { id: "mergeSort", name: "In-Place Merge Sort" },
];

export function AlgorithmForm({ onRun, isLoading, algorithms = DEFAULT_ALGORITHMS }) {
  const [selectedAlgo, setSelectedAlgo] = useState("bubbleSort");
  const [selectedN, setSelectedN] = useState(3);
  const [warningMessage, setWarningMessage] = useState("");

  // Update selected algorithm ID from dropdown
  const handleAlgoChange = (e) => {
    setSelectedAlgo(e.target.value);
  };

  // Update input size n and display warning for large trees (n >= 5)
  const handleNChange = (n) => {
    setSelectedN(n);
    if (n >= 5) {
      setWarningMessage("n=5 has 120 permutations. Large tree rendering ceiling.");
    } else {
      setWarningMessage("");
    }
  };

  // Validate and submit parameter choices to parent runner
  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLoading) return;
    onRun(selectedAlgo, selectedN);
  };

  return (
    <form className="algorithm-form" onSubmit={handleSubmit}>
      {/* Algorithm selector dropdown */}
      <div className="form-group">
        <label htmlFor="algo-select">Algorithm</label>
        <select
          id="algo-select"
          value={selectedAlgo}
          onChange={handleAlgoChange}
          disabled={isLoading}
        >
          {algorithms.map((algo) => (
            <option key={algo.id} value={algo.id}>
              {algo.name}
            </option>
          ))}
        </select>
      </div>

      {/* Input size n selector */}
      <div className="form-group">
        <label>Input Size (n)</label>
        <div className="button-group">
          {[3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              className={`pill-btn ${selectedN === n ? "active" : ""}`}
              onClick={() => handleNChange(n)}
              disabled={isLoading}
            >
              n = {n}
            </button>
          ))}
        </div>
      </div>

      {/* Size warning notification if n >= 5 */}
      {warningMessage && (
        <div className="warning-banner">{warningMessage}</div>
      )}

      {/* Execute button */}
      <button
        type="submit"
        className="submit-btn"
        disabled={isLoading}
      >
        {isLoading ? "Running Tree..." : "Run & Build Tree"}
      </button>
    </form>
  );
}
