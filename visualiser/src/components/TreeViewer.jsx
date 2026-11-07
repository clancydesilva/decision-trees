import React, { useRef, useEffect, useMemo, useCallback } from "react";
import * as d3 from "d3";
import { computeTidyTreeLayout } from "../utils/tidyLayout.js";

export function TreeViewer({ treeData }) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const viewportRef = useRef(null);
  const zoomBehaviorRef = useRef(null);

  // Compute Reingold-Tilford layout using the adapter
  const { nodes, links, bounds } = useMemo(() => {
    return computeTidyTreeLayout(treeData, {
      nodeWidth: 150,
      nodeHeight: 70,
      levelDistance: 100,
      siblingGap: 24,
    });
  }, [treeData]);

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
          {/* Links and node cards will be populated in subsequent chunks */}
        </g>
      </svg>
    </div>
  );
}

