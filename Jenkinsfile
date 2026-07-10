pipeline {
    agent any

    environment {
        // 🐳 Your Real Docker Hub Configurations
        DOCKER_HUB_USER = 'prad2003'
        IMAGE_NAME      = 'photo-share'
        IMAGE_TAG       = "${BUILD_NUMBER}" // Automatically tracks each build number sequentially
    }

    stages {
        stage('📥 Fetch Source') {
            steps {
                cleanWs() // Wipes workspace cleanly before pulling down code
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
                    // 🔒 Securely logs into Docker Hub using credentials stored in Jenkins Manager
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_PASS')]) {
                        sh "echo '${REGISTRY_PASS}' | docker login -u '${REGISTRY_USER}' --password-stdin"
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
                    
                    // 1. 🛠️ FIXED: Uses a regex wildcard to match ANY previous image string and swap it with the fresh build tag
                    sh "sed -i 's|image: .*photo-share.*|image: ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}|g' k8s/03-app.yaml"
                    
                    // 2. 🛠️ FIXED: Uses a regex wildcard to match ANY pull policy string and force it to Always
                    sh "sed -i 's|imagePullPolicy: .*|imagePullPolicy: Always|g' k8s/03-app.yaml"
                    
                    // 3. Directly target the local node cluster using the host credentials
                    sh "kubectl apply -f k8s/01-secrets.yaml"
                    sh "kubectl apply -f k8s/02-minio.yaml"
                    
                    // 4. Ensure internal S3 target allocation bucket configuration maps are alive
                    sh "kubectl wait --for=condition=ready pod -l app=minio --timeout=60s"
                    sh """
                       MINIO_POD=\$(kubectl get pods -l app=minio -o jsonpath='{.items[0].metadata.name}')
                       kubectl exec \$MINIO_POD -- mc mb /data/wedding-photos || echo 'Target bucket allocated.'
                    """
                    
                    // 5. Update application deployment live parameters
                    sh "kubectl apply -f k8s/03-app.yaml"
                    sh "kubectl rollout restart deployment/photo-share-deployment"
                }
            }
        }
    }

    post {
        success {
            echo "✅ Deployment Successful! Platform is live on Port 30080."
        }
        failure {
            echo "❌ Pipeline failure encountered during system rollout."
        }
    }
}
