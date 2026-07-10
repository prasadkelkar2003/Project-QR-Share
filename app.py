import os, boto3
from flask import Flask, request, render_template_string, Response, session, redirect, url_for
from botocore.client import Config

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'devops_wedding_secure_session_key')

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'wedding-photos')
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'http://minio-service:9000')
ACCESS_KEY = os.environ.get('ACCESS_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')

EXPECTED_GUEST_PASS = os.environ.get('GUEST_PASS')
EXPECTED_ADMIN_PASS = os.environ.get('ADMIN_PASS')

s3 = boto3.client(
    's3', 
    endpoint_url=MINIO_ENDPOINT, 
    aws_access_key_id=ACCESS_KEY, 
    aws_secret_access_key=SECRET_KEY, 
    config=Config(signature_version='s3v4'), 
    region_name='us-east-1'
)

LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>📸 Portal Entry</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui, sans-serif; background: #f8f9fa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); text-align: center; width: 300px; }
        input { width: 100%; padding: 10px; margin: 15px 0; border: 1px solid #ced4da; border-radius: 6px; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; width: 100%; padding: 10px; border-radius: 6px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>📸 Shared Event</h2>
        <p>Enter password to unlock the gallery</p>
        {% if error %}<p style="color: red; font-size: 14px;">{{ error }}</p>{% endif %}
        <form method="POST" action="/login">
            <input type="password" name="password" placeholder="Event Password" required>
            <button type="submit">Unlock Portal</button>
        </form>
    </div>
</body>
</html>
'''

MAIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>📸 Shared Gallery</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; text-align: center; }
        .header { display: flex; justify-content: space-between; align-items: center; max-width: 1000px; margin: 0 auto 20px; }
        .upload-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); display: inline-block; margin-bottom: 25px; }
        .gallery-grid { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; max-width: 1000px; margin: 0 auto; }
        .card-container { background: white; padding: 8px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); display: flex; flex-direction: column; width: 150px; }
        .gallery-item { width: 150px; height: 150px; object-fit: cover; border-radius: 6px; cursor: pointer; }
        .admin-actions { display: flex; justify-content: space-between; margin-top: 8px; width: 100%; gap: 5px; }
        .delete-btn { background: #dc3545; color: white; border: none; border-radius: 4px; padding: 5px 10px; font-size: 12px; cursor: pointer; font-weight: bold; width: 65px; height: 28px; }
        .download-btn { background: #28a745; color: white; border: none; border-radius: 4px; padding: 5px 0; font-size: 12px; cursor: pointer; font-weight: bold; text-decoration: none; display: block; text-align: center; width: 65px; height: 18px; }
        .modal { display: none; position: fixed; z-index: 1000; padding: 40px 10px; left: 0; top: 0; width: 100%; height: 100%; box-sizing: border-box; background-color: rgba(0,0,0,0.9); overflow: auto; }
        .modal-content { margin: auto; display: block; max-width: 90%; max-height: 85vh; border-radius: 8px; }
        .close { position: absolute; top: 15px; right: 25px; color: #f1f1f1; font-size: 40px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h3>Role Area: <span style="color: #007bff; text-transform: uppercase;">{{ role }}</span></h3>
        <a href="/logout" style="text-decoration: none; color: #6c757d; font-size: 14px;">Exit Workspace</a>
    </div>
    <h2>📸 Event Media Dashboard</h2>
    <div class="upload-card">
        <form method="POST" action="/upload" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required><br><br>
            <button type="submit" style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold;">Upload to Storage</button>
        </form>
    </div>
    <hr style="border: 0; height: 1px; background: #dee2e6; margin-bottom: 25px;">
    
    <div class="gallery-grid">
        {% for name in images %}
            <div class="card-container">
                <img src="/image/{{ name }}" class="gallery-item" onclick="openModal(this.src)">
                {% if role == 'admin' %}
                    <div class="admin-actions">
                        <a href="/image/{{ name }}?download=true" download="{{ name }}" class="download-btn">DL</a>
                        <form method="POST" action="/delete/{{ name }}" style="margin:0;">
                            <button type="submit" class="delete-btn" onclick="return confirm('Confirm destructive deletion?')">DEL</button>
                        </form>
                    </div>
                {% endif %}
            </div>
        {% endfor %}
    </div>
    
    <div id="imageModal" class="modal" onclick="if(event.target.id === 'imageModal') this.style.display='none'">
        <span class="close" onclick="document.getElementById('imageModal').style.display='none'">&times;</span>
        <img class="modal-content" id="modalImg">
    </div>
    <script>
        function openModal(src) {
            document.getElementById("imageModal").style.display = "block";
            document.getElementById("modalImg").src = src.split('?')[0];
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    if 'role' not in session:
        return render_template_string(LOGIN_HTML, error=None)
    images = []
    try:
        res = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' in res:
            for o in res['Contents']:
                images.append(o['Key'])
    except Exception as e:
        print(e)
    return render_template_string(MAIN_HTML, images=images, role=session['role'])

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password == EXPECTED_ADMIN_PASS:
        session['role'] = 'admin'
        return redirect(url_for('index'))
    elif password == EXPECTED_GUEST_PASS:
        session['role'] = 'guest'
        return redirect(url_for('index'))
    return render_template_string(LOGIN_HTML, error="Invalid credentials.")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'role' not in session: return "Unauthorized", 403
    f = request.files['file']
    if f:
        s3.upload_fileobj(f, BUCKET_NAME, f.filename, ExtraArgs={"ContentType": f.content_type})
    return redirect(url_for('index'))

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if session.get('role') != 'admin': return "Forbidden", 403
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
    except Exception as e:
        return str(e), 500
    return redirect(url_for('index'))

@app.route('/image/<filename>')
def get_image(filename):
    if 'role' not in session: return "Unauthorized", 401
    try:
        file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
        response = Response(file_obj['Body'].read(), mimetype=file_obj.get('ContentType', 'image/jpeg'))
        if 'download' in request.args:
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    except Exception as e:
        return str(e), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
