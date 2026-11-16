import React, { useState, useEffect, useRef } from "react";
import { AlgorithmForm } from "./components/AlgorithmForm.jsx";
import { TreeViewer } from "./components/TreeViewer.jsx";

// Fetch decision tree from live Python server, falling back to static precomputed JSON
async function fetchAlgorithmTree(algoId, n, signal) {
  const numericN = Number(n);
  if (!Number.isInteger(numericN) || numericN < 1 || numericN > 6) {
    throw new Error(`Input size n=${n} is rejected. Full decision trees are hard-capped at n=6.`);
  }

  try {
    // 1. Attempt live fetch via relative API path (proxied in dev or served directly in production)
    const liveResponse = await fetch(`/api/run?algo=${algoId}&n=${n}`, { signal });
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
  } catch (err) {
    if (err.name === "AbortError") {
      throw err;
    }
    // If the server explicitly responded with an application error, propagate it
    if (err.message && !err.message.includes("Failed to fetch") && !err.message.includes("NetworkError")) {
      throw err;
    }
  }

  // 2. Fallback to static public JSON data
  const staticResponse = await fetch(`/data/${algoId}_n${n}.json`, { signal });
  const contentType = staticResponse.headers.get("content-type") || "";

  // Verify response is genuine JSON and not Vite's HTML 404 fallback page
  if (!staticResponse.ok || !contentType.includes("application/json")) {
    throw new Error(
      `Dataset for ${algoId} (n=${n}) is not precomputed. Start the live Python API server to generate dynamic trees on-demand: python export_runner.py --serve`
    );
  }

  const staticData = await staticResponse.json();
  return { data: staticData, source: "Precomputed Dataset" };
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
          <TreeViewer treeData={treeResult?.tree} maxDepth={stats.max_depth} />
        )}
      </main>
    </div>
  );
}
