import os
import pandas as pd
import numpy as np
import re

class DataCleaner:
    """Handles cleaning of real estate listings data."""
    
    def __init__(self, raw_dir, clean_dir):
        self.raw_dir = raw_dir
        self.clean_dir = clean_dir
        self.stats = {'before': 0, 'after': 0, 'operations': {}}
        
    def _log_op(self, op_name, count_diff):
        self.stats['operations'][op_name] = self.stats['operations'].get(op_name, 0) + count_diff
        print(f"  [{op_name}] Removed {count_diff} records")

    def _extract_location_from_title(self, title):
        """Extract location name from title text like 'Condo for sale at สุขุมวิท'."""
        if pd.isna(title):
            return np.nan
        locations = [
            'สุขุมวิท', 'Sukhumvit', 'สีลม', 'Silom', 'สาทร', 'Sathorn',
            'ลาดพร้าว', 'Lat Phrao', 'พระราม9', 'Rama 9', 'อ่อนนุช', 'On Nut',
            'บางนา', 'Bang Na', 'รังสิต', 'Rangsit', 'ธนบุรี', 'Thonburi',
            'พญาไท', 'Phaya Thai', 'อารีย์', 'Ari', 'ทองหล่อ', 'Thong Lo',
            'เอกมัย', 'Ekkamai', 'ราชเทวี', 'Ratchathewi', 'ห้วยขวาง', 'Huai Khwang',
            'บางกะปิ', 'Bang Kapi', 'มีนบุรี', 'Min Buri', 'หนองจอก', 'Nong Chok',
            'ตลิ่งชัน', 'Taling Chan', 'บางแค', 'Bang Khae', 'จตุจักร', 'Chatuchak'
        ]
        title_lower = str(title).lower()
        for loc in locations:
            if loc.lower() in title_lower:
                return loc
        return np.nan

    def load_and_merge(self):
        """Load 3 CSVs and merge into a unified schema."""
        # 1. DDProperty
        dd = pd.read_csv(os.path.join(self.raw_dir, 'ddproperty.csv'))
        dd_clean = pd.DataFrame({
            'id': dd['id'],
            'title': dd['title'],
            'description': dd['description'],
            'price_raw': dd['price'],
            'area_raw': dd['area_sqm'],
            'area_unit': 'sqm',
            'bedrooms': dd['bedrooms'],
            'bathrooms': dd['bathrooms'],
            'property_type': dd['property_type'],
            'location': dd['location'],
            'floor': dd['floor'],
            'near_bts': dd['near_bts'],
            'posted_date': dd['posted_date'],
            'source': dd['source']
        })
        
        # 2. Baania
        bn = pd.read_csv(os.path.join(self.raw_dir, 'baania.csv'))
        bn_clean = pd.DataFrame({
            'id': bn['รหัส'],
            'title': bn['หัวข้อ'],
            'description': bn['รายละเอียด'],
            'price_raw': bn['ราคา'],
            'area_raw': bn['พื้นที่_ตร.วา'],
            'area_unit': 'sqw',
            'bedrooms': bn['ห้องนอน'],
            'bathrooms': bn['ห้องน้ำ'],
            'property_type': bn['ประเภท'],
            'location': bn['ทำเล'],
            'floor': bn['ชั้น'],
            'near_bts': bn['ใกล้รถไฟฟ้า'],
            'posted_date': bn['วันที่ลง'],
            'source': bn['แหล่ง']
        })
        
        # 3. HipFlat — extract location from title since no location column
        hf = pd.read_csv(os.path.join(self.raw_dir, 'hipflat.csv'))
        hf_locations = hf['name'].apply(self._extract_location_from_title)
        
        hf_clean = pd.DataFrame({
            'id': hf['listing_id'],
            'title': hf['name'],
            'description': hf['desc'],
            'price_raw': hf['cost_usd'],
            'area_raw': hf['area'],
            'area_unit': 'sqm_split',
            'bedrooms': hf['beds'],
            'bathrooms': hf['baths'],
            'property_type': hf['type'],
            'location': hf_locations,
            'floor': hf['level'],
            'near_bts': pd.Series([np.nan]*len(hf)),
            'posted_date': hf['date'],
            'source': hf['platform'],
            'land_rai': hf['land_rai'],
            'land_ngan': hf['land_ngan'],
            'land_wah': hf['land_wah']
        })
        
        df = pd.concat([dd_clean, bn_clean, hf_clean], ignore_index=True)
        self.stats['before'] = len(df)
        print(f"  Loaded {len(dd_clean)} DDProperty + {len(bn_clean)} Baania + {len(hf_clean)} HipFlat = {len(df)} total")
        return df
        
    def deduplicate(self, df):
        """Remove duplicates."""
        initial_len = len(df)
        # Exact duplicates by id
        df = df.drop_duplicates(subset=['id'], keep='first')
        
        # Fuzzy/Cross-source duplicates: same title + location + similar price
        df = df.drop_duplicates(subset=['title', 'location', 'price_raw'], keep='first')
        
        self._log_op('deduplication', initial_len - len(df))
        return df
        
    def handle_missing(self, df):
        """Handle missing values appropriately."""
        initial_len = len(df)
        
        # Drop if both price and area missing
        mask = df['price_raw'].isna() & df['area_raw'].isna()
        df = df[~mask].copy()
        
        # Flag missing prices for imputation
        df['price_imputed'] = df['price_raw'].isna()
        
        # Drop untransformable text prices
        untransformable = ['ราคาต่อรอง', 'สอบถาม']
        df = df[~df['price_raw'].astype(str).str.strip().isin(untransformable)].copy()
        
        # Handle string bedrooms
        df['bedrooms'] = df['bedrooms'].replace({'studio': 0, '3+1': 4, 'N/A': np.nan})
        df['bedrooms'] = pd.to_numeric(df['bedrooms'], errors='coerce')
        
        # Infer bedrooms by property type
        condo_mask = (df['property_type'].str.contains('คอนโด|condo|condominium', case=False, na=False)) & df['bedrooms'].isna()
        df.loc[condo_mask, 'bedrooms'] = 1
        house_mask = (df['property_type'].str.contains('บ้าน|house|detached', case=False, na=False)) & df['bedrooms'].isna()
        df.loc[house_mask, 'bedrooms'] = 3
        townhome_mask = (df['property_type'].str.contains('ทาวน์|town', case=False, na=False)) & df['bedrooms'].isna()
        df.loc[townhome_mask, 'bedrooms'] = 2
        land_mask = (df['property_type'].str.contains('ที่ดิน|land', case=False, na=False)) & df['bedrooms'].isna()
        df.loc[land_mask, 'bedrooms'] = 0
        
        self._log_op('missing_values', initial_len - len(df))
        return df

    def filter_spam_outliers(self, df):
        """Filter out spam, outliers and fix artifacts."""
        initial_len = len(df)
        
        # === TEXT CLEANUP ===
        # HTML/Emoji artifacts in title
        df['title'] = df['title'].astype(str).str.replace(r'&amp;|<br>|\\n\\t', '', regex=True)
        df['title'] = df['title'].str.replace(r'[🏠🔥⭐\u0e00]', '', regex=True)
        
        # === SPAM REMOVAL ===
        # Phone numbers in title
        phone_mask = df['title'].str.contains(r'0\d{1,2}[-\s]?\d{3}[-\s]?\d{4}', regex=True, na=False)
        df = df[~phone_mask].copy()
        
        # Agent ads in description
        agent_keywords = r'รับฝากขาย|รับฝากเช่า|นายหน้า'
        agent_mask = df['description'].astype(str).str.contains(agent_keywords, regex=True, na=False)
        df = df[~agent_mask].copy()
        
        # Spam titles with repeated exclamation
        spam_mask = df['title'].str.contains(r'ด่วน!!!', regex=True, na=False)
        df = df[~spam_mask].copy()
        
        # === GARBAGE PROPERTY TYPES ===
        valid_types = r'คอนโด|condo|condominium|บ้าน|house|detached|ทาวน์|town|ที่ดิน|land'
        garbage_type = ~df['property_type'].astype(str).str.contains(valid_types, case=False, na=False)
        df = df[~garbage_type].copy()
        
        # === NUMERIC FIXES ===
        # Convert price_raw to numeric for checks (keep original)
        temp_price = pd.to_numeric(df['price_raw'], errors='coerce')
        
        # Remove price = 0 or price = 1 (test data)
        zero_price = (temp_price == 0) | (temp_price == 1)
        df = df[~zero_price | temp_price.isna() | df['price_raw'].apply(lambda x: isinstance(x, str) and not x.strip().isdigit())].copy()
        temp_price = pd.to_numeric(df['price_raw'], errors='coerce')
        
        # Fix negative prices/areas — take absolute
        neg_price = temp_price < 0
        df.loc[neg_price, 'price_raw'] = temp_price[neg_price].abs()
        
        temp_area = pd.to_numeric(df['area_raw'], errors='coerce')
        neg_area = temp_area < 0
        df.loc[neg_area, 'area_raw'] = temp_area[neg_area].abs()
        
        # Fix swapped price/area (price < 1000 and area > 100000)
        temp_price = pd.to_numeric(df['price_raw'], errors='coerce')
        temp_area = pd.to_numeric(df['area_raw'], errors='coerce')
        swap_mask = (temp_price < 1000) & (temp_area > 100000) & temp_price.notna() & temp_area.notna()
        if swap_mask.sum() > 0:
            df.loc[swap_mask, ['price_raw', 'area_raw']] = df.loc[swap_mask, ['area_raw', 'price_raw']].values
        
        # Remove bedrooms > 15
        df = df[(df['bedrooms'] <= 15) | df['bedrooms'].isna()].copy()
        
        # Remove area = 999999 (placeholder)
        temp_area = pd.to_numeric(df['area_raw'], errors='coerce')
        df = df[(temp_area != 999999) | temp_area.isna()].copy()
        
        # === DETECT AND FIX HipFlat USD values that are actually THB ===
        # If cost_usd > 500000 it's likely THB not USD
        hipflat_mask = df['source'] == 'HipFlat'
        temp_price_hf = pd.to_numeric(df.loc[hipflat_mask, 'price_raw'], errors='coerce')
        already_thb = temp_price_hf > 500000
        # Mark these so transformer knows not to multiply by 35
        df.loc[hipflat_mask & (temp_price_hf > 500000).reindex(df.index, fill_value=False), 'area_unit'] = 'sqm_split_thb'
        
        self._log_op('spam_outliers', initial_len - len(df))
        return df
        
    def clean(self):
        print("Starting data cleaning...")
        df = self.load_and_merge()
        print(f"\n  Phase 1: Deduplication")
        df = self.deduplicate(df)
        print(f"  Phase 2: Missing Value Handling")
        df = self.handle_missing(df)
        print(f"  Phase 3: Spam & Outlier Filtering")
        df = self.filter_spam_outliers(df)
        
        self.stats['after'] = len(df)
        os.makedirs(self.clean_dir, exist_ok=True)
        df.to_csv(os.path.join(self.clean_dir, 'cleaned_listings.csv'), index=False)
        
        print(f"\n  === Cleaning Summary ===")
        print(f"  Before: {self.stats['before']:,} records")
        print(f"  After:  {self.stats['after']:,} records")
        print(f"  Total removed: {self.stats['before'] - self.stats['after']:,}")
        for op, count in self.stats['operations'].items():
            print(f"    - {op}: {count:,}")
        
        return self.stats

if __name__ == "__main__":
    cleaner = DataCleaner('../../data/raw', '../../data/cleaned')
    cleaner.clean()
