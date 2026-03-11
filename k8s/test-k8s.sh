#!/bin/bash

# Получаем IP сервиса
SERVICE_IP=$(kubectl get svc fraud-detection-api -o jsonpath='{.spec.clusterIP}')
SERVICE_LB_IP=$(kubectl get svc fraud-detection-api-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)

echo "Тестирование API в Kubernetes"
echo "=============================="

# Тест 1: Health check
echo -e "\n1. Health check:"
if [ ! -z "$SERVICE_LB_IP" ]; then
    curl -s http://$SERVICE_LB_IP/health | jq .
else
    # Пробрасываем порт для теста
    kubectl port-forward svc/fraud-detection-api 8000:8000 &
    PF_PID=$!
    sleep 2
    curl -s http://localhost:8000/health | jq .
    kill $PF_PID
fi

# Тест 2: Информация о модели
echo -e "\n2. Информация о модели:"
if [ ! -z "$SERVICE_LB_IP" ]; then
    curl -s http://$SERVICE_LB_IP/info | jq .
else
    kubectl port-forward svc/fraud-detection-api 8000:8000 &
    PF_PID=$!
    sleep 2
    curl -s http://localhost:8000/info | jq .
    kill $PF_PID
fi

# Тест 3: Предсказание
echo -e "\n3. Предсказание:"
DATA='{
    "amount": 317.31,
    "hour_of_day": 15,
    "day_of_week": 6,
    "distance_from_home": 9.01,
    "distance_from_last_transaction": 2.84,
    "ratio_to_median_purchase_price": 0.39,
    "repeat_retailer": 1,
    "used_chip": 1,
    "used_pin_number": 0,
    "online_order": 0
}'

if [ ! -z "$SERVICE_LB_IP" ]; then
    curl -s -X POST http://$SERVICE_LB_IP/predict \
        -H "Content-Type: application/json" \
        -d "$DATA" | jq .
else
    kubectl port-forward svc/fraud-detection-api 8000:8000 &
    PF_PID=$!
    sleep 2
    curl -s -X POST http://localhost:8000/predict \
        -H "Content-Type: application/json" \
        -d "$DATA" | jq .
    kill $PF_PID
fi