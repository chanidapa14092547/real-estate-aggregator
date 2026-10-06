import json
import os

def create_notebook():
    cells = []
    
    setup_code = """import os
import pandas as pd
from IPython.display import display

# สร้างโฟลเดอร์ที่จำเป็น
os.makedirs('data/raw', exist_ok=True)
os.makedirs('data/cleaned', exist_ok=True)
os.makedirs('data/transformed', exist_ok=True)
os.makedirs('models', exist_ok=True)
"""
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["# EstateInsight (Pumpkin Grill) - Data Pipeline\n", "สมุดโน้ตนี้ถูกตั้งค่าให้รันทีละขั้นตอน (Step-by-step) เพื่อโชว์ผลลัพธ์และดูหน้าตาข้อมูลในแต่ละขั้นให้เห็นภาพชัดเจนครับ"]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in setup_code.split("\n")]
    })

    files = [
        ("1. Data Extraction (จำลองข้อมูลดิบ)", "src/extraction/mock_generator.py", """
# รันการจำลองข้อมูล
print("--- Step 1: Data Generation ---")
generate_mock_data('.', seed=42)

# ดูหน้าตาข้อมูลดิบ (เช่นของ DDProperty ที่ยังมีความพังอยู่)
print("\\nตัวอย่างข้อมูลดิบ (DDProperty):")
df_raw = pd.read_csv('data/raw/ddproperty.csv')
display(df_raw.head())
"""),
        ("2. Data Cleaning (ทำความสะอาดข้อมูล)", "src/cleaning/cleaner.py", """
# รันการทำความสะอาดข้อมูล (ลบตัวซ้ำ กรองสแปม ฯลฯ)
print("--- Step 2: Data Cleaning ---")
cleaner = DataCleaner('data/raw', 'data/cleaned')
clean_stats = cleaner.clean()

# ดูหน้าตาข้อมูลที่คลีนแล้ว
print("\\nตัวอย่างข้อมูลที่ทำความสะอาดแล้ว:")
df_clean = pd.read_csv('data/cleaned/cleaned_listings.csv')
display(df_clean.head())
"""),
        ("3. Data Transformation (แปลงและปรับโครงสร้าง)", "src/transformation/transformer.py", """
# รันการแปลงข้อมูล (Zone Mapping, Standardize ราคาและพื้นที่)
print("--- Step 3: Data Transformation ---")
transformer = DataTransformer('data/cleaned', 'data/transformed')
transformer.transform()

# ดูหน้าตาข้อมูลที่แปลงเสร็จพร้อมเข้า ML
print("\\nตัวอย่างข้อมูลที่แปลงโครงสร้างแล้ว (ดูคอลัมน์ zone, price_thb, area_sqm):")
df_trans = pd.read_csv('data/transformed/final_listings.csv')
display(df_trans.head())
"""),
        ("4. Machine Learning (เทรนโมเดลประเมินราคา)", "src/modeling/predictor.py", """
# รันการเทรนโมเดล Gradient Boosting
print("--- Step 4: Model Training ---")
predictor = PropertyPredictor('data/transformed/final_listings.csv', 'models')
predictor.train_and_evaluate()
"""),
    ]
    
    for title, filepath, exec_code in files:
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"## {title}"]
        })
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
                if 'if __name__ == "__main__":' in code:
                    code = code.split('if __name__ == "__main__":')[0]
                    
            full_code = code + "\n" + exec_code
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in full_code.split("\n")]
            })
        except Exception as e:
            print(f"Could not read {filepath}: {e}")

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with open("Pumpkin_Grill_Data_Pipeline.ipynb", "w", encoding="utf-8") as f:
        json.dump(notebook, f, ensure_ascii=False, indent=2)
        
    print("Created Pumpkin_Grill_Data_Pipeline.ipynb (Step-by-step Version)")

if __name__ == "__main__":
    create_notebook()
