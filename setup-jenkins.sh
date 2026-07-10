cat <<EOF > setup-jenkins.sh
#!/bin/bash
set -e

# Verify that the user actually passed the token into the terminal session environment
if [ -z "\$DOCKER_HUB_PAT" ]; then
    echo "❌ Error: DOCKER_HUB_PAT environment variable is not set!"
    echo "💡 Run this first: export DOCKER_HUB_PAT='your_actual_token_here'"
    exit 1
fi

echo "⚙️ Automatically provisioning Jenkins credentials..."

USER="prad2003"
CRED_ID="docker-hub-credentials"

echo "📥 Fetching Jenkins CLI binaries..."
curl -sS http://localhost:8080/jnlpJars/jenkins-cli.jar -o jenkins-cli.jar

cat <<GROOVY > add_cred.groovy
import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*

def domain = Domain.global()
def store = Jenkins.get().getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

def credential = new UsernamePasswordCredentialsImpl(
  CredentialsScope.GLOBAL,
  "${CRED_ID}",
  "Docker Hub Automation Token",
  "${USER}",
  "\$DOCKER_HUB_PAT" # 🧠 Injected dynamically from your secure environment variable
)

store.addCredentials(domain, credential)
println "✅ Credential '${CRED_ID}' injected successfully!"
GROOVY

echo "🚀 Executing credential script injection via Jenkins CLI..."
java -jar jenkins-cli.jar -s http://localhost:8080/ groovy = < add_cred.groovy

rm -f add_cred.groovy jenkins-cli.jar
echo "🏁 Provisioning Complete!"
EOF

chmod +x setup-jenkins.sh
