# ระบบรวบรวมและวิเคราะห์ราคาที่อยู่อาศัย (Real Estate Aggregator)

**กลุ่ม (Group):** Pumpkin Grill  
**รายวิชา (Course):** 204426

## ภาพรวมของโปรเจกต์ (Project Overview)
โปรเจกต์นี้เป็นระบบที่ทำการรวบรวม ทำความสะอาด แปลงข้อมูล และสร้างโมเดล Machine Learning เพื่อทำนายและวิเคราะห์ราคาที่อยู่อาศัย โดยมี Web Dashboard สำหรับแสดงผลข้อมูลและผลการทำนาย

## สถาปัตยกรรมระบบ (Architecture Diagram)
```text
[Data Sources] --> (Extraction: src/extraction)
                      |
                      v
[Raw Data] ------> (Cleaning: src/cleaning)
                      |
                      v
[Cleaned Data] --> (Transformation: src/transformation)
                      |
                      v
[Transformed Data] -> (Modeling: src/modeling) --> [ML Models]
                      |
                      v
                  [Flask App: app/server.py]
                      |
                      v
                 [Web Dashboard (Port 8080)]
```

## วิธีการติดตั้ง (Installation)
ติดตั้งไลบรารีที่จำเป็นทั้งหมดผ่านคำสั่ง:
```bash
pip install -r requirements.txt
```

## วิธีรัน Data Pipeline (How to run the pipeline)
รัน pipeline เพื่อสร้างข้อมูล ทำความสะอาดข้อมูล และเทรนโมเดล:
```bash
python src/pipeline.py
```

## วิธีรัน Dashboard (How to run the dashboard)
เปิดการทำงานของ Flask web server:
```bash
python app/server.py
```
หลังจากรันคำสั่ง สามารถเข้าดู Dashboard ได้ที่ `http://localhost:8080`

## วิธีรัน Tests (How to run tests)
สามารถรัน unit test สำหรับตรวจสอบ pipeline ได้ด้วยคำสั่ง:
```bash
python -m unittest tests/test_pipeline.py
```

## เทคนิค Data Engineering ที่ใช้
1. **Data Extraction**: ดึงข้อมูลและสร้างข้อมูลจำลอง (Mock scraper) จาก 3 แหล่งข้อมูลที่แตกต่างกัน
2. **Data Cleaning**: 
   - ลบข้อมูลที่ซ้ำซ้อน (Deduplication)
   - จัดการค่าว่างหรือข้อมูลสูญหาย (Handling missing values)
   - คัดกรองข้อมูลสแปม (Spam filtering)
   - จัดการค่าที่ผิดปกติหรืออยู่นอกเกณฑ์ (Handling outliers)
3. **Data Transformation**: 
   - ปรับมาตรฐานและบรรทัดฐานของราคา (Price normalization)
   - แปลงหน่วยพื้นที่ให้อยู่ในหน่วยมาตรฐานเดียวกัน (Area conversion)
   - จับคู่และจัดกลุ่มโซนพื้นที่ (Zone mapping)

## โมเดล Machine Learning (ML Models)
- ระบบใช้โมเดล Machine Learning เพื่อทำนายราคาที่อยู่อาศัยและวิเคราะห์แนวโน้มตลาด

## เทคโนโลยีที่ใช้ (Tech Stack)
- **ภาษาหลัก:** Python
- **จัดการข้อมูล:** Pandas, NumPy
- **Machine Learning:** scikit-learn, joblib
- **เว็บแอปพลิเคชัน:** Flask, Gunicorn
- **การแสดงผลกราฟิก:** Chart.js
- **Cloud Deployment:** Render
