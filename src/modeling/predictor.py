import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import json

class PropertyPredictor:
    """Trains models and makes predictions for property prices."""
    
    def __init__(self, data_path, model_dir):
        self.data_path = data_path
        self.model_dir = model_dir
        self.best_model = None
        self.model_columns = None
        
    def prepare_data(self):
        df = pd.read_csv(self.data_path)
        
        # Fill missing numeric values
        df['floor'] = df.apply(lambda r: 0 if r['property_type'] == 'ที่ดิน' else r['floor'], axis=1)
        df = df.dropna(subset=['price_thb', 'area_sqm']) # Essential cols
        df = df.fillna({'bedrooms': 1, 'bathrooms': 1, 'floor': 1, 'age_days': 0})
        
        # One-hot encoding
        features = df[['area_sqm', 'bedrooms', 'bathrooms', 'floor', 'zone', 'property_type', 'has_bts', 'age_days']]
        features = pd.get_dummies(features, columns=['zone', 'property_type'])
        
        X = features
        y = df['price_thb']
        self.model_columns = list(X.columns)
        
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def train_and_evaluate(self):
        print("Starting model training...")
        X_train, X_test, y_train, y_test = self.prepare_data()
        
        models = {
            'Linear Regression': LinearRegression(),
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=200, random_state=42)
        }
        
        results = {}
        best_r2 = -float('inf')
        best_name = ""
        
        for name, model in models.items():
            print(f"Training {name}...")
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            
            mae = mean_absolute_error(y_test, preds)
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            r2 = r2_score(y_test, preds)
            
            results[name] = {'MAE': mae, 'RMSE': rmse, 'R2': r2}
            
            if r2 > best_r2:
                best_r2 = r2
                self.best_model = model
                best_name = name
                
        print(f"Best model: {best_name} (R2: {best_r2:.4f})")
        
        # Save artifacts
        os.makedirs(self.model_dir, exist_ok=True)
        joblib.dump(self.best_model, os.path.join(self.model_dir, 'best_model.pkl'))
        joblib.dump(self.model_columns, os.path.join(self.model_dir, 'model_columns.pkl'))
        
        with open(os.path.join(self.model_dir, 'evaluation.json'), 'w') as f:
            json.dump(results, f, indent=4)
            
        # Feature importance if available
        if hasattr(self.best_model, 'feature_importances_'):
            fi = dict(zip(self.model_columns, self.best_model.feature_importances_))
            with open(os.path.join(self.model_dir, 'feature_importance.json'), 'w') as f:
                json.dump(fi, f, indent=4)
                
        return results

    @classmethod
    def load_model(cls, model_dir):
        inst = cls(None, model_dir)
        inst.best_model = joblib.load(os.path.join(model_dir, 'best_model.pkl'))
        inst.model_columns = joblib.load(os.path.join(model_dir, 'model_columns.pkl'))
        return inst
        
    def predict(self, area_sqm, bedrooms, bathrooms, floor, zone, property_type, has_bts):
        # Create input df
        input_data = pd.DataFrame([{
            'area_sqm': area_sqm, 'bedrooms': bedrooms, 'bathrooms': bathrooms,
            'floor': floor, 'has_bts': has_bts, 'age_days': 0,
            f'zone_{zone}': 1, f'property_type_{property_type}': 1
        }])
        
        # Reindex to match training columns
        input_data = input_data.reindex(columns=self.model_columns, fill_value=0)
        return self.best_model.predict(input_data)[0]

if __name__ == "__main__":
    p = PropertyPredictor('../../data/transformed/final_listings.csv', '../../models')
    p.train_and_evaluate()
