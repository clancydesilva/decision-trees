import React, { useState, useEffect, useRef } from "react";
import { AlgorithmForm } from "./components/AlgorithmForm.jsx";
import { TreeViewer } from "./components/TreeViewer.jsx";

// Fetch decision tree from precomputed static JSON first, falling back to live Python API
async function fetchAlgorithmTree(algoId, n, signal) {
  const numericN = Number(n);
  if (!Number.isInteger(numericN) || numericN < 1 || numericN > 7) {
    throw new Error(`Input size n=${n} is rejected. Full decision trees are hard-capped at n=7.`);
  }

  // 1. Attempt fast static lookup from precomputed dataset (/data/{algo}_n{n}.json)
  try {
    const staticResponse = await fetch(`/data/${algoId}_n${numericN}.json`, { signal });
    const staticContentType = staticResponse.headers.get("content-type") || "";
    if (staticResponse.ok && staticContentType.includes("application/json")) {
      const staticData = await staticResponse.json();
      return { data: staticData, source: "Precomputed Dataset" };
    }
  } catch (err) {
    if (err.name === "AbortError") {
      throw err;
    }
  }

  // 2. Fallback to live Python API server if static file is missing
  const liveResponse = await fetch(`/api/run?algo=${algoId}&n=${numericN}`, { signal });
  const liveContentType = liveResponse.headers.get("content-type") || "";
  if (liveResponse.ok && liveContentType.includes("application/json")) {
    const liveData = await liveResponse.json();
    return { data: liveData, source: "Live Python Server" };
  } else if (liveContentType.includes("application/json")) {
    const errJson = await liveResponse.json().catch(() => null);
    if (errJson?.error) {
      throw new Error(errJson.error);
    }
  }

  throw new Error(
    `Dataset for ${algoId} (n=${numericN}) was not found statically and the live Python API server is unreachable.`
  );
}

export default function App() {
  const [treeResult, setTreeResult] = useState(null);
  const [dataSource, setDataSource] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  // Trigger tree construction or retrieval for the chosen parameters
  const handleRunAlgorithm = async (algoId, n) => {
    // Cancel any in-flight request before starting a new one
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsLoading(true);
    setError(null);
    try {
      const { data, source } = await fetchAlgorithmTree(algoId, n, controller.signal);
      setTreeResult(data);
      setDataSource(source);
    } catch (err) {
      if (err.name === "AbortError") return;
      setError(err.message || "Failed to load decision tree data");
    } finally {
      if (abortControllerRef.current === controller) {
        setIsLoading(false);
      }
    }
  };

  // Run bubbleSort (n=3) on initial mount so the dashboard displays baseline data
  useEffect(() => {
    handleRunAlgorithm("bubbleSort", 3);
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const stats = treeResult?.stats || {};

  return (
    <div className="workbench-app">
      {/* Top dashboard bar (~20% screen height) containing branding, controls, and stats */}
      <header className="top-dashboard-bar">
        <div className="top-bar-primary">
          <div className="brand-group">
            <h1>Decision Tree Visualiser</h1>
            {dataSource && (
              <span className="source-pill">
                <span className="dot" />
                {dataSource}
              </span>
            )}
          </div>
          <AlgorithmForm onRun={handleRunAlgorithm} isLoading={isLoading} />
        </div>

        {/* Real-time tree complexity and leaf verification metrics */}
        {treeResult && (
          <div className="top-bar-stats">
            <div className="stat-pill">
              <span className="stat-label">Algorithm</span>
              <span className="stat-value">{treeResult.algorithm} (n={treeResult.n})</span>
            </div>
            <div className="stat-pill">
              <span className="stat-label">Permutations</span>
              <span className="stat-value">{stats.permutations ?? "—"}</span>
            </div>
            <div className="stat-pill">
              <span className="stat-label">Leaves</span>
              <span className="stat-value">{stats.leaves ?? "—"}</span>
            </div>
            <div className="stat-pill">
              <span className="stat-label">Total Nodes</span>
              <span className="stat-value">{stats.total_nodes ?? "—"}</span>
            </div>
            <div className="stat-pill">
              <span className="stat-label">Depth (Max/Avg)</span>
              <span className="stat-value">
                {stats.max_depth ?? "—"} / {stats.avg_depth ?? "—"}
              </span>
            </div>
            <div className="stat-pill">
              <span className="stat-label">Verification</span>
              <span className={`stat-value ${stats.all_valid ? "status-pass" : "status-fail"}`}>
                {stats.all_valid ? "ALL VALID" : "INVALID"}
              </span>
            </div>
          </div>
        )}
      </header>

      {/* Main full-bleed tree visualizer viewport (~80% screen height) */}
      <main className="main-visualiser-canvas">
        {isLoading ? (
          <div className="canvas-state-overlay">
            <div className="spinner" />
            <p>Constructing decision tree and analyzing permutations...</p>
          </div>
        ) : error ? (
          <div className="canvas-state-overlay error">
            <h3>Execution Failed</h3>
            <p>{error}</p>
          </div>
        ) : (
          <TreeViewer
            treeData={treeResult?.tree}
            maxDepth={stats.max_depth}
            n={treeResult?.n}
            totalNodes={stats.total_nodes}
          />
        )}
      </main>
    </div>
  );
}
