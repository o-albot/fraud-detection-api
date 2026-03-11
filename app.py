# Вставьте сюда полный код app.py из предыдущего раздела
"""
Минимальное API для детекции мошеннических транзакций
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import numpy as np
import uvicorn
from typing import Optional, List
import os

# Импортируем классы модели
from model import SimpleRandomForest, DecisionTree

# ============ МОДЕЛЬ ДАННЫХ ============
class Transaction(BaseModel):
    amount: float = Field(..., description="Сумма транзакции")
    hour_of_day: int = Field(..., ge=0, le=23, description="Час дня (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="День недели (0-6)")
    distance_from_home: float = Field(..., description="Расстояние от дома")
    distance_from_last_transaction: float = Field(..., description="Расстояние от последней транзакции")
    ratio_to_median_purchase_price: float = Field(..., description="Отношение к медианной цене")
    repeat_retailer: int = Field(..., ge=0, le=1, description="Повторный продавец (0/1)")
    used_chip: int = Field(..., ge=0, le=1, description="Использован чип (0/1)")
    used_pin_number: int = Field(..., ge=0, le=1, description="Использован PIN (0/1)")
    online_order: int = Field(..., ge=0, le=1, description="Онлайн заказ (0/1)")


class PredictionResponse(BaseModel):
    fraud_probability: float
    is_fraud: bool
    transaction_id: Optional[str] = None


class BatchPredictionRequest(BaseModel):
    transactions: List[Transaction]


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    count: int


# ============ ИНИЦИАЛИЗАЦИЯ ============
app = FastAPI(
    title="Fraud Detection API (Minimal)",
    description="API для детекции мошеннических транзакций",
    version="1.0.0"
)

# Загружаем модель
MODEL_PATH = os.getenv('MODEL_PATH', 'model.pkl')
print(f"🔍 Загрузка модели из: {MODEL_PATH}")

try:
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Файл {MODEL_PATH} не найден!")
        print(f"📁 Содержимое директории: {os.listdir('.')}")
        MODEL_LOADED = False
    else:
        print(f"✅ Файл модели найден, размер: {os.path.getsize(MODEL_PATH)} байт")
        
        # Загружаем модель
        model = joblib.load(MODEL_PATH)
        
        print(f"✅ Модель загружена успешно!")
        print(f"   Тип модели: {type(model).__name__}")
        
        if hasattr(model, 'trees'):
            print(f"   Количество деревьев: {len(model.trees)}")
        
        MODEL_LOADED = True
        
except Exception as e:
    print(f"❌ Ошибка загрузки модели: {e}")
    import traceback
    traceback.print_exc()
    MODEL_LOADED = False


# ============ ЭНДПОИНТЫ ============
@app.get("/")
async def root():
    return {
        "service": "Fraud Detection API",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": MODEL_LOADED
    }


@app.get("/health")
async def health():
    if MODEL_LOADED:
        return {"status": "healthy", "model_loaded": True}
    else:
        return {"status": "degraded", "model_loaded": False}


@app.get("/info")
async def info():
    """Информация о модели"""
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Модель не загружена")
    
    model_info = {
        "model_type": type(model).__name__,
        "num_features": 10
    }
    
    if hasattr(model, 'feature_names'):
        model_info["feature_names"] = model.feature_names
    
    if hasattr(model, 'trees'):
        model_info["num_trees"] = len(model.trees)
    
    return model_info


@app.post("/predict", response_model=PredictionResponse)
async def predict(transaction: Transaction):
    """
    Предсказание для одной транзакции
    """
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Модель не загружена")
    
    try:
        # Конвертируем в DataFrame
        df = pd.DataFrame([transaction.dict()])
        
        # Получаем предсказание
        proba = model.predict_proba(df)[0]
        pred = model.predict(df)[0]
        
        return PredictionResponse(
            fraud_probability=float(proba[1]),
            is_fraud=bool(pred)
        )
        
    except Exception as e:
        print(f"❌ Ошибка предсказания: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """
    Пакетное предсказание для нескольких транзакций
    """
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Модель не загружена")
    
    try:
        # Конвертируем в DataFrame
        transactions = [t.dict() for t in request.transactions]
        df = pd.DataFrame(transactions)
        
        # Получаем предсказания
        probas = model.predict_proba(df)
        preds = model.predict(df)
        
        predictions = []
        for i in range(len(transactions)):
            predictions.append(PredictionResponse(
                fraud_probability=float(probas[i][1]),
                is_fraud=bool(preds[i])
            ))
        
        return BatchPredictionResponse(
            predictions=predictions,
            count=len(predictions)
        )
        
    except Exception as e:
        print(f"❌ Ошибка пакетного предсказания: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ ЗАПУСК ============
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )