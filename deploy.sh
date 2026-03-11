#!/bin/bash

echo "🚀 Развертывание Minimal Fraud Detection API"

if [ ! -f "model.pkl" ]; then
    echo "❌ Файл model.pkl не найден!"
    exit 1
fi

echo "🐳 Запуск контейнера..."
docker-compose up -d

echo "✅ API запущено на порту 8000"
echo "📝 Проверка: curl http://localhost:8000/health"
