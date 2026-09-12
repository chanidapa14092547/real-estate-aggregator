import os
import pandas as pd
import numpy as np
from datetime import datetime

class DataTransformer:
    """Handles feature engineering and standardization."""
    
    def __init__(self, clean_dir, trans_dir):
        self.clean_dir = clean_dir
        self.trans_dir = trans_dir
        
    def normalize_prices(self, df):
        """Parse text prices and convert USD to THB."""
        def parse_price(val, source, area_unit):
            if pd.isna(val):
                return np.nan
            
            # Numeric values
            if isinstance(val, (int, float)):
                num = float(val)
                if num <= 0:
                    return np.nan
                # HipFlat: convert USD to THB unless already marked as THB
                if source == 'HipFlat':
                    if area_unit == 'sqm_split_thb':
                        return num  # Already THB
                    return num * 35.0
                return num
                
            val_str = str(val).strip()
            
            # Thai formats: "3.5 ล้าน", "3.5ล้าน", "35 ล้านบาท"
            lan_match = re.search(r'([\d,.]+)\s*ล้าน', val_str)
            if lan_match:
                num = float(lan_match.group(1).replace(',', ''))
                return num * 1_000_000
            
            # Thai: "8 แสน"
            saen_match = re.search(r'([\d,.]+)\s*แสน', val_str)
            if saen_match:
                num = float(saen_match.group(1).replace(',', ''))
                return num * 100_000
                
            # Numeric with commas and optional "บาท": "3,500,000 บาท", "3500000"
            val_str = val_str.replace(',', '').replace('บาท', '').replace(' ', '').strip()
            try:
                num = float(val_str)
                if num <= 0:
                    return np.nan
                if source == 'HipFlat' and area_unit != 'sqm_split_thb':
                    return num * 35.0
                return num
            except:
                return np.nan
        
        import re
        df['price_thb'] = df.apply(
            lambda row: parse_price(row['price_raw'], row['source'], row.get('area_unit', '')), 
            axis=1
        )
        
        # Remove extreme prices (> 500M THB for any single listing is unrealistic for mock data)
        df.loc[df['price_thb'] > 500_000_000, 'price_thb'] = np.nan
        
        return df

    def convert_area(self, df):
        """Convert all areas to SQM."""
        def to_sqm(row):
            area = pd.to_numeric(row.get('area_raw'), errors='coerce')
            unit = row.get('area_unit', 'sqm')
            
            # For HipFlat with split rai/ngan/wah
            if unit in ['sqm_split', 'sqm_split_thb']:
                rai = pd.to_numeric(row.get('land_rai'), errors='coerce')
                ngan = pd.to_numeric(row.get('land_ngan'), errors='coerce')
                wah = pd.to_numeric(row.get('land_wah'), errors='coerce')
                
                if pd.notna(rai) and pd.notna(ngan) and pd.notna(wah):
                    # Cap rai to reasonable values (max ~10 rai for Bangkok)
                    rai = min(rai, 10)
                    ngan = min(ngan, 3)
                    sqm = (rai * 1600) + (ngan * 400) + (wah * 4)
                    if sqm > 0:
                        return sqm
                
                # Fallback to area column
                if pd.notna(area) and area > 0:
                    return area
                return np.nan
            
            if pd.isna(area) or area <= 0:
                return np.nan
                
            if unit == 'sqw':
                return area * 4.0  # ตร.วา to ตร.ม.
            
            return area  # Already in sqm
            
        df['area_sqm'] = df.apply(to_sqm, axis=1)
        
        # Cap extreme areas (max ~20,000 sqm for urban plots)
        df.loc[df['area_sqm'] > 20000, 'area_sqm'] = np.nan
        
        return df

    def categorize_location(self, df):
        """Normalize locations and assign zones."""
        loc_map = {
            'sukhumvit': 'สุขุมวิท', 'สุขุมวิท ': 'สุขุมวิท', ' สุขุมวิท': 'สุขุมวิท', 'สุขุมวิทร์': 'สุขุมวิท',
            'silom': 'สีลม', 'sathorn': 'สาทร', 'lat phrao': 'ลาดพร้าว', 'rama 9': 'พระราม9',
            'on nut': 'อ่อนนุช', 'bang na': 'บางนา', 'rangsit': 'รังสิต', 'thonburi': 'ธนบุรี',
            'phaya thai': 'พญาไท', 'ari': 'อารีย์', 'thong lo': 'ทองหล่อ', 'ekkamai': 'เอกมัย',
            'ratchathewi': 'ราชเทวี', 'huai khwang': 'ห้วยขวาง', 'bang kapi': 'บางกะปิ',
            'min buri': 'มีนบุรี', 'nong chok': 'หนองจอก', 'taling chan': 'ตลิ่งชัน',
            'bang khae': 'บางแค', 'chatuchak': 'จตุจักร'
        }
        
        def normalize_loc(loc):
            if pd.isna(loc):
                return np.nan
            loc_str = str(loc).strip().lower()
            return loc_map.get(loc_str, loc.strip() if isinstance(loc, str) else loc)
        
        df['location'] = df['location'].apply(normalize_loc)
        
        zones = {
            'CBD': ['สุขุมวิท', 'สีลม', 'สาทร', 'ทองหล่อ', 'เอกมัย'],
            'Inner City': ['ลาดพร้าว', 'พระราม9', 'อ่อนนุช', 'พญาไท', 'อารีย์', 'ราชเทวี', 'ห้วยขวาง', 'จตุจักร'],
            'Suburban': ['บางนา', 'บางกะปิ', 'ธนบุรี', 'ตลิ่งชัน', 'บางแค'],
            'Outer': ['รังสิต', 'มีนบุรี', 'หนองจอก']
        }
        
        def assign_zone(loc):
            if pd.isna(loc):
                return 'Unknown'
            for z, locs in zones.items():
                if loc in locs:
                    return z
            return 'Unknown'
            
        df['zone'] = df['location'].apply(assign_zone)
        df['district'] = df['location']
        return df

    def feature_engineering(self, df):
        """Create derived features for ML."""
        # Normalize property type
        p_map = {
            'condo': 'คอนโด', 'condominium': 'คอนโด', 
            'house': 'บ้านเดี่ยว', 'single house': 'บ้านเดี่ยว', 'detached house': 'บ้านเดี่ยว',
            'townhome': 'ทาวน์โฮม', 'townhouse': 'ทาวน์โฮม',
            'land': 'ที่ดิน', 'land plot': 'ที่ดิน'
        }
        df['property_type'] = df['property_type'].apply(
            lambda x: p_map.get(str(x).lower().strip(), x) if pd.notna(x) else x
        )
        
        # Impute missing prices using median by (property_type, zone)
        for (ptype, zone), group in df.groupby(['property_type', 'zone']):
            median_price = group['price_thb'].median()
            if pd.notna(median_price):
                mask = (df['property_type'] == ptype) & (df['zone'] == zone) & df['price_thb'].isna()
                df.loc[mask, 'price_thb'] = median_price
                df.loc[mask, 'price_imputed'] = True
        
        # Fill remaining NaN prices with overall median
        overall_median = df['price_thb'].median()
        df['price_thb'] = df['price_thb'].fillna(overall_median)
        
        # Price per sqm
        df['price_per_sqm'] = np.where(
            (df['area_sqm'] > 0) & df['area_sqm'].notna(),
            df['price_thb'] / df['area_sqm'],
            np.nan
        )
        
        # BTS
        df['has_bts'] = df['near_bts'].apply(lambda x: 1 if pd.notna(x) and str(x).strip() != '' else 0)
        
        # Age
        ref_date = datetime.now()
        df['posted_date_parsed'] = pd.to_datetime(df['posted_date'], errors='coerce', dayfirst=True)
        # Try alternative formats for unparsed dates
        unparsed = df['posted_date_parsed'].isna() & df['posted_date'].notna()
        if unparsed.any():
            df.loc[unparsed, 'posted_date_parsed'] = pd.to_datetime(
                df.loc[unparsed, 'posted_date'], errors='coerce', format='mixed'
            )
        df['age_days'] = (ref_date - df['posted_date_parsed']).dt.days.fillna(180)
        
        # Floor handling
        df['floor'] = pd.to_numeric(df['floor'], errors='coerce').fillna(0)
        
        return df

    def transform(self):
        print("Starting data transformation...")
        df = pd.read_csv(os.path.join(self.clean_dir, 'cleaned_listings.csv'), low_memory=False)
        
        print("  Step 1: Price normalization...")
        df = self.normalize_prices(df)
        print("  Step 2: Area unit conversion...")
        df = self.convert_area(df)
        print("  Step 3: Location categorization...")
        df = self.categorize_location(df)
        print("  Step 4: Feature engineering...")
        df = self.feature_engineering(df)
        
        # Drop records where both price and area are still missing
        df = df.dropna(subset=['price_thb'])
        df = df[df['area_sqm'].notna() & (df['area_sqm'] > 0)]
        
        # Remove extreme price_per_sqm outliers
        df = df[df['price_per_sqm'].notna() & (df['price_per_sqm'] > 0)]
        q99 = df['price_per_sqm'].quantile(0.99)
        df = df[df['price_per_sqm'] <= q99]
        
        cols = ['id', 'title', 'price_thb', 'area_sqm', 'price_per_sqm', 'bedrooms', 'bathrooms', 
                'property_type', 'location', 'zone', 'district', 'floor', 'near_bts', 'has_bts', 
                'posted_date', 'age_days', 'source', 'price_imputed']
        
        # Ensure cols exist
        for c in cols:
            if c not in df.columns:
                df[c] = np.nan
                
        final_df = df[cols].copy()
        
        # Fill NaN bedrooms/bathrooms
        final_df['bedrooms'] = final_df['bedrooms'].fillna(1)
        final_df['bathrooms'] = final_df['bathrooms'].fillna(1)
        
        os.makedirs(self.trans_dir, exist_ok=True)
        final_df.to_csv(os.path.join(self.trans_dir, 'final_listings.csv'), index=False)
        
        print(f"\n  === Transformation Summary ===")
        print(f"  Final records: {len(final_df):,}")
        print(f"  By zone: {final_df['zone'].value_counts().to_dict()}")
        print(f"  By type: {final_df['property_type'].value_counts().to_dict()}")
        print(f"  Price range: {final_df['price_thb'].min():,.0f} — {final_df['price_thb'].max():,.0f} THB")
        print(f"  Area range: {final_df['area_sqm'].min():,.1f} — {final_df['area_sqm'].max():,.1f} sqm")
        
        return len(final_df)

if __name__ == "__main__":
    t = DataTransformer('../../data/cleaned', '../../data/transformed')
    t.transform()
