import os
import sys
import json
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
import joblib

app = Flask(__name__)

# Config paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'transformed', 'final_listings.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'best_model.pkl')
MODEL_COLS_PATH = os.path.join(BASE_DIR, 'models', 'model_columns.pkl')
REPORT_PATH = os.path.join(BASE_DIR, 'data', 'pipeline_report.json')
EVAL_PATH = os.path.join(BASE_DIR, 'models', 'evaluation.json')
FI_PATH = os.path.join(BASE_DIR, 'models', 'feature_importance.json')

# Cache loaded objects
_data_cache = None
_model_cache = None
_columns_cache = None

def load_data():
    global _data_cache
    if _data_cache is not None:
        return _data_cache
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_csv(DATA_PATH)
            _data_cache = df
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
    return pd.DataFrame()

def load_model():
    global _model_cache, _columns_cache
    if _model_cache is not None:
        return _model_cache, _columns_cache
    if os.path.exists(MODEL_PATH):
        try:
            _model_cache = joblib.load(MODEL_PATH)
            if os.path.exists(MODEL_COLS_PATH):
                _columns_cache = joblib.load(MODEL_COLS_PATH)
            return _model_cache, _columns_cache
        except Exception as e:
            print(f"Error loading model: {e}")
    return None, None

def load_json_file(path):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
    return {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    df = load_data()
    if df.empty:
        return jsonify({"error": "Data not available. Please run the pipeline first."})
    
    total_listings = len(df)
    avg_price = float(df['price_thb'].mean()) if 'price_thb' in df.columns else 0
    median_price = float(df['price_thb'].median()) if 'price_thb' in df.columns else 0
    avg_price_per_sqm = float(df['price_per_sqm'].mean()) if 'price_per_sqm' in df.columns else 0
    
    by_type = []
    if 'property_type' in df.columns and 'price_thb' in df.columns:
        type_group = df.groupby('property_type').agg(
            count=('price_thb', 'count'),
            avg_price=('price_thb', 'mean')
        ).reset_index()
        if 'price_per_sqm' in df.columns:
            type_ppsqm = df.groupby('property_type')['price_per_sqm'].mean().reset_index()
            type_ppsqm.columns = ['property_type', 'avg_price_per_sqm']
            type_group = type_group.merge(type_ppsqm, on='property_type', how='left')
        by_type = type_group.to_dict('records')
        
    by_zone = []
    if 'zone' in df.columns and 'price_thb' in df.columns:
        zone_group = df.groupby('zone').agg(
            count=('price_thb', 'count'),
            avg_price=('price_thb', 'mean')
        ).reset_index()
        by_zone = zone_group.to_dict('records')
    
    # Source breakdown
    by_source = []
    if 'source' in df.columns:
        src_group = df['source'].value_counts().reset_index()
        src_group.columns = ['source', 'count']
        by_source = src_group.to_dict('records')

    report = load_json_file(REPORT_PATH)
    
    return jsonify({
        'total_listings': int(total_listings),
        'avg_price': avg_price,
        'avg_price_per_sqm': avg_price_per_sqm,
        'median_price': median_price,
        'by_type': by_type,
        'by_zone': by_zone,
        'by_source': by_source,
        'cleaning_stats': report.get('cleaning', {}),
    })

@app.route('/api/listings')
def listings():
    df = load_data()
    if df.empty:
        return jsonify({"listings": [], "total": 0, "page": 1, "pages": 0})
        
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    prop_type = request.args.get('type')
    zone = request.args.get('zone')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort_by', 'price_thb')
    search = request.args.get('search', '')
    
    # Filtering
    if prop_type and prop_type != 'all' and 'property_type' in df.columns:
        df = df[df['property_type'] == prop_type]
    if zone and zone != 'all' and 'zone' in df.columns:
        df = df[df['zone'] == zone]
    if min_price is not None and 'price_thb' in df.columns:
        df = df[df['price_thb'] >= min_price]
    if max_price is not None and 'price_thb' in df.columns:
        df = df[df['price_thb'] <= max_price]
    if search and 'title' in df.columns:
        df = df[df['title'].str.contains(search, case=False, na=False)]
        
    # Sorting
    if sort_by and sort_by in df.columns:
        ascending = sort_by != 'price_thb'
        df = df.sort_values(by=sort_by, ascending=ascending)
        
    total = len(df)
    pages = max(1, (total + per_page - 1) // per_page)
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Select columns for the table
    display_cols = ['id', 'title', 'property_type', 'location', 'zone', 'price_thb', 
                    'area_sqm', 'price_per_sqm', 'bedrooms', 'bathrooms', 'floor', 'source']
    available_cols = [c for c in display_cols if c in df.columns]
    
    paginated = df.iloc[start_idx:end_idx][available_cols].fillna("").to_dict('records')
    
    return jsonify({
        "listings": paginated,
        "total": total,
        "page": page,
        "pages": pages
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    model, model_columns = load_model()
    data = request.json
    
    area_sqm = float(data.get('area_sqm', 50))
    bedrooms = float(data.get('bedrooms', 1))
    bathrooms = float(data.get('bathrooms', 1))
    floor_val = float(data.get('floor', 1))
    zone = data.get('zone', 'CBD')
    property_type = data.get('property_type', 'คอนโด')
    has_bts = int(data.get('has_bts', 0))
    
    if model is None or model_columns is None:
        # Fallback estimation based on simple heuristics
        zone_multiplier = {'CBD': 1.5, 'Inner City': 1.2, 'Suburban': 0.9, 'Outer': 0.7}
        type_base = {'คอนโด': 120000, 'บ้านเดี่ยว': 80000, 'ทาวน์โฮม': 70000, 'ที่ดิน': 50000}
        base_per_sqm = type_base.get(property_type, 80000)
        mult = zone_multiplier.get(zone, 1.0)
        predicted = area_sqm * base_per_sqm * mult
        if has_bts:
            predicted *= 1.1
        return jsonify({
            'predicted_price': float(predicted),
            'formatted_price': format_thai_price(predicted),
            'model_info': 'Estimated (model not loaded)'
        })
    
    try:
        input_dict = {
            'area_sqm': area_sqm,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'floor': floor_val,
            'has_bts': has_bts,
            'age_days': 0,
        }
        # Add one-hot encoded zone and property_type
        input_dict[f'zone_{zone}'] = 1
        input_dict[f'property_type_{property_type}'] = 1
        
        input_df = pd.DataFrame([input_dict])
        input_df = input_df.reindex(columns=model_columns, fill_value=0)
        
        prediction = float(model.predict(input_df)[0])
        
        # Load evaluation info
        eval_data = load_json_file(EVAL_PATH)
        best_model_name = max(eval_data.keys(), key=lambda k: eval_data[k].get('R2', 0)) if eval_data else 'Unknown'
        r2 = eval_data.get(best_model_name, {}).get('R2', 0)
        
        return jsonify({
            'predicted_price': prediction,
            'formatted_price': format_thai_price(prediction),
            'model_info': f'{best_model_name} (R² = {r2:.4f})'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def format_thai_price(price):
    if price >= 1_000_000:
        return f"฿{price/1_000_000:.2f} ล้าน"
    elif price >= 100_000:
        return f"฿{price/100_000:.1f} แสน"
    else:
        return f"฿{price:,.0f}"

@app.route('/api/charts/price-by-zone')
def chart_price_by_zone():
    df = load_data()
    if df.empty or 'zone' not in df.columns or 'price_thb' not in df.columns:
        return jsonify({"labels": [], "data": []})
        
    grouped = df.groupby('zone')['price_thb'].mean().sort_values(ascending=False).reset_index()
    return jsonify({
        "labels": grouped['zone'].tolist(),
        "data": [round(v, 2) for v in grouped['price_thb'].tolist()]
    })

@app.route('/api/charts/price-distribution')
def chart_price_distribution():
    df = load_data()
    if df.empty or 'price_thb' not in df.columns:
        return jsonify({"labels": [], "data": []})
    
    prices = df['price_thb'].dropna()
    # Cap at 95th percentile for better visualization
    cap = prices.quantile(0.95)
    prices = prices[prices <= cap]
    
    hist, bins = np.histogram(prices, bins=20)
    labels = [f"{bins[i]/1e6:.1f}-{bins[i+1]/1e6:.1f}M" for i in range(len(bins)-1)]
    
    return jsonify({
        "labels": labels,
        "data": hist.tolist()
    })

@app.route('/api/charts/type-breakdown')
def chart_type_breakdown():
    df = load_data()
    if df.empty or 'property_type' not in df.columns:
        return jsonify({"labels": [], "data": []})
        
    counts = df['property_type'].value_counts()
    return jsonify({
        "labels": counts.index.tolist(),
        "data": counts.values.tolist()
    })

@app.route('/api/charts/price-vs-area')
def chart_price_vs_area():
    df = load_data()
    if df.empty or 'price_thb' not in df.columns or 'area_sqm' not in df.columns:
        return jsonify({"datasets": []})
    
    # Filter reasonable ranges for visualization  
    df = df[(df['area_sqm'] > 0) & (df['area_sqm'] < 2000) & 
            (df['price_thb'] > 0) & (df['price_thb'] < df['price_thb'].quantile(0.95))]
        
    # Sample to 500 points
    if len(df) > 500:
        df = df.sample(500, random_state=42)
    
    colors = {
        'คอนโด': 'rgba(99, 102, 241, 0.7)',
        'บ้านเดี่ยว': 'rgba(16, 185, 129, 0.7)',
        'ทาวน์โฮม': 'rgba(245, 158, 11, 0.7)',
        'ที่ดิน': 'rgba(239, 68, 68, 0.7)'
    }
        
    datasets = []
    if 'property_type' in df.columns:
        for p_type in df['property_type'].unique():
            subset = df[df['property_type'] == p_type]
            data = [{"x": round(float(r['area_sqm']), 1), "y": round(float(r['price_thb']), 0)} 
                    for _, r in subset.iterrows() if pd.notna(r['area_sqm']) and pd.notna(r['price_thb'])]
            datasets.append({
                "label": str(p_type),
                "data": data,
                "backgroundColor": colors.get(str(p_type), 'rgba(148, 163, 184, 0.7)')
            })
        
    return jsonify({"datasets": datasets})

@app.route('/api/charts/price-trend')
def chart_price_trend():
    df = load_data()
    if df.empty or 'posted_date' not in df.columns or 'price_thb' not in df.columns:
        return jsonify({"labels": [], "data": []})
        
    try:
        df['posted_date_dt'] = pd.to_datetime(df['posted_date'], errors='coerce')
        df = df.dropna(subset=['posted_date_dt', 'price_thb'])
        grouped = df.groupby(df['posted_date_dt'].dt.to_period('M'))['price_thb'].mean().reset_index()
        grouped['posted_date_dt'] = grouped['posted_date_dt'].astype(str)
        grouped = grouped.sort_values('posted_date_dt')
        return jsonify({
            "labels": grouped['posted_date_dt'].tolist(),
            "data": [round(v, 2) for v in grouped['price_thb'].tolist()]
        })
    except Exception as e:
        print(f"Price trend error: {e}")
        return jsonify({"labels": [], "data": []})

@app.route('/api/charts/feature-importance')
def chart_feature_importance():
    fi = load_json_file(FI_PATH)
    if fi:
        # Sort by importance
        sorted_fi = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:15]
        labels = [item[0] for item in sorted_fi]
        data = [round(item[1], 4) for item in sorted_fi]
        return jsonify({"labels": labels, "data": data})
    
    # Dummy data
    return jsonify({
        "labels": ["area_sqm", "zone_CBD", "property_type_คอนโด", "bedrooms", "has_bts", "bathrooms", "floor"],
        "data": [0.45, 0.20, 0.15, 0.08, 0.05, 0.04, 0.03]
    })

@app.route('/api/pipeline-report')
def pipeline_report():
    report = load_json_file(REPORT_PATH)
    if report:
        # Restructure for frontend consumption
        cleaning = report.get('cleaning', {})
        result = {
            'initial_rows': cleaning.get('before', 0),
            'final_rows': cleaning.get('after', 0),
            'operations': cleaning.get('operations', {}),
            'generation_time': round(report.get('generation_time', 0), 2),
            'cleaning_time': round(report.get('cleaning_time', 0), 2),
            'transformation_time': round(report.get('transformation_time', 0), 2),
            'modeling_time': round(report.get('modeling_time', 0), 2),
            'total_time': round(report.get('total_time', 0), 2),
            'modeling': report.get('modeling', {}),
            'transformation': report.get('transformation', {})
        }
        return jsonify(result)
    
    return jsonify({
        'initial_rows': 0,
        'final_rows': 0,
        'operations': {},
        'message': 'No pipeline report found. Please run the pipeline first.'
    })

if __name__ == '__main__':
    print(f"\n{'='*50}")
    print(f"  Real Estate Dashboard - Pumpkin Grill")
    print(f"  Data: {DATA_PATH}")
    print(f"  Model: {MODEL_PATH}")
    print(f"{'='*50}")
    print(f"\n  Open http://localhost:8080 in your browser\n")
    app.run(debug=True, host='0.0.0.0', port=8080)
