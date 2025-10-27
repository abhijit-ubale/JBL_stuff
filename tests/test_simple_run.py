#!/usr/bin/env python3
"""
Simple test to check if all imports and basic functionality work
"""

# Import all modules at the top
import src.healthcare_crl
from pathlib import Path
from src.healthcare_crl.data.pipeline import RealDataPipeline
from src.healthcare_crl.models.causal_graph import create_healthcare_causal_model, CausalOracle
from src.healthcare_crl.agents.crl_agent import CausalRLAgent, MultiAgentCRL
from src.healthcare_crl.baselines.baselines import BaselineAgents
from src.healthcare_crl.utils.metrics import ResilienceMetrics, EpisodeData
from data.TRADITIONAL_RULES.traditional_baseline_system import TraditionalBaselineSystem


def test_data_pipeline():
    """Test data pipeline initialization"""
    print("\nTesting data pipeline...")
    
    # Use absolute path to data directory
    data_path = r"c:\ABHIz_WORLD\ALL_CODE\PANKAJ_RISHAB\JBL_stuff\data\DATA_SPLITS"
    pipeline = RealDataPipeline(data_path)
    print("  ✓ Pipeline initialized")
    
    # Test the actual available methods
    supply_train = pipeline.get_supply_chain_records('train')
    print(f"  ✓ Supply chain train: {len(supply_train)} records")
    
    logistics_train = pipeline.get_logistics_performance('train')
    print(f"  ✓ Logistics train: {len(logistics_train)} records")
    
    disasters_train = pipeline.get_disaster_records('train', 'natural')
    print(f"  ✓ Natural disasters train: {len(disasters_train)} records")
    
    stats = pipeline.get_dataset_statistics()
    print(f"  ✓ Dataset statistics: {len(stats)} items")
        
    return True

def test_traditional_baseline():
    """Test traditional baseline system"""
    print("\nTesting traditional baseline...")
    
    # Pass the path string, not the pipeline object
    # Use absolute path to data directory 
    data_path = r"c:\ABHIz_WORLD\ALL_CODE\PANKAJ_RISHAB\JBL_stuff\data\DATA_SPLITS"
    traditional_system = TraditionalBaselineSystem(data_path)
    
    print("  ✓ Traditional system initialized")
    
    metrics = traditional_system.calculate_comprehensive_traditional_metrics()
    print("  ✓ Traditional metrics calculated")
    print(f"    - Recovery Time: {metrics.get('recovery_time', 'N/A')} days")
    print(f"    - Service Level: {metrics.get('service_level', 'N/A')}%")
    print(f"    - Cost: ${metrics.get('cost', 'N/A')}")
    print(f"    - Supplier Reliability: {metrics.get('supplier_reliability', 'N/A')}%")
    print(f"    - Adaptability: {metrics.get('adaptation_capability', 'N/A')}%")
    
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("HEALTHCARE CRL FRAMEWORK - SIMPLE TEST")
    print("="*60)
    
    success = True
    
    
    # Test data pipeline
    success &= test_data_pipeline()
    
    # Test traditional baseline
    success &= test_traditional_baseline()
    
    print("\n" + "="*60)
    if success:
        print("✓ ALL TESTS PASSED - Framework is ready!")
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
    print("="*60)
    
    return success

if __name__ == "__main__":
    main()