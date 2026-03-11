#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Деплой Fraud Detection API в Kubernetes${NC}"
echo -e "${GREEN}========================================${NC}"

# Проверка подключения к кластеру
echo -e "${YELLOW}🔍 Проверка подключения к кластеру...${NC}"
kubectl cluster-info
if [ $? -ne 0 ]; then
    echo "❌ Не удалось подключиться к кластеру"
    exit 1
fi

# Создание namespace если не существует
echo -e "${YELLOW}📦 Создание namespace...${NC}"
kubectl create namespace fraud-detection --dry-run=client -o yaml | kubectl apply -f -

# Применение ConfigMap
echo -e "${YELLOW}📝 Применение ConfigMap...${NC}"
kubectl apply -f configmap.yaml

# Применение Deployment
echo -e "${YELLOW}🚀 Применение Deployment...${NC}"
kubectl apply -f deployment.yaml

# Применение Service
echo -e "${YELLOW}🌐 Применение Service...${NC}"
kubectl apply -f service.yaml

# Применение Ingress (если есть)
if [ -f ingress.yaml ]; then
    echo -e "${YELLOW}🛣️ Применение Ingress...${NC}"
    kubectl apply -f ingress.yaml
fi

# Ожидание запуска подов
echo -e "${YELLOW}⏳ Ожидание запуска подов...${NC}"
kubectl wait --for=condition=ready pod -l app=fraud-detection-api --timeout=60s

# Проверка статуса
echo -e "${YELLOW}📊 Статус деплоя:${NC}"
kubectl get pods -l app=fraud-detection-api
kubectl get svc fraud-detection-api

# Получение внешнего IP (если есть LoadBalancer)
EXTERNAL_IP=$(kubectl get svc fraud-detection-api-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
if [ ! -z "$EXTERNAL_IP" ]; then
    echo -e "${GREEN}✅ Внешний IP: $EXTERNAL_IP${NC}"
    echo -e "${GREEN}📝 Тест: curl http://$EXTERNAL_IP/health${NC}"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Деплой завершен успешно!${NC}"
echo -e "${GREEN}========================================${NC}"