#!/usr/bin/env python3

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    print(f"Health: {r.status_code}")
    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2))
    return r.status_code == 200

def test_info():
    r = requests.get(f"{BASE_URL}/info")
    print(f"Info: {r.status_code}")
    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2))
    return r.status_code == 200

def test_predict():
    # Отправляем поля напрямую, без обертки "transaction"
    data = {
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
    }
    
    print(f"📤 Отправка данных: {json.dumps(data, indent=2)}")
    
    r = requests.post(
        f"{BASE_URL}/predict",
        json=data,  # Отправляем data напрямую, без обертки
        headers={"Content-Type": "application/json"}
    )
    print(f"Predict: {r.status_code}")
    if r.status_code == 200:
        print("✅ Успех!")
        print(json.dumps(r.json(), indent=2))
    else:
        print("❌ Ошибка:")
        print(json.dumps(r.json(), indent=2))
    return r.status_code == 200

def main():
    print("="*50)
    print("Тестирование API")
    print("="*50)
    
    tests = [
        ("Health check", test_health),
        ("Model info", test_info),
        ("Prediction", test_predict)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"Ошибка: {e}")
            results.append((name, False))
    
    print("\n" + "="*50)
    print("Результаты:")
    print("="*50)
    
    all_passed = True
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Все тесты пройдены!")
        return 0
    else:
        print("\n❌ Некоторые тесты не пройдены")
        return 1

if __name__ == "__main__":
    sys.exit(main())