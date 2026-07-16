import os
import boto3
import base64
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

# 1. SETUP ROUTE: Workspace creation engine with S3 Metadata Injection
@app.route('/', methods=['GET', 'POST'])
def setup_workspace():
    if request.method == 'POST':
        raw_name = request.form.get('bucket_name', '')
        bucket_name = raw_name.lower().strip().replace(" ", "-")
        admin_pass = request.form.get('admin_password')
        guest_pass = request.form.get('guest_password')

        if not bucket_name or not admin_pass or not guest_pass:
            return "Missing configuration parameters", 400

        # Generate standard hashes
        admin_hash = generate_password_hash(admin_pass)
        guest_hash = generate_password_hash(guest_pass)

        try:
            # Instruct cloud storage engine to allocate an isolated bucket slice
            s3_client.create_bucket(Bucket=bucket_name)
            
            # 🌟 STRATEGY: Store the password hashes securely inside an empty placeholder file metadata
            s3_client.put_object(
                Bucket=bucket_name,
                Key=".workspace_metadata",
                Body=b"QR-Share Protected System Files",
                Metadata={
                    "admin-hash": admin_hash,
                    "guest-hash": guest_hash
                }
            )
        except ClientError as e:
            # If the bucket exists but the metadata file is missing, recreate it
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=".workspace_metadata",
                    Body=b"QR-Share Protected System Files",
                    Metadata={
                        "admin-hash": admin_hash,
                        "guest-hash": guest_hash
                    }
                )
            else:
                return f"Infrastructure Allocation Failed: {e}", 400
            
        return redirect(url_for('workspace_portal', bucket_name=bucket_name))

    return '''
    <div style="max-width: 400px; margin: 50px auto; font-family: sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="text-align: center;">QR-Share: Setup Platform</h2>
        <form method="POST" style="display: flex; flex-direction: column; gap: 15px;">
            <input type="text" name="bucket_name" placeholder="Unique Event/Workspace Name" required style="padding: 10px;">
            <input type="password" name="admin_password" placeholder="Set Admin Password (CRUD)" required style="padding: 10px;">
            <input type="password" name="guest_password" placeholder="Set Guest Password (Read-Only)" required style="padding: 10px;">
            <button type="submit" style="padding: 10px; background: #007bff; color: white; border: none; cursor: pointer; border-radius: 4px;">Deploy Workspace</button>
        </form>
    </div>
    '''

# 2. SUCCESS PORTAL: Generates a SINGLE URL for the cluster gateway
@app.route('/workspace/<bucket_name>')
def workspace_portal(bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        return f"Workspace Infrastructure Target '{bucket_name}' Not Found.", 404
    
    unified_share_url = f"{request.host_url}workspace/{bucket_name}/login"
    
    return f'''
    <div style="max-width: 500px; margin: 50px auto; font-family: sans-serif; line-height: 1.6; padding: 20px; border: 1px solid #ddd; border-radius: 8px; text-align: center;">
        <h1 style="color: #28a745;">Workspace Active!</h1>
        <hr>
        <p><strong>Unified Shareable Platform Link:</strong><br>
        <a href="{unified_share_url}" style="font-size: 16px; color: #007bff; font-weight: bold;">{unified_share_url}</a></p>
        <p style="color: #6c757d; font-size: 13px;">Convert this single link into a QR code. Access level will be evaluated directly by the password entered.</p>
    </div>
    '''

# 3. UNIFIED LOGIN GATE: Pulls metadata directly from MinIO to prevent multi-pod drift
@app.route('/workspace/<bucket_name>/login', methods=['GET', 'POST'])
def login(bucket_name):
    if request.method == 'POST':
        entered_password = request.form.get('password', '')
        
        try:
            # 🌟 Query MinIO directly for the hidden metadata file containing hashes
            response = s3_client.head_object(Bucket=bucket_name, Key=".workspace_metadata")
            metadata = response.get('Metadata', {})
            admin_hash = metadata.get('admin-hash')
            guest_hash = metadata.get('guest-hash')
        except ClientError:
            return "Workspace configuration metadata missing or corrupted.", 500

        # Validate entries dynamically against the centralized MinIO hashes
        if admin_hash and check_password_hash(admin_hash, entered_password):
            session[f"auth_role_{bucket_name}"] = "admin"
            return redirect(url_for('gallery', bucket_name=bucket_name))
        elif guest_hash and check_password_hash(guest_hash, entered_password):
            session[f"auth_role_{bucket_name}"] = "guest"
            return redirect(url_for('gallery', bucket_name=bucket_name))
        else:
            return "Authentication Failed: Invalid Workspace Password", 401

    return f'''
    <div style="max-width: 400px; margin: 50px auto; font-family: sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h3 style="text-align: center;">Welcome to {bucket_name}</h3>
        <p style="font-size: 13px; color: #6c757d; text-align: center;">Enter your gateway password below to unlock access.</p>
        <form method="POST" style="display: flex; flex-direction: column; gap: 10px;">
            <input type="password" name="password" placeholder="Enter Access Password" required style="padding: 10px;">
            <button type="submit" style="padding: 10px; background: #28a745; color: white; border: none; cursor: pointer; border-radius: 4px;">Unlock Gateway</button>
        </form>
    </div>
    '''

# 4. RUNTIME DATA LAYER: Renders inline assets securely avoiding internal cross-origin shifts
@app.route('/workspace/<bucket_name>/gallery', methods=['GET', 'POST'])
def gallery(bucket_name):
    role = session.get(f"auth_role_{bucket_name}")
    if not role:
        return "Access Forbidden: Authenticate through portal first.", 403

    if request.method == 'POST':
        if role != 'admin':
            return "Security Violation: Guest accounts have read-only privileges.", 403
        
        file = request.files.get('file')
        if file and file.filename != '':
            s3_client.upload_fileobj(
                file, 
                bucket_name, 
                file.filename,
                ExtraArgs={"ContentType": file.content_type}
            )
            return redirect(url_for('gallery', bucket_name=bucket_name))

    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        files = []
        for obj in response.get('Contents', []):
            # 🌟 Skip the hidden configuration metadata file in the user UI grid view
            if obj['Key'] == ".workspace_metadata":
                continue
                
            s3_obj = s3_client.get_object(Bucket=bucket_name, Key=obj['Key'])
            obj_bytes = s3_obj['Body'].read()
            b64_data = base64.b64encode(obj_bytes).decode('utf-8')
            content_type = s3_obj.get('ContentType', 'image/jpeg')
            inline_src = f"data:{content_type};base64,{b64_data}"
            
            files.append({"name": obj['Key'], "src": inline_src})
    except ClientError as e:
        return f"Storage Retrieval Interrupt: {e}", 500

    upload_form_block = '''
    <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 30px; border: 1px dashed #007bff;">
        <h4 style="margin-top: 0; color: #007bff;">Upload Media Asset (Admin Account Authenticated)</h4>
        <form method="POST" enctype="multipart/form-data" style="display: flex; gap: 15px; align-items: center;">
            <input type="file" name="file" required style="padding: 5px;">
            <button type="submit" style="background: #007bff; color: white; border:none; padding: 8px 15px; cursor: pointer; border-radius: 4px;">Upload File</button>
        </form>
    </div>
    ''' if role == 'admin' else '<div style="color: #6c757d; background: #e2e3e5; padding: 10px; border-radius: 4px; margin-bottom: 30px;">ℹ️ Logged in under Guest parameters (Read-Only Mode).</div>'

    gallery_items = ""
    for f in files:
        action_buttons = f'''
        <div style="margin-top: 10px; display: flex; gap: 10px; justify-content: center;">
            <a href="{f['src']}" download="{f['name']}" style="background: #28a745; color: white; padding: 4px 8px; text-decoration: none; font-size: 12px; border-radius: 3px;">Download</a>
            <form method="POST" action="/workspace/{bucket_name}/delete/{f['name']}" style="margin: 0;">
                <button type="submit" style="background: #dc3545; color: white; border: none; padding: 4px 8px; font-size: 12px; cursor: pointer; border-radius: 3px;">Delete</button>
            </form>
        </div>
        ''' if role == 'admin' else f'''
        <div style="margin-top: 10px; text-align: center;">
            <a href="{f['src']}" download="{f['name']}" style="background: #28a745; color: white; padding: 4px 12px; text-decoration: none; font-size: 12px; border-radius: 3px; display: inline-block;">Download</a>
        </div>
        '''

        gallery_items += f'''
        <div style="border: 1px solid #ddd; padding: 10px; border-radius: 6px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
            <img src="{f['src']}" style="width: 100%; height: 150px; object-fit: cover; border-radius: 4px;" alt="Media Asset">
            <div style="font-size: 12px; color: #555; margin-top: 8px; word-break: break-all;">{f['name']}</div>
            {action_buttons}
        </div>
        '''

    if not gallery_items:
        gallery_items = '<p style="color: #6c757d; grid-column: 1 / -1; text-align: center;">No assets found within this isolated storage container layer yet.</p>'

    return f'''
    <div style="max-width: 900px; margin: 30px auto; font-family: sans-serif; padding: 0 20px;">
        <h2>Gallery: Storage Cluster '{bucket_name}'</h2>
        <a href="/workspace/{bucket_name}" style="font-size: 12px; color: #6c757d;">< Back to Workspace Home</a>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid #eee;">
        {upload_form_block}
        <h3>Infrastructure Media Assets:</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; margin-top: 20px;">
            {gallery_items}
        </div>
    </div>
    '''

# 5. REMOVE ROUTE: Deletes an asset securely (Only for Admins)
@app.route('/workspace/<bucket_name>/delete/<filename>', methods=['POST'])
def delete_file(bucket_name, filename):
    role = session.get(f"auth_role_{bucket_name}")
    if role != 'admin':
        return "Unauthorized action request context", 403
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=filename)
        return redirect(url_for('gallery', bucket_name=bucket_name))
    except ClientError as e:
        return f"Deletion Failed: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
