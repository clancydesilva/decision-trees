import os
import json
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from decision_tree import DecisionTree
from algorithms import ALL_ALGORITHMS, ALGORITHM_INFO

ALGORITHM_MAP = {algo.__name__: algo for algo in ALL_ALGORITHMS}


def generateTreePayload(algo_fn, n):
    # Construct decision tree and extract structured dictionary for the visualiser
    tree = DecisionTree(algo_fn, n)
    tree_dict = tree.toDict()
    return {
        "algorithm": tree.algorithm_name,
        "algorithm_id": algo_fn.__name__,
        "n": n,
        "stats": tree_dict.get("stats", {}),
        "tree": tree_dict.get("tree", {}),
    }


def exportAllDatasets(output_dir="visualiser/public/data"):
    # Pre-generate JSON datasets for all standard algorithms at n=3, n=4, and n=5
    os.makedirs(output_dir, exist_ok=True)
    algo_catalog = []

    for algo_fn in ALL_ALGORITHMS:
        algo_catalog.append({
            "id": algo_fn.__name__,
            "name": ALGORITHM_INFO[algo_fn]["name"],
        })
        for n in (3, 4, 5):
            payload = generateTreePayload(algo_fn, n)
            file_path = os.path.join(output_dir, f"{algo_fn.__name__}_n{n}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

    catalog_path = os.path.join(output_dir, "algorithms.json")
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump({"algorithms": algo_catalog, "supported_n": [3, 4, 5]}, f, indent=2)


class DecisionTreeRequestHandler(BaseHTTPRequestHandler):
    # Lightweight HTTP handler acting as a local REST API without external dependencies (Flask/FastAPI)
    def _sendHeaders(self, content_type="application/json", status=200):
        # Attach standard response headers and enable Cross-Origin Resource Sharing (CORS)
        # This allows the frontend (running on Vite at localhost:5173) to fetch data from localhost:5001
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        # Handle CORS preflight handshake requests sent by modern web browsers
        self._sendHeaders(status=204)

    def do_GET(self):
        # Parse the requested URL path and query parameters
        parsed_url = urllib.parse.urlparse(self.path)

        # Route 1: Catalog of available algorithms and supported sizes for the UI dropdown
        if parsed_url.path == "/api/algorithms":
            catalog = [
                {"id": fn.__name__, "name": ALGORITHM_INFO[fn]["name"]}
                for fn in ALL_ALGORITHMS
            ]
            self._sendHeaders()
            self.wfile.write(json.dumps({"algorithms": catalog, "supported_n": [3, 4, 5, 6, 7]}).encode("utf-8"))
            return

        # Route 2: On-demand algorithm execution and decision tree construction
        if parsed_url.path == "/api/run":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            algo_id = query_params.get("algo", ["bubbleSort"])[0]

            # Validate that the size parameter 'n' is a valid integer
            try:
                n = int(query_params.get("n", ["3"])[0])
            except ValueError:
                self._sendHeaders(status=400)
                self.wfile.write(json.dumps({"error": "Parameter n must be an integer"}).encode("utf-8"))
                return

            # Validate parameter n: require 1 <= n <= 7 for full permutation trees
            if n < 1:
                self._sendHeaders(status=400)
                self.wfile.write(json.dumps({
                    "error": f"Parameter n={n} must be at least 1."
                }).encode("utf-8"))
                return

            if n > 7:
                self._sendHeaders(status=400)
                self.wfile.write(json.dumps({
                    "error": f"n={n} is too large for full permutation trees ({n}! permutations). Maximum supported size is n=7."
                }).encode("utf-8"))
                return

            # Look up the algorithm function reference from the mapping dictionary
            algo_fn = ALGORITHM_MAP.get(algo_id)
            if not algo_fn:
                self._sendHeaders(status=404)
                self.wfile.write(json.dumps({"error": f"Algorithm '{algo_id}' not found"}).encode("utf-8"))
                return

            # Run decision tree algorithm, capture printout and structured tree, then return JSON
            payload = generateTreePayload(algo_fn, n)
            self._sendHeaders()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        # Fallback for any unrecognized URL path
        self._sendHeaders(status=404)
        self.wfile.write(json.dumps({"error": "Route not found"}).encode("utf-8"))


def startServer(port=5001):
    # Start the local threaded development API server
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, DecisionTreeRequestHandler)
    print(f"Starting DecisionTree API server on http://127.0.0.1:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    import sys
    if "--serve" in sys.argv:
        startServer()
    else:
        exportAllDatasets()
        print("Precomputed datasets generated in visualiser/public/data/")
