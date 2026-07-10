# 🚀 Project QR-Share: Simple Automated GitOps Infrastructure

## 📝 What is this project in a simple way?
When developers write code, they often have to manually build it, push it to a registry, and update their servers. This project completely automates that entire process. 

It is a fully automated system where a developer just pushes code to GitHub, and a background automation engine automatically packages the application, runs it inside a secure container, and deploys it live to a cloud cluster without a single second of downtime.

---

## 🎯 What can someone do using this application?
Once this project is deployed, a user can access a live web platform to:
* **Upload Media securely:** Instantly upload files or photos through a web browser.
* **Generate QR Codes:** Create fast dynamic QR links for easy content sharing.
* **Access Cloud Object Storage:** Store assets cleanly inside a dedicated private storage bucket.
* **Sign In Securely:** Log into the dashboard using isolated Admin or Guest profiles.

---

## 🛠️ Tech Stack Used

* **Web Application:** Python 3.11-slim, Flask Framework, Gunicorn WSGI.
* **Automation (CI/CD):** Jenkins Server (using Groovy Pipeline-as-Code).
* **Containers:** Docker Engine & Docker Hub Registry.
* **Orchestration & Deployments:** Kubernetes (Pods, Services, and Cluster Secrets).
* **Storage Engine:** MinIO S3 Object Storage API.

---

## 🏗️ System Architecture Diagram

```text
===================================================================================
[ GitHub Repository ]  ───►  [ Jenkins Server ]  ───►  [ Docker Container Engine ]
  (Public Code Source)          (Automation Hub)            (Compiles App Layers)
                                       │                              │
                                       ▼ (Direct Deploy)              ▼ (Pushes Image)
                                [ Kubernetes Cluster ] ◄───── [ Docker Hub Registry ]
                                  ├── Flask Web Pods            (Secure Cloud Storage)
                                  └── MinIO S3 Storage
===================================================================================

Detailed Task Breakdown & How We Achieved It
The main goal of this task was to eliminate manual server management. Here is exactly how we engineered the solution:

Setting Up Automatic Retrieval (The SCM Stage)

How: Linked Jenkins directly to GitHub using a declarative pipeline script. The moment a run is triggered, it wipes old files cleanly and pulls down the fresh code.

Isolating the Application (The Build Stage)

How: Created a custom Dockerfile that packages our Flask code with a lightweight Python Linux environment. It caches system dependencies so subsequent builds take less than 2 seconds.

Publishing the Application (The Push Stage)

How: Injected a private secure Docker Hub Automation Token directly into Jenkins memory on system boot, letting the pipeline securely login and publish container images automatically.

Zero-Downtime Deployment (The Deploy Stage)

How: Programmed Jenkins to use standard terminal stream tools (sed) to update live Kubernetes YAML manifests dynamically. It updates cluster configurations, forces a rolling container update, and provisions storage buckets automatically behind the scenes.

🎓 What We Learned New In This Project
Building this project from scratch provided hands-on mastery over real-world DevOps and Cloud Engineering concepts:

Automating Infrastructure via Code: Moving away from manual user clicking by writing programmatic Jenkinsfiles and Kubernetes declarations.

Advanced Linux Group Permissions: Learning how to securely map system users (jenkins) to host daemons (docker.sock) using precise user-group mappings.

Overcoming Proxy and CORS Roadblocks: Mastering Jenkins initialization logic (init.groovy.d) to bypass browser network blocks and pre-configure server parameters before the UI even opens.

Cloud Storage Integration: Integrating microservices with an S3 object storage API layer (MinIO) using native Python helper modules (boto3).

Container Hardening: Setting up strict container security protocols by switching executions to restricted non-root runtime profiles (appuser).
