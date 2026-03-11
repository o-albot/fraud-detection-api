"""
Модуль с классами модели для детекции мошенничества
"""

import pandas as pd
import numpy as np

class DecisionTree:
    """
    Простая реализация дерева решений для бинарной классификации
    """
    def __init__(self, tree_data=None):
        self.tree_data = tree_data
        self.feature_names = [
            'amount', 'hour_of_day', 'day_of_week', 'distance_from_home',
            'distance_from_last_transaction', 'ratio_to_median_purchase_price',
            'repeat_retailer', 'used_chip', 'used_pin_number', 'online_order'
        ]
        
    def predict(self, X):
        """
        Предсказание для каждого образца
        """
        if isinstance(X, pd.DataFrame):
            X = X.values
        elif isinstance(X, dict):
            X = np.array([[X[f] for f in self.feature_names]])
        
        n_samples = X.shape[0]
        predictions = np.zeros(n_samples)
        
        for i in range(n_samples):
            predictions[i] = self._predict_single(X[i])
        
        return predictions
    
    def _predict_single(self, x):
        """Предсказание для одного образца"""
        node = self.tree_data
        while 'left' in node and 'right' in node:
            feature_idx = node['feature']
            threshold = node['threshold']
            
            if x[feature_idx] <= threshold:
                node = node['left']
            else:
                node = node['right']
        
        return node.get('prediction', 0)


class SimpleRandomForest:
    """
    Простая реализация RandomForest для бинарной классификации
    """
    
    def __init__(self, trees=None, feature_names=None):
        self.trees = trees if trees else []
        self.feature_names = feature_names if feature_names else [
            'amount', 'hour_of_day', 'day_of_week', 'distance_from_home',
            'distance_from_last_transaction', 'ratio_to_median_purchase_price',
            'repeat_retailer', 'used_chip', 'used_pin_number', 'online_order'
        ]
        self.n_classes = 2
        
    def predict_proba(self, X):
        """
        Предсказание вероятностей для каждого класса
        X: pandas DataFrame или dict
        """
        if isinstance(X, dict):
            X = pd.DataFrame([X])
        elif isinstance(X, list):
            X = pd.DataFrame(X, columns=self.feature_names)
        
        # Убеждаемся в правильном порядке признаков
        if self.feature_names:
            X = X[self.feature_names]
        
        # Получаем предсказания от каждого дерева
        n_samples = len(X)
        predictions = np.zeros((n_samples, self.n_classes))
        
        for tree in self.trees:
            tree_preds = tree.predict(X)
            for i in range(n_samples):
                predictions[i, int(tree_preds[i])] += 1
        
        # Нормализуем в вероятности
        predictions = predictions / len(self.trees)
        
        return predictions
    
    def predict(self, X):
        """Бинарное предсказание (0 или 1)"""
        proba = self.predict_proba(X)
        return (proba[:, 1] >= 0.5).astype(int)