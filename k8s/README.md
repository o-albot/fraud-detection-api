# README.md - Развертывание Fraud Detection API в Kubernetes

```markdown
# Fraud Detection API - Развертывание в Kubernetes

## 📋 Содержание
- [Требования](#требования)
- [Получение ID кластера и подсети](#получение-id-кластера-и-подсети)
- [Создание кластера и нод](#создание-кластера-и-нод)
- [Подготовка кластера](#подготовка-кластера)
- [Развертывание приложения](#развертывание-приложения)
- [Проверка работоспособности](#проверка-работоспособности)
- [Доступ к API](#доступ-к-api)
- [Тестирование](#тестирование)
- [Мониторинг и управление](#мониторинг-и-управление)
- [Очистка](#очистка)

## Требования

- ✅ Yandex Cloud CLI (`yc`) установлен и настроен
- ✅ `kubectl` установлен и настроен
- ✅ Публичный Docker образ: `ghcr.io/o-albot/fraud-detection-api:latest`

## Получение ID кластера и подсети

### 1. Получение списка кластеров и их ID

```bash
# Просмотр всех кластеров
yc managed-kubernetes cluster list

# Пример вывода:
# +----------------------+-------------+---------------------+
# |          ID          |    NAME     |     CREATED AT      |
# +----------------------+-------------+---------------------+
# | <cluster_id>         | k8s-cluster | 2026-03-12 08:21:16 |
# +----------------------+-------------+---------------------+

# Сохраните ID кластера (понадобится далее)
export CLUSTER_ID=<your_cluster_id>
```

### 2. Получение списка подсетей и их ID

```bash
# Просмотр всех подсетей
yc vpc subnet list

# Пример вывода:
# +----------------------+-------+----------------------+
# |          ID          | NAME  |        ZONE          |
# +----------------------+-------+----------------------+
# | <subnet_id>          | my-subnet | ru-central1-a        |
# +----------------------+-------+----------------------+

# Сохраните ID подсети (понадобится далее)
export SUBNET_ID=<your_subnet_id>
```

## Создание кластера и нод

### 1. Создание группы узлов (Node Group)

Перед развертыванием приложения необходимо создать группу узлов в кластере с внешними IP для доступа к интернету:

```bash
yc managed-kubernetes node-group create \
  --name fraud-api-nodes \
  --cluster-id <your_cluster_id> \
  --fixed-size 2 \
  --location zone=ru-central1-a \
  --memory 4 \
  --cores 2 \
  --core-fraction 100 \
  --disk-type network-ssd \
  --disk-size 64 \
  --network-interface "subnets=<your_subnet_id>,ipv4-address=nat"
```

**Параметры команды:**
- `--name`: имя группы узлов
- `--cluster-id`: ID кластера (получен на предыдущем шаге)
- `--fixed-size`: количество узлов (2 для отказоустойчивости)
- `--location`: зона доступности
- `--memory`, `--cores`: ресурсы узлов (4 GB RAM, 2 vCPU)
- `--disk-type`, `--disk-size`: тип и размер диска (64 GB SSD)
- `--network-interface`: настройки сети с публичным IP (`ipv4-address=nat`) и ID подсети

### 2. Проверка создания узлов

```bash
# Проверка статуса создания группы
yc managed-kubernetes node-group list --cluster-id <your_cluster_id>

# Ожидаемый вывод:
# +----------------------+------------------+--------------------+---------+------------+
# |          ID          |       NAME       | INSTANCE GROUP ID | STATUS  | NODE COUNT |
# +----------------------+------------------+--------------------+---------+------------+
# | <node_group_id>      | fraud-api-nodes  | <instance_group_id>| RUNNING |     2      |
# +----------------------+------------------+--------------------+---------+------------+
```

## Подготовка кластера

### 1. Проверка подключения к кластеру

```bash
# Проверка нод
kubectl get nodes -o wide

# Ожидаемый вывод:
NAME                        STATUS   ROLES    AGE   VERSION   INTERNAL-IP   EXTERNAL-IP
<node_name_1>               Ready    <none>   93s   v1.32.1   10.128.0.9     <external_ip_1>
<node_name_2>               Ready    <none>   81s   v1.32.1   10.128.0.20    <external_ip_2>
```

**Важно:** Убедитесь, что у нод есть внешние IP (колонка `EXTERNAL-IP`). Это необходимо для скачивания образов из интернета.

### 2. Проверка доступа к интернету из кластера

```bash
# Создание тестового пода
kubectl run test-nginx --image=nginx:latest --restart=Never

# Проверка статуса
kubectl get pod test-nginx -w

# Ожидаемый вывод:
NAME         READY   STATUS    RESTARTS   AGE
test-nginx   1/1     Running   0          10s

# Просмотр логов
kubectl logs test-nginx

# Удаление тестового пода
kubectl delete pod test-nginx
```

## Развертывание приложения

### 1. Клонирование репозитория

```bash
git clone https://github.com/o-albot/fraud-detection-api.git
cd fraud-detection-api/k8s
```

### 2. Применение ConfigMap

```bash
kubectl apply -f configmap.yaml

# Проверка:
kubectl get configmap fraud-detection-api-config
```

### 3. Развертывание приложения

**Важно:** Образ публичный, секрет не требуется!

```bash
# Применение deployment
kubectl apply -f deployment.yaml

# Применение service
kubectl apply -f service.yaml
```

### 4. Мониторинг развертывания

```bash
# Отслеживание создания подов
kubectl get pods -w

# Ожидаемый вывод:
NAME                                   READY   STATUS    RESTARTS   AGE
fraud-detection-api-<hash1>            1/1     Running   0          28s
fraud-detection-api-<hash2>            1/1     Running   0          30s
```

## Проверка работоспособности

### 1. Локальная проверка через port-forward

```bash
# Проброс порта
kubectl port-forward svc/fraud-detection-api 8000:8000 &

# Проверка health endpoint
curl http://localhost:8000/health

# Ожидаемый ответ:
{"status":"healthy","model_loaded":true}

# Проверка info endpoint
curl http://localhost:8000/info

# Ожидаемый ответ:
{
  "model_type": "SimpleRandomForest",
  "num_features": 10,
  "feature_names": [...],
  "num_trees": 20
}

# Завершение port-forward
kill %1
```

### 2. Проверка через LoadBalancer (публичный доступ)

```bash
# Получение внешнего IP
kubectl get svc fraud-detection-api-lb

# Ожидаемый вывод:
NAME                     TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)
fraud-detection-api-lb   LoadBalancer   10.96.202.133   <external_ip>    80:30693/TCP

# Проверка через внешний IP
curl http://<external_ip>/health

# Ожидаемый ответ:
{"status":"healthy","model_loaded":true}
```

## Тестирование API

### 1. Тестовое предсказание

```bash
curl -X POST http://<external_ip>/predict \
  -H "Content-Type: application/json" \
  -d '{
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
```

**Ожидаемый ответ:**
```json
{
  "fraud_probability": 0.0,
  "is_fraud": false,
  "transaction_id": null
}
```

### 2. Пакетное тестирование

```bash
curl -X POST http://<external_ip>/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      {
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
      },
      {
        "amount": 241.07,
        "hour_of_day": 2,
        "day_of_week": 2,
        "distance_from_home": 11.39,
        "distance_from_last_transaction": 7.62,
        "ratio_to_median_purchase_price": 1.09,
        "repeat_retailer": 0,
        "used_chip": 1,
        "used_pin_number": 0,
        "online_order": 1
      }
    ]
  }'
```

## Мониторинг и управление

### Просмотр логов

```bash
# Логи всех подов приложения
kubectl logs -l app=fraud-detection-api

# Логи конкретного пода
kubectl logs fraud-detection-api-<hash>

# Непрерывное наблюдение за логами
kubectl logs -l app=fraud-detection-api -f
```

### Масштабирование

```bash
# Ручное масштабирование
kubectl scale deployment fraud-detection-api --replicas=3

# Автоматическое масштабирование (настроено в HPA)
kubectl get hpa -w
```

### Проверка статуса

```bash
# Все ресурсы
kubectl get all

# Поды с деталями
kubectl get pods -o wide

# Сервисы
kubectl get svc

# События
kubectl get events --sort-by='.lastTimestamp'
```

## Очистка

### Удаление приложения

```bash
# Удаление всех ресурсов
kubectl delete deployment fraud-detection-api
kubectl delete service fraud-detection-api
kubectl delete service fraud-detection-api-lb
kubectl delete configmap fraud-detection-api-config

# Проверка удаления
kubectl get all
```

### Удаление группы узлов

```bash
# Удаление группы узлов
yc managed-kubernetes node-group delete --name fraud-api-nodes
```

### Полная очистка кластера (опционально)

```bash
# Удаление кластера
yc managed-kubernetes cluster delete --id <your_cluster_id>
```

## 📊 Структура манифестов

```
k8s/
├── configmap.yaml          # Конфигурация приложения
├── deployment.yaml         # Deployment и HPA
├── service.yaml            # ClusterIP и LoadBalancer сервисы
└── README.md               # Документация
```

## 🔗 Полезные ссылки

- **Публичный образ:** `ghcr.io/o-albot/fraud-detection-api:latest`
- **Репозиторий:** https://github.com/o-albot/fraud-detection-api
- **Документация API:** `http://<external_ip>/docs`

## ✅ Чек-лист развертывания

- [ ] Yandex Cloud CLI настроен (`yc config list`)
- [ ] Получен ID кластера (`yc managed-kubernetes cluster list`)
- [ ] Получен ID подсети (`yc vpc subnet list`)
- [ ] Группа узлов создана с публичными IP
- [ ] Кластер доступен (`kubectl cluster-info`)
- [ ] Ноды в статусе Ready (`kubectl get nodes`)
- [ ] Ноды имеют внешние IP (`kubectl get nodes -o wide`)
- [ ] ConfigMap создан (`kubectl get configmap`)
- [ ] Deployment применен (`kubectl get deployment`)
- [ ] Поды в статусе Running (`kubectl get pods`)
- [ ] Сервисы созданы (`kubectl get svc`)
- [ ] LoadBalancer получил внешний IP
- [ ] API отвечает на запросы (`curl <external_ip>/health`)

---

**Развертывание успешно завершено!** 🚀
```