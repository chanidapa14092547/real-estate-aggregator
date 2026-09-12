"""
Test suite for the Real Estate Aggregator Pipeline.
Run with: python -m pytest tests/test_pipeline.py -v
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extraction.mock_generator import generate_mock_data
from src.cleaning.cleaner import DataCleaner
from src.transformation.transformer import DataTransformer
from src.modeling.predictor import PropertyPredictor


@pytest.fixture(scope='module')
def project_root(tmp_path_factory):
    """Create a temporary project root for testing."""
    root = tmp_path_factory.mktemp("test_project")
    return str(root)


@pytest.fixture(scope='module')
def raw_data(project_root):
    """Generate mock data for testing."""
    generate_mock_data(project_root, seed=42)
    raw_dir = os.path.join(project_root, 'data', 'raw')
    return raw_dir


class TestMockGenerator:
    """Tests for mock data generation."""
    
    def test_generates_three_files(self, raw_data):
        """Should create 3 CSV files."""
        files = os.listdir(raw_data)
        csv_files = [f for f in files if f.endswith('.csv')]
        assert len(csv_files) == 3
    
    def test_ddproperty_has_records(self, raw_data):
        """DDProperty should have ~17,200 records (17K + duplicates)."""
        df = pd.read_csv(os.path.join(raw_data, 'ddproperty.csv'))
        assert len(df) > 17000
        assert 'id' in df.columns
        assert 'price' in df.columns
        assert 'area_sqm' in df.columns
    
    def test_baania_has_thai_columns(self, raw_data):
        """Baania should have Thai column names."""
        df = pd.read_csv(os.path.join(raw_data, 'baania.csv'))
        assert 'ราคา' in df.columns
        assert 'พื้นที่_ตร.วา' in df.columns
        assert 'ทำเล' in df.columns
        assert len(df) > 17000
    
    def test_hipflat_has_usd_prices(self, raw_data):
        """HipFlat should have cost_usd column."""
        df = pd.read_csv(os.path.join(raw_data, 'hipflat.csv'))
        assert 'cost_usd' in df.columns
        assert 'land_rai' in df.columns
        assert len(df) >= 16000
    
    def test_data_has_problems(self, raw_data):
        """Mock data should contain injected problems."""
        dd = pd.read_csv(os.path.join(raw_data, 'ddproperty.csv'))
        # Should have some missing prices
        assert dd['price'].isna().sum() > 0
        # Should have duplicates
        assert dd.duplicated(subset=['id']).sum() > 0
    
    def test_total_records_near_50k(self, raw_data):
        """Total records across all sources should be ~50,000."""
        dd = pd.read_csv(os.path.join(raw_data, 'ddproperty.csv'))
        bn = pd.read_csv(os.path.join(raw_data, 'baania.csv'))
        hf = pd.read_csv(os.path.join(raw_data, 'hipflat.csv'))
        total = len(dd) + len(bn) + len(hf)
        assert 49000 < total < 52000


class TestCleaner:
    """Tests for data cleaning."""
    
    @pytest.fixture(scope='class')
    def cleaned_data(self, raw_data):
        """Run cleaner and return stats."""
        clean_dir = os.path.join(os.path.dirname(raw_data), 'cleaned')
        cleaner = DataCleaner(raw_data, clean_dir)
        stats = cleaner.clean()
        return stats, clean_dir
    
    def test_reduces_record_count(self, cleaned_data):
        """Cleaning should reduce the number of records."""
        stats, _ = cleaned_data
        assert stats['after'] < stats['before']
    
    def test_removes_duplicates(self, cleaned_data):
        """Should report deduplication removals."""
        stats, _ = cleaned_data
        assert stats['operations']['deduplication'] > 0
    
    def test_handles_missing_values(self, cleaned_data):
        """Should report missing value handling."""
        stats, _ = cleaned_data
        assert stats['operations']['missing_values'] > 0
    
    def test_filters_spam(self, cleaned_data):
        """Should report spam/outlier filtering."""
        stats, _ = cleaned_data
        assert stats['operations']['spam_outliers'] > 0
    
    def test_creates_output_file(self, cleaned_data):
        """Should create cleaned CSV file."""
        _, clean_dir = cleaned_data
        output = os.path.join(clean_dir, 'cleaned_listings.csv')
        assert os.path.exists(output)
    
    def test_unified_schema(self, cleaned_data):
        """Output should have unified column schema."""
        _, clean_dir = cleaned_data
        df = pd.read_csv(os.path.join(clean_dir, 'cleaned_listings.csv'), nrows=10)
        required_cols = ['id', 'title', 'price_raw', 'area_raw', 'area_unit', 'property_type', 'source']
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"


class TestTransformer:
    """Tests for data transformation."""
    
    @pytest.fixture(scope='class')
    def transformed_data(self, raw_data):
        """Run cleaner + transformer and return path."""
        base = os.path.dirname(raw_data)
        clean_dir = os.path.join(base, 'cleaned')
        trans_dir = os.path.join(base, 'transformed')
        
        # Clean if not already done
        if not os.path.exists(os.path.join(clean_dir, 'cleaned_listings.csv')):
            cleaner = DataCleaner(raw_data, clean_dir)
            cleaner.clean()
        
        transformer = DataTransformer(clean_dir, trans_dir)
        count = transformer.transform()
        return trans_dir, count
    
    def test_creates_final_csv(self, transformed_data):
        """Should create final_listings.csv."""
        trans_dir, _ = transformed_data
        assert os.path.exists(os.path.join(trans_dir, 'final_listings.csv'))
    
    def test_has_price_thb(self, transformed_data):
        """Prices should be in THB."""
        trans_dir, _ = transformed_data
        df = pd.read_csv(os.path.join(trans_dir, 'final_listings.csv'), nrows=100)
        assert 'price_thb' in df.columns
        assert df['price_thb'].notna().sum() > 0
        # Prices should be reasonable (> 100K, < 500M THB)
        valid_prices = df['price_thb'].dropna()
        assert valid_prices.min() > 0
    
    def test_has_area_sqm(self, transformed_data):
        """Areas should be in square meters."""
        trans_dir, _ = transformed_data
        df = pd.read_csv(os.path.join(trans_dir, 'final_listings.csv'), nrows=100)
        assert 'area_sqm' in df.columns
        valid_areas = df['area_sqm'].dropna()
        assert valid_areas.min() > 0
    
    def test_has_zone_classification(self, transformed_data):
        """Should have zone column with valid values."""
        trans_dir, _ = transformed_data
        df = pd.read_csv(os.path.join(trans_dir, 'final_listings.csv'), nrows=500)
        assert 'zone' in df.columns
        valid_zones = {'CBD', 'Inner City', 'Suburban', 'Outer', 'Unknown'}
        actual_zones = set(df['zone'].dropna().unique())
        assert actual_zones.issubset(valid_zones)
    
    def test_property_types_normalized(self, transformed_data):
        """Property types should be normalized to Thai."""
        trans_dir, _ = transformed_data
        df = pd.read_csv(os.path.join(trans_dir, 'final_listings.csv'), nrows=500)
        valid_types = {'คอนโด', 'บ้านเดี่ยว', 'ทาวน์โฮม', 'ที่ดิน'}
        actual_types = set(df['property_type'].dropna().unique())
        assert actual_types.issubset(valid_types), f"Unexpected types: {actual_types - valid_types}"
    
    def test_price_per_sqm_calculated(self, transformed_data):
        """Should have price_per_sqm column."""
        trans_dir, _ = transformed_data
        df = pd.read_csv(os.path.join(trans_dir, 'final_listings.csv'), nrows=100)
        assert 'price_per_sqm' in df.columns
        assert df['price_per_sqm'].notna().sum() > 0


class TestPredictor:
    """Tests for ML prediction."""
    
    @pytest.fixture(scope='class')
    def trained_model(self, raw_data):
        """Train model and return results."""
        base = os.path.dirname(raw_data)
        clean_dir = os.path.join(base, 'cleaned')
        trans_dir = os.path.join(base, 'transformed')
        model_dir = os.path.join(base, 'models')
        
        # Ensure transformed data exists
        data_path = os.path.join(trans_dir, 'final_listings.csv')
        if not os.path.exists(data_path):
            if not os.path.exists(os.path.join(clean_dir, 'cleaned_listings.csv')):
                cleaner = DataCleaner(raw_data, clean_dir)
                cleaner.clean()
            transformer = DataTransformer(clean_dir, trans_dir)
            transformer.transform()
        
        predictor = PropertyPredictor(data_path, model_dir)
        results = predictor.train_and_evaluate()
        return results, model_dir
    
    def test_trains_three_models(self, trained_model):
        """Should train 3 models."""
        results, _ = trained_model
        assert len(results) == 3
        assert 'Linear Regression' in results
        assert 'Random Forest' in results
        assert 'Gradient Boosting' in results
    
    def test_evaluation_metrics(self, trained_model):
        """Each model should have MAE, RMSE, R2."""
        results, _ = trained_model
        for name, metrics in results.items():
            assert 'MAE' in metrics
            assert 'RMSE' in metrics
            assert 'R2' in metrics
            assert metrics['MAE'] > 0
            assert metrics['RMSE'] > 0
    
    def test_best_model_saved(self, trained_model):
        """Best model should be saved to disk."""
        _, model_dir = trained_model
        assert os.path.exists(os.path.join(model_dir, 'best_model.pkl'))
        assert os.path.exists(os.path.join(model_dir, 'model_columns.pkl'))
        assert os.path.exists(os.path.join(model_dir, 'evaluation.json'))
    
    def test_prediction_works(self, trained_model):
        """Should make a reasonable prediction."""
        _, model_dir = trained_model
        predictor = PropertyPredictor.load_model(model_dir)
        price = predictor.predict(
            area_sqm=50, bedrooms=1, bathrooms=1,
            floor=10, zone='CBD', property_type='คอนโด', has_bts=1
        )
        assert price > 0
        # A 50sqm condo in CBD should be roughly 5M-30M THB
        assert 1_000_000 < price < 100_000_000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
