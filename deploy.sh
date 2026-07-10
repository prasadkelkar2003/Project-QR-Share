#!/bin/bash
set -e

echo "🧹 Pre-cleaning lingering architecture caches..."
kubectl delete deployment photo-share-deployment --ignore-not-found=true
ctr -n=k8s.io images remove docker.io/library/photo-share:local 2>/dev/null || true

echo "🐳 Compiling updated application binaries locally..."
docker build -t photo-share:local .

echo "📦 Transferring image tarball to containerd internal registry namespace..."
docker save photo-share:local -o photo-share.tar
ctr -n=k8s.io images import photo-share.tar
rm -f photo-share.tar

echo "🔒 Applying Umpire Access Keys & Secrets..."
kubectl apply -f k8s/01-secrets.yaml

echo "💾 Orchestrating Cloud-Mimic MinIO Engine..."
kubectl apply -f k8s/02-minio.yaml

echo "⏳ Verifying MinIO Pod Status..."
kubectl wait --for=condition=ready pod -l app=minio --timeout=90s

echo "⚙️ Creating S3 Data Bucket target allocation..."
MINIO_POD=$(kubectl get pods -l app=minio -o jsonpath='{.items[0].metadata.name}')
until kubectl exec $MINIO_POD -- mc mb /data/wedding-photos 2>/dev/null || echo "Target bucket ready."; do
    echo "Waiting for storage API layer to settle..."
    sleep 2
done

echo "🚀 Rolling Out Stateless Application Nodes..."
kubectl apply -f k8s/03-app.yaml

echo "⏳ Verification check for Application Node startup..."
kubectl wait --for=condition=ready pod -l app=photo-share --timeout=90s

echo "🏁 Infrastructure Pipeline Active!"
kubectl get pods,svc
