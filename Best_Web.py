from flask import Flask, render_template, request, redirect, url_for, session
import os, subprocess, signal, time, threading, zipfile

app = Flask(__name__)
app.secret_key = "nirob_ultra_funk_2026"

SECRET_PASS = "NIROB"
UPLOAD_FOLDER = "projects"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
active_nodes = {}

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get('authorized'):
        if request.method == "POST" and request.form.get("password") == SECRET_PASS:
            session['authorized'] = True
            return redirect(url_for("index"))
        return render_template("index.html", login_mode=True)

    if request.method == "POST" and 'zip_file' in request.files:
        file = request.files.get("zip_file")
        main_file = request.form.get("p_name") # এখানে ছোট হাতের অক্ষর কাজ করবে
        
        if file and file.filename.endswith('.zip'):
            p_path = os.path.join(UPLOAD_FOLDER, str(time.time()))
            os.makedirs(p_path, exist_ok=True)
            z_path = os.path.join(p_path, "source.zip")
            file.save(z_path)
            
            with zipfile.ZipFile(z_path, 'r') as z_ref:
                z_ref.extractall(p_path)
            
            # ফাইলের ধরন অনুযায়ী রান করার লজিক
            cmd = []
            if main_file.endswith('.py'):
                cmd = ['python3', main_file]
            elif main_file.endswith('.html'):
                cmd = ['python3', '-m', 'http.server', '8081'] # HTML এর জন্য লোকাল সার্ভার
            else:
                cmd = ['node', main_file] # অন্যান্য ক্ষেত্রে (যেমন JS)

            try:
                proc = subprocess.Popen(cmd, cwd=p_path, preexec_fn=os.setsid)
                active_nodes[main_file] = {"proc": proc, "start": time.time()}
                
                # ২ ঘণ্টা পর অটো-কিল
                threading.Timer(7200, lambda: os.killpg(os.getpgid(proc.pid), signal.SIGTERM)).start()
            except Exception as e:
                print(f"Error starting file: {e}")

    return render_template("index.html", login_mode=False, nodes=active_nodes)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8030)
