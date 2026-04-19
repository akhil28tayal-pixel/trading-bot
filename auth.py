from kiteconnect import KiteConnect
from flask import Flask, request
import threading
import webbrowser
import json
import config
import os
import time
import datetime

TOKEN_FILE = "token.json"

app = Flask(__name__)
kite = KiteConnect(api_key=config.API_KEY)

access_token_global = None


def _calculate_token_expiry(now=None):
    """Zerodha access tokens expire around 6 AM local time on the next trading day."""
    now = now or datetime.datetime.now()
    expiry = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now >= expiry:
        expiry += datetime.timedelta(days=1)
    return expiry


# =========================
# CALLBACK
# =========================
@app.route("/")
def login_callback():
    global access_token_global

    request_token = request.args.get("request_token")

    if not request_token:
        return "No request token received"

    session = kite.generate_session(
        request_token,
        api_secret=config.API_SECRET
    )

    access_token = session["access_token"]

    expiry = _calculate_token_expiry()

    # Save token with both legacy date and explicit expiry metadata.
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "access_token": access_token,
            "date": str(datetime.date.today()),
            "created_at": datetime.datetime.now().isoformat(),
            "expiry": expiry.isoformat(),
        }, f)

    access_token_global = access_token

    print("✅ Access token generated")

    return "Login successful! You can close this tab."


# =========================
# START SERVER
# =========================
def start_server():
    app.run(host="127.0.0.1", port=5001, use_reloader=False)


# =========================
# LOAD TOKEN (SAFE)
# =========================
def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None

    try:
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)

        expiry_str = data.get("expiry")
        if expiry_str:
            expiry = datetime.datetime.fromisoformat(expiry_str)
            if datetime.datetime.now() >= expiry:
                print("⚠️ Token expired")
                return None
        elif data.get("date") != str(datetime.date.today()):
            # Backward-compatible fallback for older token.json files.
            print("⚠️ Token expired (old date)")
            return None

        return data.get("access_token")

    except:
        return None


# =========================
# MAIN FUNCTION
# =========================
def get_kite():
    global access_token_global
    access_token_global = None

    kite = KiteConnect(api_key=config.API_KEY)

    # =========================
    # TRY EXISTING TOKEN
    # =========================
    token = load_token()

    if token:
        print("✅ Using saved access token")
        kite.set_access_token(token)

        # 🔥 IMPORTANT: sync with config
        config.ACCESS_TOKEN = token

        return kite

    # =========================
    # AUTO LOGIN FLOW
    # =========================
    print("🔐 Starting auto login...")

    # start flask server
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # open login page
    login_url = kite.login_url()
    print("👉 Open this URL if browser doesn't open:")
    print(login_url)

    try:
        webbrowser.open(login_url)
    except Exception:
        pass

    print("⏳ Waiting for login...")

    # ✅ FIX: avoid CPU freeze
    while access_token_global is None:
        time.sleep(1)

    kite.set_access_token(access_token_global)

    # 🔥 CRITICAL FIX: update config
    config.ACCESS_TOKEN = access_token_global

    print("✅ Login successful, token set")

    return kite


# =========================
# MAIN EXECUTION
# =========================
if __name__ == "__main__":
    print("🚀 Starting Flask Authentication Server...")
    print("📡 Server will be available at: http://127.0.0.1:5001")
    print("👉 Access the server to start authentication flow")
    
    # Start Flask server directly
    app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
