# 🚀 Project QR-Share: Cloud-Native Automated GitOps Infrastructure

---

## 📝 Project Overview
When developers write code, they often have to manually build it, push it to a registry, and update their servers. This project completely automates that entire process. 

It is a fully automated system where a developer just pushes code to GitHub, and a background automation engine automatically packages the application, runs it inside a secure container, and deploys it live to a cloud cluster without a single second of downtime.

---

## 🎯 Key Core Features
Once this infrastructure is live, end-users can access the web platform to:
* **Secure Media Uploads:** Instantly upload files or photos through a clean web interface.
* **Dynamic QR Generation:** Create fast dynamic QR links for easy content sharing.
* **S3 Object Storage:** Store assets cleanly inside an isolated private storage bucket.
* **Role-Based Access:** Log into the dashboard using isolated Admin or Guest profiles.

---

## 🛠️ Technological Stack

* **Web Application:** Python 3.11-slim | Flask Framework | Gunicorn WSGI
* **Automation Server:** Jenkins Core Engine (Groovy Pipeline-as-Code)
* **Container Layer:** Docker Engine & Docker Hub Registry
* **Orchestration Hub:** Kubernetes (Pods, Services, and Cluster Secrets)
* **Storage Engine:** MinIO S3 Object Storage API (Boto3 Client Integration)

---

## 🏗️ System Architecture Workflow

```text
===================================================================================
 [ GitHub Repository ] ────► [ Jenkins Server ] ────► [ Docker Container Engine ]
  (Public Code Source)        (Automation Hub)           (Compiles App Layers)
                                     │                            │
                                     ▼ (Direct Deploy)            ▼ (Pushes Image)
                              [ Kubernetes Cluster ] ◄─── [ Docker Hub Registry ]
                                ├── Flask Web Pods          (Secure Cloud Storage)
                                └── MinIO S3 Storage
===================================================================================

⚙️ CI/CD Pipeline Implementation
📥 1. The Source Code Retrieval Stage
Objective: Establish automated pull mechanics from the source repository.

Execution: Linked Jenkins directly to GitHub using a declarative pipeline script. The moment a run triggers, the workspace wipes old files cleanly (cleanWs) and pulls down the fresh code.

🐳 2. The Application Isolation Stage
Objective: Compile the application code into an immutable environment layer.

Execution: Created a custom Dockerfile that packages our Flask code with a lightweight Python Linux environment. It builds non-root execution parameters and caches system dependencies so subsequent builds take less than 2 seconds.

🚀 3. The Artifact Publication Stage
Objective: Ship the tested build secure to a public image registry.

Execution: Injected a secure Docker Hub Automation Token directly into Jenkins memory on system boot (init.groovy.d), letting the pipeline securely login and publish container images automatically without exposing plain-text keys.

☸️ 4. The Zero-Downtime Deployment Stage
Objective: Apply runtime state updates to the active cluster.

Execution: Programmed Jenkins to use standard terminal stream tools (sed) to update live Kubernetes YAML manifests dynamically. It patches cluster tags, forces an active rolling container update, and provisions S3 storage buckets automatically behind the scenes.

🎓 Core Competencies & Skills Mastered
Infrastructure-as-Code (IaC): Moved completely away from manual GUI management by writing programmatic Jenkinsfiles and declarative Kubernetes definitions.

Linux Hardening & System Administration: Mastered secure process delegation by mapping isolated system users (jenkins) to host daemons (docker.sock) using precise user-group adjustments.

Overcoming Network & Proxy Roadblocks: Utilized Jenkins initialization scripts (init.groovy.d) to bypass browser network proxy shifts and pre-configure server parameters before the UI even logs in.

S3 Storage APIs Integration: Gained deep experience connecting live microservices with an S3 object storage API layer (MinIO) using native Python helper modules (boto3).

Container Least-Privilege Practices: Set up strict container security protocols by switching runtime executions to restricted non-root profiles (appuser).
