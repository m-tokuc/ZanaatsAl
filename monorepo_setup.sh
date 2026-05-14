#!/bin/bash
set -e

echo "Starting Monorepo Organization..."

# Backend dosyalarını taşı
git mv main.py orchestrator_service.py serper_service.py vision_test.py api_contract.py .env .env.example ipad_case.jpeg backend/ || echo "Some backend files may not exist, continuing..."

# Frontend dosyalarını taşı
git mv lib android ios linux macos test web windows pubspec.yaml pubspec.lock analysis_options.yaml .metadata frontend/ || echo "Some frontend files may not exist, continuing..."

# Değişiklikleri ekle
git add .gitignore
git add backend/
git add frontend/

# Commit ve Push
git commit -m "feat(project): Backend ve Frontend monorepo yapısında birleştirildi ve klasörler organize edildi. Agentic workflow entegrasyonu hazır."
git push origin dev

echo "Monorepo setup completed successfully!"
