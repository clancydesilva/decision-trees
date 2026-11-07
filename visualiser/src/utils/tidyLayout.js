import * as d3 from "d3";

// Normalize node children into strict binary slots (left = Yes, right = No)
// Satisfies Reingold-Tilford Aesthetic 2 by inserting virtual placeholders for single-branch nodes
function normalizeBinarySlots(node) {
  if (!node) return null;

  const clone = {
    ...node,
    attributes: { ...node.attributes },
  };

  // Leaves have no children to slot
  if (!node.children || node.children.length === 0) {
    clone.children = null;
    return clone;
  }

  // Identify Yes and No branch children based on branch attribute
  let yesChild = null;
  let noChild = null;

  node.children.forEach((child) => {
    const branch = child.attributes?.branch;
    if (branch === "Yes") {
      yesChild = normalizeBinarySlots(child);
    } else if (branch === "No") {
      noChild = normalizeBinarySlots(child);
    } else {
      // Fallback: if branch attribute is absent, preserve original child order
      if (!yesChild) {
        yesChild = normalizeBinarySlots(child);
      } else {
        noChild = normalizeBinarySlots(child);
      }
    }
  });

  // Insert virtual placeholder if a branch outcome is absent to prevent centering
  const leftChild = yesChild || { isPlaceholder: true, name: "virtual-yes", children: null };
  const rightChild = noChild || { isPlaceholder: true, name: "virtual-no", children: null };

  clone.children = [leftChild, rightChild];
  return clone;
}

// Compute Reingold-Tilford tidy coordinates for a decision tree hierarchy
export function computeTidyTreeLayout(rawTreeData, options = {}) {
  if (!rawTreeData) {
    return { nodes: [], links: [], bounds: { minX: 0, maxX: 0, minY: 0, maxY: 0, width: 0, height: 0 } };
  }

  const nodeWidth = options.nodeWidth || 160;
  const nodeHeight = options.nodeHeight || 80;
  const levelDistance = options.levelDistance || 110;
  const siblingGap = options.siblingGap || 20;

  // 1. Structure the binary tree with virtual slots
  const structuredRoot = normalizeBinarySlots(rawTreeData);

  // 2. Instantiate D3 hierarchy
  const hierarchyRoot = d3.hierarchy(structuredRoot, (d) => d.children);

  // 3. Configure D3 tidy tree layout engine implementing Reingold-Tilford contour separation
  const treeEngine = d3.tree()
    .nodeSize([nodeWidth + siblingGap, levelDistance + nodeHeight])
    .separation((a, b) => (a.parent === b.parent ? 1.0 : 1.25));

  treeEngine(hierarchyRoot);

  // 4. Filter out virtual placeholders to keep only physical decision tree elements
  const visibleNodes = hierarchyRoot.descendants().filter((d) => !d.data.isPlaceholder);
  const visibleLinks = hierarchyRoot.links().filter((link) => !link.target.data.isPlaceholder && !link.source.data.isPlaceholder);

  // 5. Calculate layout bounding box for canvas centering and zoom framing
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;

  visibleNodes.forEach((node) => {
    if (node.x < minX) minX = node.x;
    if (node.x > maxX) maxX = node.x;
    if (node.y < minY) minY = node.y;
    if (node.y > maxY) maxY = node.y;
  });

  return {
    nodes: visibleNodes,
    links: visibleLinks,
    bounds: {
      minX,
      maxX,
      minY,
      maxY,
      width: maxX - minX + nodeWidth,
      height: maxY - minY + nodeHeight,
    },
  };
}

