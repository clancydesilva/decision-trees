import os
import json
import mimetypes
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from decision_tree import DecisionTree, MAX_FULL_TREE_N
from algorithms import ALL_ALGORITHMS, ALGORITHM_INFO

ALGORITHM_MAP = {algo.__name__: algo for algo in ALL_ALGORITHMS}
STATIC_DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "visualiser", "dist"))
STATIC_PUBLIC_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "visualiser", "public", "data"))


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


def writeJsonAtomic(file_path, payload):
    # Write compact JSON to a temporary sibling file and atomically replace destination
    tmp_path = f"{file_path}.tmp.{os.getpid()}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, file_path)


def exportAllDatasets(output_dir="visualiser/public/data"):
    # Pre-generate compact JSON datasets for all 9 algorithms across n=1..7 (63 datasets total)
    os.makedirs(output_dir, exist_ok=True)
    algo_catalog = []
    supported_sizes = list(range(1, MAX_FULL_TREE_N + 1))

    for algo_fn in ALL_ALGORITHMS:
        algo_catalog.append({
            "id": algo_fn.__name__,
            "name": ALGORITHM_INFO[algo_fn]["name"],
        })
        for n in supported_sizes:
            payload = generateTreePayload(algo_fn, n)
            file_path = os.path.join(output_dir, f"{algo_fn.__name__}_n{n}.json")
            writeJsonAtomic(file_path, payload)

    catalog_path = os.path.join(output_dir, "algorithms.json")
    writeJsonAtomic(catalog_path, {"algorithms": algo_catalog, "supported_n": supported_sizes})


class DecisionTreeRequestHandler(BaseHTTPRequestHandler):
    # Lightweight HTTP handler acting as a local REST API and static file server
    def _sendHeaders(self, content_type="application/json", status=200, extra_headers=None):
        # Attach standard response headers and enable Cross-Origin Resource Sharing (CORS)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if extra_headers:
            for header_name, header_val in extra_headers.items():
                self.send_header(header_name, header_val)
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
            self.wfile.write(
                json.dumps(
                    {"algorithms": catalog, "supported_n": list(range(1, MAX_FULL_TREE_N + 1))},
                    separators=(",", ":"),
                ).encode("utf-8")
            )
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

            if n > MAX_FULL_TREE_N:
                self._sendHeaders(status=400)
                self.wfile.write(json.dumps({
                    "error": f"n={n} is too large for full permutation trees ({n}! permutations). Maximum supported size is n={MAX_FULL_TREE_N}."
                }).encode("utf-8"))
                return

            # Look up the algorithm function reference from the mapping dictionary
            algo_fn = ALGORITHM_MAP.get(algo_id)
            if not algo_fn:
                self._sendHeaders(status=404)
                self.wfile.write(json.dumps({"error": f"Algorithm '{algo_id}' not found"}).encode("utf-8"))
                return

            # Run decision tree algorithm and return compact JSON
            payload = generateTreePayload(algo_fn, n)
            self._sendHeaders()
            self.wfile.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
            return

        # Route 3: Serve built frontend static assets from visualiser/dist when present
        if os.path.isdir(STATIC_DIST_DIR):
            unquoted_path = urllib.parse.unquote(parsed_url.path)
            # Reject explicit parent-directory traversal segments in raw or decoded URL path
            path_segments = [seg for seg in unquoted_path.replace("\\", "/").split("/") if seg]
            if ".." in path_segments:
                self._sendHeaders(status=403)
                self.wfile.write(json.dumps({"error": "Forbidden"}).encode("utf-8"))
                return

            rel_path = "/".join(path_segments) if path_segments else "index.html"
            dist_root = os.path.realpath(STATIC_DIST_DIR)
            candidate_path = os.path.realpath(os.path.join(dist_root, rel_path))

            # Guard against directory traversal and prefix collisions outside STATIC_DIST_DIR
            try:
                is_within_dist = os.path.commonpath([dist_root, candidate_path]) == dist_root
            except ValueError:
                is_within_dist = False

            if not is_within_dist:
                self._sendHeaders(status=403)
                self.wfile.write(json.dumps({"error": "Forbidden"}).encode("utf-8"))
                return

            # Fall back to visualiser/public/data if a /data/* file is requested before dist rebuild
            if not os.path.isfile(candidate_path) and len(path_segments) == 2 and path_segments[0] == "data":
                public_data_root = os.path.realpath(STATIC_PUBLIC_DATA_DIR)
                alt_candidate = os.path.realpath(os.path.join(public_data_root, path_segments[1]))
                if os.path.commonpath([public_data_root, alt_candidate]) == public_data_root and os.path.isfile(alt_candidate):
                    candidate_path = alt_candidate

            if os.path.isfile(candidate_path):
                mime_type, _ = mimetypes.guess_type(candidate_path)
                extra_headers = None
                if unquoted_path.startswith("/data/"):
                    extra_headers = {"Cache-Control": "public, max-age=3600"}
                self._sendHeaders(
                    content_type=mime_type or "application/octet-stream",
                    status=200,
                    extra_headers=extra_headers,
                )
                with open(candidate_path, "rb") as f:
                    self.wfile.write(f.read())
                return

            # SPA fallback to index.html for non-API and non-data routes
            index_path = os.path.join(dist_root, "index.html")
            if not unquoted_path.startswith("/api/") and not unquoted_path.startswith("/data/") and os.path.isfile(index_path):
                self._sendHeaders(content_type="text/html; charset=utf-8", status=200)
                with open(index_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        # Fallback for any unrecognized URL path
        self._sendHeaders(status=404)
        self.wfile.write(json.dumps({"error": "Route not found"}).encode("utf-8"))


def startServer(host=None, port=None):
    # Start the threaded HTTP server binding to configurable host and port
    bind_host = host or os.environ.get("HOST", "127.0.0.1")
    bind_port = int(port or os.environ.get("PORT", "5001"))
    server_address = (bind_host, bind_port)
    httpd = ThreadingHTTPServer(server_address, DecisionTreeRequestHandler)
    print(f"Starting DecisionTree server on http://{bind_host}:{bind_port}")
    httpd.serve_forever()


if __name__ == "__main__":
    import sys
    if "--serve" in sys.argv:
        host_arg = "0.0.0.0" if "--production" in sys.argv else None
        startServer(host=host_arg)
    else:
        out_dir = "visualiser/public/data"
        if "--output" in sys.argv:
            idx = sys.argv.index("--output")
            if idx + 1 < len(sys.argv):
                out_dir = sys.argv[idx + 1]
        exportAllDatasets(output_dir=out_dir)
        print(f"Precomputed datasets generated in {out_dir}/")
