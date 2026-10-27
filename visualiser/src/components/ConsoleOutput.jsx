import React from "react";

export function ConsoleOutput({ data, isLoading, error }) {
  // 1. Loading state view
  if (isLoading) {
    return (
      <div className="console-card loading-state">
        <div className="spinner"></div>
        <p>Constructing decision tree and analyzing permutations...</p>
      </div>
    );
  }

  // 2. Error state view
  if (error) {
    return (
      <div className="console-card error-state">
        <h3>Execution Failed</h3>
        <p>{error}</p>
      </div>
    );
  }

  // 3. Idle / Empty initial state view
  if (!data) {
    return (
      <div className="console-card empty-state">
        <p>Select an algorithm and input size above, then click <strong>Run & Build Tree</strong>.</p>
      </div>
    );
  }

  const { algorithm, n, stats = {}, print_output, tree } = data;

  return (
    <div className="console-card">
      {/* Metrics and statistics summary bar */}
      <div className="stats-header">
        <h2>{algorithm} (n={n})</h2>
        <div className="metrics-grid">
          <div className="metric-badge">
            <span className="metric-label">Permutations:</span>
            <span className="metric-value">{stats.permutations}</span>
          </div>
          <div className="metric-badge">
            <span className="metric-label">Leaves:</span>
            <span className="metric-value">{stats.leaves}</span>
          </div>
          <div className="metric-badge">
            <span className="metric-label">Total Nodes:</span>
            <span className="metric-value">{stats.total_nodes}</span>
          </div>
          <div className="metric-badge">
            <span className="metric-label">Max Depth:</span>
            <span className="metric-value">{stats.max_depth}</span>
          </div>
          <div className="metric-badge">
            <span className="metric-label">Avg Depth:</span>
            <span className="metric-value">{stats.avg_depth}</span>
          </div>
          <div className="metric-badge">
            <span className="metric-label">Leaves Valid:</span>
            <span className={`metric-value ${stats.all_valid ? "valid" : "invalid"}`}>
              {stats.all_valid ? "PASS" : "FAIL"}
            </span>
          </div>
        </div>
      </div>

      {/* Terminal ASCII tree printout section */}
      <div className="terminal-section">
        <div className="terminal-header">
          <span>Terminal Output (printTree)</span>
        </div>
        <pre className="terminal-pre">
          <code>{print_output || "(No print output available)"}</code>
        </pre>
      </div>

      {/* Placeholder container for future D3.js interactive SVG tree */}
      <div className="d3-placeholder-section">
        <div className="placeholder-content">
          <h4>D3.js Tree Visualization (Mount Point)</h4>
          <p>
            Structured hierarchy is loaded in memory ready for D3 SVG rendering.
          </p>
          {/* Placeholder: D3.js SVG tree rendering will mount here using tree data */}
          <div className="tree-data-preview">
            Root node: <code>{tree?.name || "None"}</code> | Child branches: <code>{tree?.children?.length || 0}</code>
          </div>
        </div>
      </div>
    </div>
  );
}
