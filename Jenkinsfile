pipeline {
    agent any

    environment {
        DOCKER_HUB_USER   = 'prad2003'
        IMAGE_NAME        = 'photo-share'
        IMAGE_TAG         = "${BUILD_NUMBER}" // Tracks each build number sequentially
        KUBECONFIG_PATH   = "/var/lib/jenkins/.kube/config"
    }

    stages {
        stage('📥 Fetch Source') {
            steps {
                cleanWs() // Wipes workspace cleanly before pulling down fresh code layers
                checkout scm
            }
        }

        stage('🐳 Build Container Engine') {
            steps {
                script {
                    echo "Compiling code layers into container binary..."
                    sh "docker build -t ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} ."
                    sh "docker build -t ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest ."
                }
            }
        }

        stage('🚀 Push to Docker Hub') {
            steps {
                script {
                    // Securely extracts credentials from Jenkins UI Store vault
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-hub-credentials', 
                        usernameVariable: 'REGISTRY_USER', 
                        passwordVariable: 'REGISTRY_PASS'
                    )]) {
                        echo "Authenticating to Docker Hub..."
                        sh "echo '${REGISTRY_PASS}' | docker login -u '${REGISTRY_USER}' --password-stdin"
                        
                        echo "Pushing built container artifacts..."
                        sh "docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
                        sh "docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest"
                    }
                }
            }
        }

        stage('☸️ Deploy to Killercoda Cluster') {
            steps {
                script {
                    echo "Injecting builds dynamically into infrastructure layer..."
                    
                    // 1. Patches manifest to map the newly built numeric container tag version
                    sh "sed -i 's|image: .*photo-share.*|image: ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}|g' 03-app.yaml"
                    
                    // 2. Adjusts image pull policies so Kubernetes pulls from remote Docker Hub instead of looking locally
                    sh "sed -i 's|imagePullPolicy: .*|imagePullPolicy: Always|g' 03-app.yaml"
                    
                    // 3. Applies core configurations and isolated private storage infrastructure layers
                    sh "export KUBECONFIG=${KUBECONFIG_PATH} && kubectl apply -f 01-secrets.yaml"
                    sh "export KUBECONFIG=${KUBECONFIG_PATH} && kubectl apply -f 02-minio.yaml"
                    
                    // 4. Waits for the MinIO storage backend engine components to establish a healthy status flag
                    sh "export KUBECONFIG=${KUBECONFIG_PATH} && kubectl wait --for=condition=ready pod -l app=minio --timeout=60s"
                    
                    // 5. Deploys the multi-tenant SaaS application layer and performs a smooth rolling update
                    echo "Rolling out dynamic cloud architecture..."
                    sh "export KUBECONFIG=${KUBECONFIG_PATH} && kubectl apply -f 03-app.yaml"
                    sh "export KUBECONFIG=${KUBECONFIG_PATH} && kubectl rollout restart deployment/photo-share-deployment"
                }
            }
        }
    }

    post {
        success {
            echo "✅ Deployment Successful! Multi-bucket platform is live on NodePort 30080."
        }
        failure {
            echo "❌ Pipeline failure encountered during system rollout."
        }
    }
}
