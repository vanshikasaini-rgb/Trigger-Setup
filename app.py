from flask import Flask, jsonify
import threading

# IMPORTANT: direct import
from Scripts.cli import run_full_indexing, download_and_process_uploads

app = Flask(__name__)

def run_pipeline():
    try:
        # Run only what you want on button click
        download_and_process_uploads()
    except Exception as e:
        print("Pipeline error:", e)

@app.route("/", methods=["GET"])
def health():
    return "Media Portfolio Automation is running", 200

@app.route("/run", methods=["POST"])
def run():
    thread = threading.Thread(target=run_pipeline)
    thread.start()
    return jsonify({"status": "started"}), 200

if __name__ == "__main__":
    import os
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
