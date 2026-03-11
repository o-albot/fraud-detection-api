# Kubernetes манифесты для Fraud Detection API

## Файлы:
- `deployment.yaml` - Deployment и HPA
- `service.yaml` - Services (ClusterIP и LoadBalancer)
- `ingress.yaml` - Ingress для внешнего доступа
- `configmap.yaml` - Конфигурация
- `kustomization.yaml` - Kustomize для управления
- `deploy.sh` - Скрипт деплоя
- `test-k8s.sh` - Скрипт тестирования

## Быстрый старт:

```bash
# Применить все манифесты
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Или через kustomize
kubectl apply -k .

# Проверить статус
kubectl get pods
kubectl get svc
kubectl get hpa

# Протестировать
./test-k8s.sh