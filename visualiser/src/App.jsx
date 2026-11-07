import React, { useState, useEffect } from "react";
import { AlgorithmForm } from "./components/AlgorithmForm.jsx";
import { ConsoleOutput } from "./components/ConsoleOutput.jsx";

// Fetch decision tree from live Python server, falling back to static precomputed JSON
async function fetchAlgorithmTree(algoId, n) {
  try {
    // Attempt live fetch from local Python server
    const liveResponse = await fetch(`http://127.0.0.1:5001/api/run?algo=${algoId}&n=${n}`);
    if (liveResponse.ok) {
      const liveData = await liveResponse.json();
      return { data: liveData, source: "Live Python Server" };
    }
  } catch (err) {
    // Live server not running, fall through to static precomputed dataset
  }

  // Fallback to static public JSON data
  const staticResponse = await fetch(`/data/${algoId}_n${n}.json`);
  if (!staticResponse.ok) {
    throw new Error(`Dataset for ${algoId} (n=${n}) not available`);
  }
  const staticData = await staticResponse.json();
  return { data: staticData, source: "Precomputed Dataset" };
}

export default function App() {
  const [treeResult, setTreeResult] = useState(null);
  const [dataSource, setDataSource] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Trigger tree construction or retrieval for the chosen parameters
  const handleRunAlgorithm = async (algoId, n) => {
    setIsLoading(true);
    setError(null);
    try {
      const { data, source } = await fetchAlgorithmTree(algoId, n);
      setTreeResult(data);
      setDataSource(source);
    } catch (err) {
      setError(err.message || "Failed to load decision tree data");
    } finally {
      setIsLoading(false);
    }
  };

  // Run bubbleSort (n=3) on initial mount so the dashboard displays baseline data
  useEffect(() => {
    handleRunAlgorithm("bubbleSort", 3);
  }, []);

  return (
    <div className="app-container">
      {/* App header and status indicators */}
      <header className="app-header">
        <div className="header-title">
          <h1>Decision Tree Visualiser</h1>
          <p>Sorting Decision Tree Workbench</p>
        </div>
        {dataSource && (
          <div className="source-badge">
            <span className="dot"></span>
            <span>Source: {dataSource}</span>
          </div>
        )}
      </header>

      {/* Main interactive workbench layout */}
      <main className="workbench-layout">
        <section className="controls-panel">
          <AlgorithmForm onRun={handleRunAlgorithm} isLoading={isLoading} />
        </section>

        <section className="display-panel">
          <ConsoleOutput data={treeResult} isLoading={isLoading} error={error} />
        </section>
      </main>
    </div>
  );
}
