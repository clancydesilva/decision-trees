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

export function TreeViewer({ treeData }) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const viewportRef = useRef(null);
  const zoomBehaviorRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [collapsedIds, setCollapsedIds] = useState(new Set());

  // Reset collapsed nodes when loading a new algorithm or size
  useEffect(() => {
    setCollapsedIds(new Set());
  }, [treeData]);

  // Compute Reingold-Tilford layout using the adapter with collapsed branches pruned
  const { nodes, links, bounds } = useMemo(() => {
    return computeTidyTreeLayout(treeData, {
      nodeWidth: 150,
      nodeHeight: 70,
      levelDistance: 100,
      siblingGap: 24,
      collapsedIds,
    });
  }, [treeData, collapsedIds]);

  // Toggle subtree folding for an internal comparison node
  const handleToggleCollapse = (nodeId) => {
    setCollapsedIds((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  // Center and fit the entire tree within the visible SVG viewport
  const fitToScreen = useCallback(() => {
    if (!svgRef.current || !containerRef.current || nodes.length === 0) return;

    const width = containerRef.current.clientWidth || 800;
    const height = containerRef.current.clientHeight || 600;
    const padding = 60;

    const treeW = Math.max(bounds.width, 100);
    const treeH = Math.max(bounds.height, 100);

    // Compute scale constrained between 0.15 and 1.2
    const scale = Math.min(1.2, Math.max(0.15, Math.min((width - padding) / treeW, (height - padding) / treeH)));

    // Center root and tree mass horizontally and vertically
    const centerX = width / 2 - ((bounds.minX + bounds.maxX) / 2) * scale;
    const centerY = padding + 20 - bounds.minY * scale;

    const transform = d3.zoomIdentity.translate(centerX, centerY).scale(scale);
    d3.select(svgRef.current)
      .transition()
      .duration(400)
      .call(zoomBehaviorRef.current.transform, transform);
  }, [nodes.length, bounds]);

  // Initialize D3 pan & zoom behavior
  useEffect(() => {
    if (!svgRef.current || !viewportRef.current) return;

    const zoomBehavior = d3.zoom()
      .scaleExtent([0.1, 2.5])
      .on("zoom", (event) => {
        d3.select(viewportRef.current).attr("transform", event.transform);
      });

    zoomBehaviorRef.current = zoomBehavior;
    d3.select(svgRef.current).call(zoomBehavior);

    fitToScreen();
  }, [fitToScreen]);

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
        {collapsedIds.size > 0 && (
          <button
            type="button"
            className="toolbar-btn-expand"
            onClick={() => setCollapsedIds(new Set())}
            title="Expand All Subtrees"
          >
            Expand All
          </button>
        )}
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
                  onClick={() => !isLeaf && nodeId && handleToggleCollapse(nodeId)}
                  onMouseEnter={(e) => {
                    const rect = containerRef.current?.getBoundingClientRect() || { left: 0, top: 0 };
                    setHoveredNode({
                      data: node.data,
                      screenX: e.clientX - rect.left + 15,
                      screenY: e.clientY - rect.top + 15,
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

