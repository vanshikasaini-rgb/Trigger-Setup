from flask import Flask, jsonify
import threading
import traceback

app = Flask(__name__)

def run_pipeline():
    print("🚀 PIPELINE STARTED")

    try:
        from Scripts.cli import download_and_process_uploads
        print("📦 Imported pipeline function")

        result = download_and_process_uploads()
        print("✅ PIPELINE FINISHED")
        print("RESULT:", result)

    except Exception as e:
        print("❌ PIPELINE ERROR")
        traceback.print_exc()

@app.route("/", methods=["GET"])
def home():
    return "Media Portfolio Automation is live", 200

@app.route("/run", methods=["POST"])
def run():
    print("🔥 /run triggered")
    threading.Thread(target=run_pipeline).start()
    return jsonify({"status": "started"}), 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
