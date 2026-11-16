import React, { useRef, useEffect, useState, useMemo, useCallback } from "react";
import * as d3 from "d3";
import { computeTidyTreeLayout } from "../utils/tidyLayout.js";

// Generate smooth vertical cubic Bezier paths connecting parent bottom to child top
function generateLinkPath(link, nodeHeight = 70) {
  const sourceX = link.source.x;
  const sourceY = link.source.y + nodeHeight / 2;
  const targetX = link.target.x;
  const targetY = link.target.y - nodeHeight / 2;

  // Calculate vertical midpoint for smooth S-curve control points
  const midY = (sourceY + targetY) / 2;
  return `M ${sourceX} ${sourceY} C ${sourceX} ${midY}, ${targetX} ${midY}, ${targetX} ${targetY}`;
}

// Compute max depth of tree if not provided via props
function getTreeMaxDepth(node, currentDepth = 0) {
  if (!node || !node.children || node.children.length === 0) return currentDepth;
  return Math.max(...node.children.map((child) => getTreeMaxDepth(child, currentDepth + 1)));
}

// Collect deterministic node IDs at targetDepth to initialize default folding
function findCollapsedAtDepth(node, targetDepth = 3, currentDepth = 0, path = "root", collected = new Set()) {
  if (!node || !node.children || node.children.length === 0) return collected;

  // Reach target depth: mark this internal node to be collapsed
  if (currentDepth === targetDepth) {
    collected.add(path);
    return collected;
  }

  // Follow child branches preserving binary path mapping
  let yesChild = null;
  let noChild = null;
  let yesSuffix = "/Y";
  let noSuffix = "/N";

  node.children.forEach((child) => {
    const branch = child.attributes?.branch;
    if (branch === "Yes") {
      yesChild = child;
      yesSuffix = "/Y";
    } else if (branch === "No") {
      noChild = child;
      noSuffix = "/N";
    } else {
      if (!yesChild) {
        yesChild = child;
        yesSuffix = "/L";
      } else {
        noChild = child;
        noSuffix = "/R";
      }
    }
  });

  if (yesChild) {
    findCollapsedAtDepth(yesChild, targetDepth, currentDepth + 1, `${path}${yesSuffix}`, collected);
  }
  if (noChild) {
    findCollapsedAtDepth(noChild, targetDepth, currentDepth + 1, `${path}${noSuffix}`, collected);
  }

  return collected;
}

export function TreeViewer({ treeData, maxDepth: propMaxDepth, n, totalNodes }) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const viewportRef = useRef(null);
  const zoomBehaviorRef = useRef(null);
  const boundsRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [collapsedIds, setCollapsedIds] = useState(new Set());
  const isExpandAllDisabled = (n && n >= 7) || (totalNodes && totalNodes > 3000);

  // Determine whether initial folding is required (when tree max depth > 4)
  useEffect(() => {
    if (!treeData) {
      setCollapsedIds(new Set());
      return;
    }

    const calculatedMaxDepth = propMaxDepth ?? getTreeMaxDepth(treeData);

    // If max depth > 4, default to collapsing comparison nodes at the 4th level (depth 3)
    if (calculatedMaxDepth > 4) {
      const defaultCollapsed = findCollapsedAtDepth(treeData, 3);
      setCollapsedIds(defaultCollapsed);
    } else {
      setCollapsedIds(new Set());
    }
  }, [treeData, propMaxDepth]);

  // Compute Reingold-Tilford layout using the adapter with collapsed branches pruned
  const { nodes, links, bounds } = useMemo(() => {
    const layout = computeTidyTreeLayout(treeData, {
      nodeWidth: 150,
      nodeHeight: 70,
      levelDistance: 100,
      siblingGap: 24,
      collapsedIds,
    });
    boundsRef.current = layout.bounds;
    return layout;
  }, [treeData, collapsedIds]);

  // Center and fit the tree within the visible SVG viewport with generous bottom margin
  const fitToScreen = useCallback(() => {
    if (!svgRef.current || !containerRef.current || !zoomBehaviorRef.current) return;
    const currentBounds = boundsRef.current;
    if (!currentBounds || currentBounds.width === 0) return;

    const width = containerRef.current.clientWidth || 800;
    const height = containerRef.current.clientHeight || 600;

    // Raised bottom margin by 18% of viewport height to ensure leaf nodes and badges are never cut off
    const horizontalPadding = 80;
    const topPadding = 45;
    const bottomPadding = Math.max(110, height * 0.18);

    const availableWidth = Math.max(width - horizontalPadding, 100);
    const availableHeight = Math.max(height - topPadding - bottomPadding, 100);

    // Include space for card half-height (35px) and collapsed leaf indicator badge (25px)
    const treeW = Math.max(currentBounds.width, 100);
    const treeH = Math.max(currentBounds.height + 40, 100);

    const scale = Math.min(1.2, Math.max(0.12, Math.min(availableWidth / treeW, availableHeight / treeH)));

    // Center root and tree mass horizontally
    const centerX = width / 2 - ((currentBounds.minX + currentBounds.maxX) / 2) * scale;
    // Align tree from top with topPadding, guaranteeing bottom clearance
    const centerY = topPadding - (currentBounds.minY - 35) * scale;

    const transform = d3.zoomIdentity.translate(centerX, centerY).scale(scale);
    d3.select(svgRef.current)
      .transition()
      .duration(350)
      .call(zoomBehaviorRef.current.transform, transform);
  }, []);

  // Initialize D3 pan & zoom behavior once on mount
  useEffect(() => {
    if (!svgRef.current || !viewportRef.current) return;

    const zoomBehavior = d3.zoom()
      .scaleExtent([0.1, 2.5])
      .on("zoom", (event) => {
        d3.select(viewportRef.current).attr("transform", event.transform);
      });

    zoomBehaviorRef.current = zoomBehavior;
    d3.select(svgRef.current).call(zoomBehavior);
  }, []);

  // Re-fit viewport only when a new algorithm or input size dataset is loaded
  useEffect(() => {
    if (!treeData) return;
    const timer = setTimeout(() => {
      fitToScreen();
    }, 50);
    return () => clearTimeout(timer);
  }, [treeData, fitToScreen]);

  // Toggle subtree folding: expanding a node reveals only the immediate next level
  const handleToggleCollapse = (nodeId, nodeData) => {
    setCollapsedIds((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        // Expanding node: remove this node from collapsed
        next.delete(nodeId);

        // Collapse immediate comparison children so expansion advances only one level
        if (nodeData?.rawChildren) {
          let fallbackLeftAssigned = false;
          nodeData.rawChildren.forEach((child) => {
            if (child.children && child.children.length > 0) {
              const branch = child.attributes?.branch;
              let childSuffix = "/R";
              if (branch === "Yes") {
                childSuffix = "/Y";
              } else if (branch === "No") {
                childSuffix = "/N";
              } else if (!fallbackLeftAssigned) {
                childSuffix = "/L";
                fallbackLeftAssigned = true;
              }
              next.add(`${nodeId}${childSuffix}`);
            } else if (!child.attributes?.branch && !fallbackLeftAssigned) {
              fallbackLeftAssigned = true;
            }
          });
        }
      } else {
        // Collapsing node: fold this node and prune any deeper tracked IDs under it
        next.add(nodeId);
        for (const id of next) {
          if (id !== nodeId && id.startsWith(`${nodeId}/`)) {
            next.delete(id);
          }
        }
      }
      return next;
    });
  };

  // Collapse all branches back to the 4th level (depth 3)
  const handleCollapseAll = () => {
    if (!treeData) return;
    const defaultCollapsed = findCollapsedAtDepth(treeData, 3);
    setCollapsedIds(defaultCollapsed);
    setTimeout(fitToScreen, 50);
  };

  // Expand all branches across the entire decision tree (disabled when n >= 7 or > 3,000 nodes)
  const handleExpandAll = () => {
    if (isExpandAllDisabled) return;
    setCollapsedIds(new Set());
    setTimeout(fitToScreen, 50);
  };

  // Programmatic zoom control handlers
  const handleZoomIn = () => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    d3.select(svgRef.current).transition().duration(250).call(zoomBehaviorRef.current.scaleBy, 1.3);
  };

  const handleZoomOut = () => {
    if (!svgRef.current || !zoomBehaviorRef.current) return;
    d3.select(svgRef.current).transition().duration(250).call(zoomBehaviorRef.current.scaleBy, 0.77);
  };

  return (
    <div className="tree-viewer-container" ref={containerRef}>
      {/* Floating canvas controls toolbar */}
      <div className="tree-toolbar">
        <button type="button" onClick={handleZoomIn} title="Zoom In">+</button>
        <button type="button" onClick={handleZoomOut} title="Zoom Out">−</button>
        <button type="button" onClick={fitToScreen} title="Fit to Screen">Fit</button>
        <button
          type="button"
          className="toolbar-btn-collapse"
          onClick={handleCollapseAll}
          title="Collapse all branches back to depth 4"
        >
          Collapse All
        </button>
        <button
          type="button"
          className="toolbar-btn-expand"
          onClick={handleExpandAll}
          disabled={isExpandAllDisabled}
          title={
            isExpandAllDisabled
              ? "Disabled for large trees (n >= 7 or > 3,000 nodes) to prevent browser lag. Click individual nodes to expand level by level."
              : "Expand all branches"
          }
        >
          {isExpandAllDisabled ? "Expand All (Capped at n=6)" : "Expand All"}
        </button>
      </div>

      {/* SVG Canvas hosting interactive tidy tree */}
      <svg ref={svgRef} className="tree-svg-canvas" width="100%" height="100%">
        <defs>
          <pattern id="grid-pattern" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="#2a3342" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid-pattern)" />
        <g ref={viewportRef} className="tree-viewport">
          {/* Reingold-Tilford links and directional branch badges */}
          <g className="links-layer">
            {links.map((link, index) => {
              const pathD = generateLinkPath(link, 70);
              const branch = link.target.data.attributes?.branch;
              const isYes = branch === "Yes";
              const isNo = branch === "No";

              // Midpoint coordinate along the vertical Bezier curve
              const badgeX = (link.source.x + link.target.x) / 2;
              const badgeY = (link.source.y + 35 + link.target.y - 35) / 2;

              return (
                <g key={`link-${index}`} className="tree-link-group">
                  <path
                    d={pathD}
                    className={`tree-link ${isYes ? "link-yes" : isNo ? "link-no" : ""}`}
                    fill="none"
                  />
                  {branch && (
                    <g
                      className={`branch-badge-group ${isYes ? "badge-yes" : "badge-no"}`}
                      transform={`translate(${badgeX}, ${badgeY})`}
                    >
                      <circle r="11" className="branch-badge-circle" />
                      <text dy="0.32em" textAnchor="middle" className="branch-badge-text">
                        {isYes ? "Y" : isNo ? "N" : branch}
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </g>

          {/* Decision tree comparison and leaf node cards */}
          <g className="nodes-layer">
            {nodes.map((node, index) => {
              const isLeaf = (!node.children && !node.data.isCollapsed) || node.data.attributes?.type === "leaf";
              const isCollapsed = Boolean(node.data.isCollapsed);
              const { name, attributes, nodeId, collapsedLeafCount } = node.data;
              const cardW = 150;
              const cardH = 70;
              const left = node.x - cardW / 2;
              const top = node.y - cardH / 2;

              return (
                <g
                  key={`node-${index}`}
                  className={`tree-node-group ${isLeaf ? "node-leaf" : "node-comparison"}`}
                  transform={`translate(${left}, ${top})`}
                  style={{ cursor: isLeaf ? "default" : "pointer" }}
                  onClick={() => !isLeaf && nodeId && handleToggleCollapse(nodeId, node.data)}
                  onMouseEnter={(e) => {
                    const rect = containerRef.current?.getBoundingClientRect() || {
                      left: 0,
                      top: 0,
                      width: 800,
                      height: 600,
                    };
                    const rawX = e.clientX - rect.left + 15;
                    const rawY = e.clientY - rect.top + 15;
                    // Clamp tooltip position within container bounds to prevent right/bottom clipping
                    const clampedX = Math.max(12, Math.min(rawX, (rect.width || 800) - 305));
                    const clampedY = Math.max(12, Math.min(rawY, (rect.height || 600) - 150));
                    setHoveredNode({
                      data: node.data,
                      screenX: clampedX,
                      screenY: clampedY,
                    });
                  }}
                  onMouseLeave={() => setHoveredNode(null)}
                >
                  <rect width={cardW} height={cardH} rx="8" className="node-card-bg" />
                  {isLeaf ? (
                    <>
                      <rect width={cardW} height="20" rx="8" className="node-card-header leaf-header" />
                      <text x={cardW / 2} y="14" textAnchor="middle" className="node-header-text">
                        LEAF ({attributes?.count || 1})
                      </text>
                      <text x={cardW / 2} y="40" textAnchor="middle" className="node-sub-text">
                        Out: {attributes?.output || "Sorted"}
                      </text>
                      <text x={cardW / 2} y="56" textAnchor="middle" className="node-hint-text">
                        In: {attributes?.input || ""}
                      </text>
                    </>
                  ) : (
                    <>
                      <rect width={cardW} height="20" rx="8" className="node-card-header comparison-header" />
                      <text x={cardW / 2} y="14" textAnchor="middle" className="node-header-text">
                        {isCollapsed ? "COMPARISON (FOLDED)" : "COMPARISON"}
                      </text>
                      <text x={cardW / 2} y="48" textAnchor="middle" className="node-title-text">
                        {name}
                      </text>
                      {isCollapsed && (
                        <g className="collapsed-indicator" transform={`translate(${cardW / 2}, ${cardH + 2})`}>
                          <rect x="-44" y="-8" width="88" height="18" rx="9" className="collapsed-indicator-bg" />
                          <text dy="0.32em" textAnchor="middle" className="collapsed-indicator-text">
                            +{collapsedLeafCount} leaves
                          </text>
                        </g>
                      )}
                    </>
                  )}
                </g>
              );
            })}
          </g>
        </g>
      </svg>

      {/* Floating tooltip displaying leaf swap details and input permutations */}
      {hoveredNode && (
        <div
          className="tree-node-tooltip"
          style={{ left: hoveredNode.screenX, top: hoveredNode.screenY }}
        >
          <h4>{hoveredNode.data.name}</h4>
          {hoveredNode.data.isCollapsed ? (
            <p className="tooltip-note">
              Subtree folded (<strong>{hoveredNode.data.collapsedLeafCount}</strong> leaves hidden). Click node to expand.
            </p>
          ) : hoveredNode.data.attributes?.type === "leaf" ? (
            <div className="tooltip-details">
              <p><strong>Permutations arriving:</strong> {hoveredNode.data.attributes?.count}</p>
              <p><strong>Result:</strong> {hoveredNode.data.attributes?.output}</p>
              {hoveredNode.data.permutations && hoveredNode.data.permutations.length > 0 && (
                <div className="tooltip-permutations">
                  <span className="tooltip-subheading">Sample trace:</span>
                  <div className="tooltip-trace">
                    Input: {JSON.stringify(hoveredNode.data.permutations[0].input)}
                    <br />
                    Swaps: {JSON.stringify(hoveredNode.data.permutations[0].swaps)}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="tooltip-note">Click node to collapse / fold subtree</p>
          )}
        </div>
      )}
    </div>
  );
}

