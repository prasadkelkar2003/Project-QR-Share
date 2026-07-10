#!/bin/bash
set -e

# 1. Safety Check: Verify the token environment variable is in memory
if [ -z "$DOCKER_HUB_PAT" ]; then
    echo "❌ Error: DOCKER_HUB_PAT environment variable is not set!"
    echo "💡 Run this first: export DOCKER_HUB_PAT='your_actual_token_here'"
    exit 1
fi

echo "⚙️ Automatically provisioning Jenkins credentials..."
USER="prad2003"
CRED_ID="docker-hub-credentials"

# 2. Fetch the CLI binaries directly from the local container server instance
echo "📥 Fetching Jenkins CLI binaries..."
curl -sS http://localhost:8080/jnlpJars/jenkins-cli.jar -o jenkins-cli.jar

# 3. Create the clean payload document
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
  "${DOCKER_HUB_PAT}"
)

store.addCredentials(domain, credential)
println "✅ Credential '${CRED_ID}' injected successfully!"
GROOVY

# 4. Fire the execution runtime block
echo "🚀 Executing credential script injection via Jenkins CLI..."
java -jar jenkins-cli.jar -s http://localhost:8080/ groovy = < add_cred.groovy

# 5. Clean up temporary configurations
rm -f add_cred.groovy jenkins-cli.jar
echo "🏁 Provisioning Complete!"
