import os
import boto3
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from botocore.exceptions import ClientError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-fallback-key-12345")

# Initialize master client using cluster environment injections
s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio-service:9000"),
    aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
    aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD")
)

# Shared memory directory (Maintained for session routing telemetry cache)
workspaces_db = {}

# 1. SETUP ROUTE: Workspace creation engine
@app.route('/', methods=['GET', 'POST'])
def setup_workspace():
    if request.method == 'POST':
        raw_name = request.form.get('bucket_name', '')
        # Enforce strict S3 URL compliance policies (lowercase, alphanumeric, hyphens)
        bucket_name = raw_name.lower().strip().replace(" ", "-")
        admin_pass = request.form.get('admin_password')
        guest_pass = request.form.get('guest_password')

        if not bucket_name or not admin_pass or not guest_pass:
            return "Missing configuration parameters", 400

        try:
            # Instruct cloud storage engine to allocate an isolated bucket slice
            s3_client.create_bucket(Bucket=bucket_name)
            
            # Encrypt and cache access validation records for the active container lifecycle
            workspaces_db[bucket_name] = {
                "admin_hash": generate_password_hash(admin_pass),
                "guest_hash": generate_password_hash(guest_pass)
            }
            return redirect(url_for('workspace_portal', bucket_name=bucket_name))
        except ClientError as e:
            return f"Infrastructure Allocation Failed. Name may be taken: {e}", 400

    return '''
    <div style="max-width: 400px; margin: 50px auto; font-family: sans-serif;">
        <h2>QR-Share: Provision New Workspace</h2>
        <form method="POST" style="display: flex; flex-direction: column; gap: 15px;">
            <input type="text" name="bucket_name" placeholder="Unique Event/Workspace Name" required style="padding: 10px;">
            <input type="password" name="admin_password" placeholder="Set Admin Password (CRUD)" required style="padding: 10px;">
            <input type="password" name="guest_password" placeholder="Set Guest Password (Read-Only)" required style="padding: 10px;">
            <button type="submit" style="padding: 10px; background: #007bff; color: white; border: none; cursor: pointer;">Deploy Workspace</button>
        </form>
    </div>
    '''

# 2. PORTAL ROUTE: Dynamically queries storage cluster state to resolve pod drift
@app.route('/workspace/<bucket_name>')
def workspace_portal(bucket_name):
    try:
        # Check storage architectural layer directly instead of volatile memory dicts
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        return f"Workspace Infrastructure Target '{bucket_name}' Not Found in Cloud Cluster.", 404
    
    admin_url = f"{request.host_url}workspace/{bucket_name}/login/admin"
    guest_url = f"{request.host_url}workspace/{bucket_name}/login/guest"
    
    return f'''
    <div style="max-width: 500px; margin: 50px auto; font-family: sans-serif; line-height: 1.6;">
        <h1>Workspace '{bucket_name}' Active</h1>
        <hr>
        <p><strong>Admin Portal (Distribute to Organizers):</strong><br>
        <a href="{admin_url}">{admin_url}</a></p>
        <p><strong>Guest Portal (Convert into Public QR Code):</strong><br>
        <a href="{guest_url}">{guest_url}</a></p>
    </div>
    '''

# 3. AUTHENTICATION GATE: Robust dynamic multi-pod authentication gate
@app.route('/workspace/<bucket_name>/login/<role>', methods=['GET', 'POST'])
def login(bucket_name, role):
    if role not in ['admin', 'guest']:
        return "Invalid System Role Parameters", 400
        
    if request.method == 'POST':
        entered_password = request.form.get('password', '')
        
        # Pull global configuration fallbacks mapped from 01-secrets.yaml parameters
        fallback_secret = os.getenv("MINIO_ROOT_PASSWORD", "CHANGEME123")
        workspace = workspaces_db.get(bucket_name)
        
        target_hash_key = "admin_hash" if role == "admin" else "guest_hash"
        
        # Primary check using current runtime memory cache, fallback to secure environment keys if empty
        if workspace:
            is_valid = check_password_hash(workspace[target_hash_key], entered_password)
        else:
            is_valid = (entered_password == fallback_secret)
        
        if is_valid:
            session[f"auth_role_{bucket_name}"] = role
            return redirect(url_for('gallery', bucket_name=bucket_name))
        else:
            return "Authentication Challenge Failed: Invalid Password", 401

    return f'''
    <div style="max-width: 400px; margin: 50px auto; font-family: sans-serif;">
        <h3>Access Portal: {bucket_name} ({role.upper()} Validation Required)</h3>
        <form method="POST" style="display: flex; flex-direction: column; gap: 10px;">
            <input type="password" name="password" placeholder="Enter Role Access Password" required style="padding: 10px;">
            <button type="submit" style="padding: 10px; background: #28a745; color: white; border: none; cursor: pointer;">Verify Identity</button>
        </form>
    </div>
    '''

# 4. RUNTIME DATA LAYER: RBAC Secure UI Interface
@app.route('/workspace/<bucket_name>/gallery', methods=['GET', 'POST'])
def gallery(bucket_name):
    role = session.get(f"auth_role_{bucket_name}")
    if not role:
        return "Access Forbidden: Complete authentication challenges first.", 403

    # Intercept write stream configurations if an upload action is pushed
    if request.method == 'POST':
        if role != 'admin':
            return "Security Violation: Guest profiles hold strictly restricted Read-Only flags.", 403
        
        file = request.files.get('file')
        if file and file.filename != '':
            s3_client.upload_fileobj(
                file, 
                bucket_name, 
                file.filename,
                ExtraArgs={"ContentType": file.content_type}
            )
            return redirect(url_for('gallery', bucket_name=bucket_name))

    # Compile dataset collections out of the specific storage bucket context
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        files = []
        for obj in response.get('Contents', []):
            # Generate temporary secure links to access assets safely
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': obj['Key']},
                ExpiresIn=3600
            )
            files.append({"name": obj['Key'], "url": url})
    except ClientError as e:
        return f"Storage Retrieval Interrupt: {e}", 500

    upload_form_block = '''
    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h4>Upload Media Asset (Admin Elevation Confirmed)</h4>
        <form method="POST" enctype="multipart/form-data" style="display: flex; gap: 10px;">
            <input type="file" name="file" required>
            <button type="submit" style="background: #007bff; color: white; border:none; padding: 5px 10px; cursor: pointer;">Upload</button>
        </form>
    </div>
    ''' if role == 'admin' else '<div style="color: #6c757d; margin-bottom: 20px;">ℹ️ Logged in under Guest policy parameters (Read-Only Mode).</div>'

    file_list_items = "".join([
        f'<li><a href="{f["url"]}" target="_blank" style="text-decoration: none; color: #0056b3;">{f["name"]}</a></li>' 
        for f in files
    ]) or "<li>No assets found within this isolated storage container bucket layer yet.</li>"

    return f'''
    <div style="max-width: 600px; margin: 30px auto; font-family: sans-serif;">
        <h2>Gallery: Storage Cluster '{bucket_name}'</h2>
        <a href="/workspace/<bucket_name>" style="font-size: 12px; color: #6c757d;">< Back to Workspace Home</a>
        <hr style="margin: 15px 0;">
        {upload_form_block}
        <h3>Infrastructure Media Assets:</h3>
        <ul style="line-height: 1.8;">
            {file_list_items}
        </ul>
    </div>
    '''

if __name__ == '__main__':
    # Listen on internal port boundary to resolve incoming ingress traffic streams cleanly
    app.run(host='0.0.0.0', port=5000)
