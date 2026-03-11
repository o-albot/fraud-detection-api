#!/usr/bin/env python3
"""
Тесты для Fraud Detection API
"""

import requests
import json
import time
import pytest
import os

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

class TestFraudAPI:
    
    def setup_method(self):
        """Подготовка перед каждым тестом"""
        # Ждем пока API запустится
        time.sleep(2)
    
    def test_health_endpoint(self):
        """Тест health check"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] == True
    
    def test_info_endpoint(self):
        """Тест info endpoint"""
        response = requests.get(f"{BASE_URL}/info")
        assert response.status_code == 200
        data = response.json()
        assert data["model_type"] == "SimpleRandomForest"
        assert data["num_trees"] == 20
        assert "feature_names" in data
    
    def test_predict_endpoint(self):
        """Тест предсказания"""
        test_data = {
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
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "fraud_probability" in data
        assert "is_fraud" in data
        assert isinstance(data["fraud_probability"], float)
        assert isinstance(data["is_fraud"], bool)
    
    def test_predict_batch_endpoint(self):
        """Тест пакетного предсказания"""
        test_data = {
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
        }
        
        response = requests.post(
            f"{BASE_URL}/predict/batch",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert data["count"] == 2
        assert len(data["predictions"]) == 2
    
    def test_invalid_data(self):
        """Тест с некорректными данными"""
        invalid_data = {
            "amount": "not_a_number",
            "hour_of_day": 25,  # Невалидный час
            "day_of_week": 7,    # Невалидный день
            "distance_from_home": 9.01,
            "distance_from_last_transaction": 2.84,
            "ratio_to_median_purchase_price": 0.39,
            "repeat_retailer": 2,  # Невалидное значение
            "used_chip": 1,
            "used_pin_number": 0,
            "online_order": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json=invalid_data
        )
        assert response.status_code == 422  # Validation error