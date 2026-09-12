import os
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_mock_data(base_path: str, seed: int = 42):
    """Generates mock real estate data with injected problems."""
    np.random.seed(seed)
    random.seed(seed)
    
    raw_dir = os.path.join(base_path, 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    
    # Common lists
    locations = [
        'สุขุมวิท', 'Sukhumvit', 'สีลม', 'Silom', 'สาทร', 'Sathorn', 'ลาดพร้าว', 'Lat Phrao',
        'พระราม9', 'Rama 9', 'อ่อนนุช', 'On Nut', 'บางนา', 'Bang Na', 'รังสิต', 'Rangsit',
        'ธนบุรี', 'Thonburi', 'พญาไท', 'Phaya Thai', 'อารีย์', 'Ari', 'ทองหล่อ', 'Thong Lo',
        'เอกมัย', 'Ekkamai', 'ราชเทวี', 'Ratchathewi', 'ห้วยขวาง', 'Huai Khwang',
        'บางกะปิ', 'Bang Kapi', 'มีนบุรี', 'Min Buri', 'หนองจอก', 'Nong Chok',
        'ตลิ่งชัน', 'Taling Chan', 'บางแค', 'Bang Khae', 'จตุจักร', 'Chatuchak'
    ]
    prop_types = ['คอนโด', 'Condo', 'condominium', 'บ้านเดี่ยว', 'House', 'Single House', 'detached house', 'ทาวน์โฮม', 'Townhome', 'Townhouse', 'ที่ดิน', 'Land', 'land plot']
    
    def random_date(start_days_ago=365):
        base_date = datetime.now() - timedelta(days=random.randint(0, start_days_ago))
        return base_date
        
    # Zone multiplier for price-per-sqm (CBD is most expensive)
    zone_price_multiplier = {
        'สุขุมวิท': 1.8, 'Sukhumvit': 1.8, 'สีลม': 1.7, 'Silom': 1.7,
        'สาทร': 1.65, 'Sathorn': 1.65, 'ทองหล่อ': 2.0, 'Thong Lo': 2.0,
        'เอกมัย': 1.6, 'Ekkamai': 1.6, 'อารีย์': 1.5, 'Ari': 1.5,
        'พญาไท': 1.3, 'Phaya Thai': 1.3, 'ราชเทวี': 1.25, 'Ratchathewi': 1.25,
        'ลาดพร้าว': 1.1, 'Lat Phrao': 1.1, 'พระราม9': 1.2, 'Rama 9': 1.2,
        'อ่อนนุช': 1.05, 'On Nut': 1.05, 'ห้วยขวาง': 1.1, 'Huai Khwang': 1.1,
        'จตุจักร': 1.15, 'Chatuchak': 1.15, 'บางนา': 0.85, 'Bang Na': 0.85,
        'บางกะปิ': 0.8, 'Bang Kapi': 0.8, 'ธนบุรี': 0.75, 'Thonburi': 0.75,
        'ตลิ่งชัน': 0.7, 'Taling Chan': 0.7, 'บางแค': 0.65, 'Bang Khae': 0.65,
        'รังสิต': 0.55, 'Rangsit': 0.55, 'มีนบุรี': 0.5, 'Min Buri': 0.5,
        'หนองจอก': 0.4, 'Nong Chok': 0.4
    }
    
    # Base price-per-sqm by property type (THB)
    type_base_price = {
        'คอนโด': 120000, 'Condo': 120000, 'condominium': 120000,
        'บ้านเดี่ยว': 80000, 'House': 80000, 'Single House': 80000, 'detached house': 80000,
        'ทาวน์โฮม': 65000, 'Townhome': 65000, 'Townhouse': 65000,
        'ที่ดิน': 45000, 'Land': 45000, 'land plot': 45000
    }
    
    bts_stations = [
        'BTS สุขุมวิท', 'BTS สีลม', 'BTS อ่อนนุช', 'BTS เอกมัย', 'BTS ทองหล่อ',
        'BTS พร้อมพงษ์', 'BTS อารีย์', 'BTS สะพานควาย', 'BTS ชิดลม',
        'MRT ลาดพร้าว', 'MRT พระราม9', 'MRT ห้วยขวาง', 'MRT สุขุมวิท',
        'MRT จตุจักร', 'MRT บางซื่อ', 'MRT ศูนย์วัฒนธรรม'
    ]
    
    def generate_base_listing(source_name, id_prefix, p_type):
        loc = random.choice(locations)
        title = f"{p_type} for sale at {loc}"
        desc = f"Beautiful {p_type} located in {loc}. Great view."
        
        # Area based on property type
        if p_type in ['คอนโด', 'Condo', 'condominium']:
            area = random.uniform(25, 200)
            beds = max(1, int(area / 40) + random.randint(-1, 1))
            beds = min(beds, 5)
            baths = max(1, beds - random.randint(0, 1))
            floor = random.randint(1, 40)
        elif p_type in ['บ้านเดี่ยว', 'House', 'Single House', 'detached house']:
            area = random.uniform(100, 500)
            beds = max(2, int(area / 60) + random.randint(-1, 1))
            beds = min(beds, 8)
            baths = max(2, beds - random.randint(0, 2))
            floor = random.randint(1, 3)
        elif p_type in ['ทาวน์โฮม', 'Townhome', 'Townhouse']:
            area = random.uniform(60, 200)
            beds = max(2, int(area / 50) + random.randint(-1, 1))
            beds = min(beds, 5)
            baths = max(1, beds - random.randint(0, 1))
            floor = random.randint(2, 4)
        else:  # Land
            area = random.uniform(50, 5000)
            beds = 0
            baths = 0
            floor = 0
        
        # Price = area × base_price_per_sqm × zone_multiplier × noise
        base_ppsqm = type_base_price.get(p_type, 80000)
        zone_mult = zone_price_multiplier.get(loc, 1.0)
        noise = random.gauss(1.0, 0.15)  # ±15% random variation
        
        # BTS proximity bonus
        near_bts = random.choice(bts_stations) if random.random() < 0.6 else ''
        bts_bonus = 1.1 if near_bts else 1.0
        
        # Floor bonus for condos
        floor_bonus = 1.0 + (floor * 0.005) if p_type in ['คอนโด', 'Condo', 'condominium'] else 1.0
        
        price = area * base_ppsqm * zone_mult * noise * bts_bonus * floor_bonus
        price = max(price, 100000)  # Minimum price floor
        
        dt = random_date()
        
        return {
            'price': price,
            'area_sqm': area,
            'beds': beds,
            'baths': baths,
            'floor': floor,
            'loc': loc,
            'title': title,
            'desc': desc,
            'near_bts': near_bts,
            'dt': dt
        }

    print("Generating Source 1: DDProperty (17,000 records)...")
    dd_records = []
    for i in range(17000):
        p_type = random.choice(prop_types)
        base = generate_base_listing("DDProperty", "DD", p_type)
        
        price = int(base['price'])
        area = base['area_sqm']
        beds = base['beds']
        
        # Inject problems
        r = random.random()
        if r < 0.08:
            price = np.nan
        if r < 0.05:
            area = np.nan
        if 0.13 < r < 0.16:
            price = -abs(price) if price is not np.nan else price
            area = -abs(area) if area is not np.nan else area
        if 0.16 < r < 0.18:
            price = 0
        if 0.18 < r < 0.20 and price is not np.nan and area is not np.nan:
            # Swap
            price, area = area, price
        if 0.20 < r < 0.22:
            beds = random.randint(21, 50)
            
        title = base['title']
        desc = base['desc']
        if r < 0.05: title += ' &amp; <br>'
        if r < 0.10: title += ' 🏠🔥⭐'
        if 0.10 < r < 0.15: title = f"คอนโดสวย โทร 081-{random.randint(100,999)}-{random.randint(1000,9999)} " + title
            
        record = {
            'id': f'DD{i}',
            'title': title,
            'description': desc,
            'price': price,
            'area_sqm': area,
            'bedrooms': beds,
            'bathrooms': base['baths'],
            'property_type': p_type,
            'location': base['loc'],
            'floor': base['floor'],
            'near_bts': base['near_bts'],
            'posted_date': base['dt'].strftime('%Y-%m-%d'),
            'url': f'https://ddproperty.fake/listing/{i}',
            'source': 'DDProperty'
        }
        dd_records.append(record)
        
    # Duplicate some rows
    for _ in range(200):
        idx = random.randint(0, len(dd_records)-1)
        dd_records.append(dd_records[idx].copy())
        
    pd.DataFrame(dd_records).to_csv(os.path.join(raw_dir, 'ddproperty.csv'), index=False)

    print("Generating Source 2: Baania (17,000 records)...")
    baania_records = []
    # Mix thai formats
    for i in range(17000):
        p_type = random.choice(prop_types)
        base = generate_base_listing("Baania", "BN", p_type)
        
        price_val = base['price']
        price_str = f"{int(price_val)}"
        
        r = random.random()
        if r < 0.1: price_str = f"{price_val/1_000_000:.1f} ล้าน"
        elif r < 0.2: price_str = f"{int(price_val/100_000)} แสน"
        elif r < 0.3: price_str = f"{int(price_val):,} บาท"
        elif r < 0.35: price_str = "ราคาต่อรอง"
        elif r < 0.4: price_str = "สอบถาม"
        
        beds = base['beds']
        if r < 0.10: beds = np.nan
        
        area_wah = base['area_sqm'] / 4.0
        if r < 0.05: area_wah = 999999
        
        title = base['title']
        desc = base['desc']
        if r < 0.05: title = "ด่วน!!! " * 3 + title
        if 0.05 < r < 0.10: 
            desc = desc.upper() + " Call 088888888"
            desc = "รับฝากขาย-เช่า ติดต่อ... " + desc
            
        loc = base['loc']
        if loc == 'Sukhumvit' or loc == 'สุขุมวิท':
            loc = random.choice(['สุขุมวิท', 'สุขุมวิท ', 'Sukhumvit', ' สุขุมวิท', 'สุขุมวิทร์'])
            
        # Mixed dates
        dt_str = base['dt'].strftime('%Y-%m-%d')
        if r < 0.3: dt_str = base['dt'].strftime('%d/%m/%Y')
        elif r < 0.6: dt_str = base['dt'].strftime('%d %b %y')
            
        record = {
            'รหัส': f'BN{i}',
            'หัวข้อ': title,
            'รายละเอียด': desc,
            'ราคา': price_str,
            'พื้นที่_ตร.วา': area_wah,
            'ห้องนอน': beds,
            'ห้องน้ำ': base['baths'],
            'ประเภท': p_type,
            'ทำเล': loc,
            'ชั้น': base['floor'],
            'ใกล้รถไฟฟ้า': base['near_bts'],
            'วันที่ลง': dt_str,
            'ลิงก์': f'https://baania.fake/p/{i}',
            'แหล่ง': 'Baania'
        }
        baania_records.append(record)
        
    for _ in range(150):
        idx = random.randint(0, len(baania_records)-1)
        dup = baania_records[idx].copy()
        dup['ราคา'] = str(dup['ราคา']) + ' '
        baania_records.append(dup)

    pd.DataFrame(baania_records).to_csv(os.path.join(raw_dir, 'baania.csv'), index=False)
    
    print("Generating Source 3: HipFlat (16,000 records)...")
    hipflat_records = []
    for i in range(16000):
        p_type = random.choice(prop_types)
        base = generate_base_listing("HipFlat", "HF", p_type)
        
        cost_usd = base['price'] / 35.0
        
        r = random.random()
        if r < 0.05: cost_usd = base['price'] # accidentaly in THB
        if 0.05 < r < 0.08: cost_usd = random.choice([0, 1])
        
        sqm = base['area_sqm']
        land_rai = sqm // 1600
        land_ngan = (sqm % 1600) // 400
        land_wah = ((sqm % 1600) % 400) / 4.0
        
        if r < 0.07:
            land_rai, land_ngan, land_wah = np.nan, np.nan, np.nan
        elif 0.07 < r < 0.12:
            land_rai += 0.5 # Fractional rai double counting
            
        type_val = p_type
        if r < 0.03: type_val = random.choice(['asdf', '123', ''])
        
        beds_val = base['beds']
        if r < 0.05: beds_val = 'studio'
        elif 0.05 < r < 0.1: beds_val = '3+1'
        elif 0.1 < r < 0.15: beds_val = 'N/A'
        
        dt_str = base['dt'].strftime('%Y-%m-%d')
        if r < 0.3: dt_str = base['dt'].strftime('%b %d, %Y')
        elif r < 0.6: dt_str = base['dt'].strftime('%d/%m/%y')
        
        name = base['title']
        if r < 0.05: name += '\u0e00'
        
        record = {
            'listing_id': f'HF{i}',
            'name': name,
            'desc': base['desc'],
            'cost_usd': cost_usd,
            'land_rai': land_rai,
            'land_ngan': land_ngan,
            'land_wah': land_wah,
            'beds': beds_val,
            'baths': base['baths'],
            'type': type_val,
            'area': sqm,
            'level': base['floor'],
            'date': dt_str,
            'platform': 'HipFlat'
        }
        hipflat_records.append(record)

    pd.DataFrame(hipflat_records).to_csv(os.path.join(raw_dir, 'hipflat.csv'), index=False)
    print("Done generating mock data.")

if __name__ == "__main__":
    generate_mock_data(os.path.join(os.path.dirname(__file__), '..', '..'))
