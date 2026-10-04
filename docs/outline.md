# Automated Construction and Analysis of Decision Trees for Comparison-Based Algorithms

## Project Outline

**Clancy DeSilva** • 123436262 • **Supervisor:** Michel Schellekens • October 4, 2026

---

### 1. High Level Project Analysis

**What the project is about.**  
When a sorting algorithm runs, every decision it makes comes from comparing two elements and asking "is this one smaller than the other". If we record the answers to these questions for every possible input of a given size ($n$), the results form a binary tree, called a *decision tree*. Each branching point is a comparison, each branch is a yes/no answer, and each leaf is a place where the algorithm finishes. The aim of this project is to build an online tool that generates these trees automatically, displays them clearly, and uses them to analyse how efficient different algorithms are.

**Why it is useful.**  
Decision trees show exactly how much work an algorithm does. The longest path in the tree is the worst case, and the average path length is the average case. Theory gives a minimum number of comparisons any algorithm must make, so the tool can measure how close each algorithm comes to that limit. Drawing these trees by hand is only realistic for very small inputs, which is why an automated tool is valuable.

**How it works.**  
Each algorithm runs on a special list that records every comparison and swap it makes. The algorithm is run on every possible ordering of the input, and runs that give the same answers to the same questions are grouped together, building the tree one path at a time. At each leaf, the recorded swaps are replayed to check that the algorithm really produced the correct result, whether that is a sorted list, a valid heap, or a partly sorted list.

**Main challenge.**  
Trees grow very quickly: a list of 5 elements already has 120 possible orderings, making the full tree hard to read. To handle this, the tool will support *partial sorting* algorithms, which produce smaller trees, and an interactive view where large parts of the tree are collapsed into a summary (for example, "these elements now form a heap") that the user can click on to expand further.

**Progress so far.**  
The recording list, eight standard sorting algorithms and the core tree-building code are complete, and produce the correct tree for small inputs.

---

### 2. The Theory

**Yao's Principle.**  
Yao's principle states that the best performance of a randomized algorithm on a worst-case input equals the best performance of a deterministic algorithm on a hard random input distribution.

By Yao's principle, the minimum average depth of a deterministic decision tree under uniformly random inputs also bounds the expected cost of any randomised algorithm on its worst input, so the bounds computed by the tool apply to randomised algorithms as well.

---

### 3. Plan

1. **Foundation** *(complete)* — recording list, basic sorting algorithms and tree builder.
2. **Choose a visualisation technology** *(in progress)* — try several options (such as Graphviz, D3.js and Cytoscape.js) on small trees and pick the one that is interactive, clear and works well online.
3. **Build the visualiser** — labelled trees, the ability to view a chosen subtree, and collapsible summary nodes for large trees.
4. **More complex algorithms** — heapify (building a heap from an unordered list) and partial sorting algorithms.
5. **Specialised algorithms** — algorithms suggested by my supervisor, including different cases of merging two heaps.
6. **Analysis** — compare each algorithm's average number of comparisons with the theoretical minimum, using random samples for larger inputs.
7. **Evaluation and report** — test the tool, assess the results and write up the project.
