pipeline {
    agent any

    environment {
        REGISTRY          = "prad2003"
        IMAGE_NAME        = "photo-share"
        BUILD_TAG         = "${BUILD_NUMBER}"
        KUBECONFIG_PATH   = "/var/lib/jenkins/.kube/config"
    }

    stages {
        stage('📥 Fetch Source') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('🐳 Build Container Engine') {
            steps {
                script {
                    echo "Compiling code layers into container binary..."
                    sh "docker build -t ${REGISTRY}/${IMAGE_NAME}:${BUILD_TAG} ."
                    sh "docker build -t ${REGISTRY}/${IMAGE_NAME}:latest ."
                }
            }
        }

        stage('🚀 Push to Docker Hub') {
            steps {
                script {
                    // This block maps your UI credentials securely to environment variables
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-hub-credentials', 
                        passwordVariable: 'DOCKER_PASSWORD', 
                        usernameVariable: 'DOCKER_USER'
                    )]) {
                        echo "Authenticating to Docker Hub..."
                        sh "echo ${DOCKER_PASSWORD} | docker login -u ${DOCKER_USER} --password-stdin"
                        
                        echo "Pushing built container artifacts..."
                        sh "docker push ${REGISTRY}/${IMAGE_NAME}:${BUILD_TAG}"
                        sh "docker push ${REGISTRY}/${IMAGE_NAME}:latest"
                    }
                }
            }
        }

        stage('☸️ Deploy to Killercoda Cluster') {
            steps {
                script {
                    echo "Rolling out dynamic cloud architecture..."
                    // Injected environment variables patch manifests dynamically on the fly
                    sh "export KUBECONFIG=${KUBECONFIG_PATH} && ./deploy.sh"
                }
            }
        }
    }

    post {
        success {
            echo "✅ Multi-bucket GitOps rollout complete! System online."
        }
        failure {
            echo "❌ Pipeline failure encountered during system rollout."
        }
    }
}
