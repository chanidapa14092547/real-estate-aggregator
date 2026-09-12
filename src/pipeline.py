import os
import sys
# Add project root to path so we can import src.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import argparse
import json
from src.extraction.mock_generator import generate_mock_data
from src.cleaning.cleaner import DataCleaner
from src.transformation.transformer import DataTransformer
from src.modeling.predictor import PropertyPredictor

def main():
    parser = argparse.ArgumentParser(description="Real Estate Aggregator Pipeline")
    parser.add_argument('--skip-generation', action='store_true', help="Skip mock data generation")
    parser.add_argument('--skip-training', action='store_true', help="Skip model training")
    args = parser.parse_args()

    print("========================================")
    print("  Real Estate Aggregator Pipeline Run   ")
    print("========================================")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    
    report = {}
    start_time = time.time()
    
    # Step 1: Mock Data Generation
    if not args.skip_generation:
        print("\n--- Step 1: Data Generation ---")
        t0 = time.time()
        generate_mock_data(project_root, seed=42)
        report['generation_time'] = time.time() - t0
    else:
        print("\n--- Step 1: Data Generation (SKIPPED) ---")
        
    # Step 2: Data Cleaning
    print("\n--- Step 2: Data Cleaning ---")
    t0 = time.time()
    raw_dir = os.path.join(project_root, 'data', 'raw')
    clean_dir = os.path.join(project_root, 'data', 'cleaned')
    cleaner = DataCleaner(raw_dir, clean_dir)
    clean_stats = cleaner.clean()
    report['cleaning'] = clean_stats
    report['cleaning_time'] = time.time() - t0
    
    # Step 3: Data Transformation
    print("\n--- Step 3: Data Transformation ---")
    t0 = time.time()
    trans_dir = os.path.join(project_root, 'data', 'transformed')
    transformer = DataTransformer(clean_dir, trans_dir)
    final_count = transformer.transform()
    report['transformation'] = {'final_record_count': final_count}
    report['transformation_time'] = time.time() - t0
    
    # Step 4: Model Training
    if not args.skip_training:
        print("\n--- Step 4: Model Training ---")
        t0 = time.time()
        data_path = os.path.join(trans_dir, 'final_listings.csv')
        model_dir = os.path.join(project_root, 'models')
        predictor = PropertyPredictor(data_path, model_dir)
        eval_results = predictor.train_and_evaluate()
        report['modeling'] = eval_results
        report['modeling_time'] = time.time() - t0
    else:
        print("\n--- Step 4: Model Training (SKIPPED) ---")

    report['total_time'] = time.time() - start_time
    
    # Save Report
    report_path = os.path.join(project_root, 'data', 'pipeline_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=4)
        
    print("\n========================================")
    print("          Pipeline Summary              ")
    print("========================================")
    print(f"Total execution time: {report['total_time']:.2f} seconds")
    print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    main()
