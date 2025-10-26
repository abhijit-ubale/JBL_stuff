"""
Test script to verify real data integration works correctly.
Tests all major components with real CSV data.
"""

import sys
import logging
import numpy as np
import warnings
from pathlib import Path

# Suppress SyntaxWarnings from pgmpy library (Python 3.13 compatibility)
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pgmpy")
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pyro")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_data_pipeline():
    """Test the RealDataPipeline class."""
    logger.info("Testing RealDataPipeline...")
    
    try:
        from data_pipeline import RealDataPipeline
        
        # Initialize pipeline
        pipeline = RealDataPipeline('DATA_SPLITS')
        
        # Test dataset statistics
        stats = pipeline.get_dataset_statistics()
        logger.info(f"Loaded {len(stats)} datasets")
        
        for name, stat in stats.items():
            logger.info(f"  {name}: {stat['num_records']} records, {stat['num_features']} features")
        
        # Test integrated features
        train_features = pipeline.create_integrated_features('train')
        logger.info(f"Integrated training features: {train_features.shape}")
        
        # Test feature vector extraction
        sample_record = train_features.iloc[0].to_dict()
        feature_vector = pipeline.get_feature_vector_for_state(sample_record)
        logger.info(f"Feature vector shape: {feature_vector.shape}")
        logger.info(f"State dimension: {pipeline.get_state_dimension()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Data pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_causal_graph():
    """Test the causal graph with real data."""
    logger.info("Testing CausalGraph with real data...")
    
    try:
        from causal_graph import create_healthcare_causal_model
        from data_pipeline import RealDataPipeline
        
        # Create pipeline for sample data
        pipeline = RealDataPipeline('DATA_SPLITS')
        train_features = pipeline.create_integrated_features('train')
        
        # Create causal model
        causal_graph, causal_oracle = create_healthcare_causal_model()
        
        # Test causal oracle with real data context
        sample_record = train_features.iloc[0].to_dict()
        
        test_context = {
            'lead_time_days': sample_record.get('Lead_Time_Days', 50),
            'supplier_reliability_score': sample_record.get('Supplier_Reliability_Score', 0.8),
            'on_time_delivery_pct': sample_record.get('On_Time_Delivery_%', 90),
            'freight_cost_level': sample_record.get('Freight_Cost_USD', 50000),
            'disruption_severity': sample_record.get('Disruption_Severity', 1)
        }
        
        # Test oracle methods
        legal_actions = causal_oracle.legal_actions(test_context)
        logger.info(f"Legal actions: {legal_actions}")
        
        if legal_actions:
            effect = causal_oracle.effect('increase_safety_stock', test_context)
            logger.info(f"Effect of increase_safety_stock: {effect}")
        
        return True
        
    except Exception as e:
        logger.error(f"Causal graph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment():
    """Test the HealthcareCRLEnvironment with real data."""
    logger.info("Testing HealthcareCRLEnvironment...")
    
    try:
        from main import HealthcareCRLEnvironment
        
        config = {
            'data_splits_path': 'DATA_SPLITS',
            'episode_length': 10,  # Short test episode
            'disruption_types': ['pandemic']
        }
        
        # Create environment
        env = HealthcareCRLEnvironment(config)
        
        # Test reset
        initial_state = env.reset()
        logger.info(f"Initial state shape: {initial_state.shape}")
        logger.info(f"State size: {env.state_size}, Action size: {env.action_size}")
        
        # Test a few steps
        for step in range(3):
            action = np.random.randint(0, env.action_size)
            next_state, reward, done, info = env.step(action)
            
            logger.info(f"Step {step}: action={action}, reward={reward:.3f}, done={done}")
            logger.info(f"  Context keys: {list(info.get('context', {}).keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"Environment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agents():
    """Test agent creation and basic functionality."""
    logger.info("Testing CRL and baseline agents...")
    
    try:
        from crl_agent import CausalRLAgent
        from baselines import BaselineAgents
        from causal_graph import create_healthcare_causal_model
        
        # Create causal model for CRL agent
        causal_graph, causal_oracle = create_healthcare_causal_model()
        
        # Test CRL agent
        crl_agent = CausalRLAgent(
            state_size=20,
            action_size=6,
            causal_oracle=causal_oracle,
            learning_rate=1e-4
        )
        
        # Test baseline agents
        baselines = BaselineAgents.get_all_baselines(20, 6, causal_oracle)
        
        logger.info(f"Created CRL agent and {len(baselines)} baseline agents")
        
        # Test action selection
        test_state = np.random.randn(20)
        test_context = {'supplier_reliability_score': 0.8, 'lead_time_days': 45}
        
        crl_action = crl_agent.act(test_state, test_context)
        logger.info(f"CRL agent action: {crl_action}")
        
        for name, agent in baselines.items():
            action = agent.act(test_state, test_context)
            logger.info(f"{name} agent action: {action}")
        
        return True
        
    except Exception as e:
        logger.error(f"Agents test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metrics():
    """Test metrics calculation with real data structure."""
    logger.info("Testing ResilienceMetrics...")
    
    try:
        from metrics import ResilienceMetrics, EpisodeData
        from datetime import datetime, timedelta
        
        # Create sample episode data
        episode = EpisodeData(
            episode_id=1,
            agent_type='crl_agent',
            disruption_type='flood',
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=30),
            actions_taken=[
                {'action_type': 'increase_safety_stock', 'timestamp': 5},
                {'action_type': 'emergency_procurement', 'timestamp': 15}
            ],
            state_trajectory=[
                {'service_level': 0.88, 'inventory_level': 0.7, 'lead_time': 45},
                {'service_level': 0.75, 'inventory_level': 0.5, 'lead_time': 60},
                {'service_level': 0.82, 'inventory_level': 0.65, 'lead_time': 50}
            ],
            rewards=[1.0, -0.3, 0.6],
            costs=[70, 95, 85],  # Using real data baseline
            service_levels=[0.88, 0.75, 0.82],
            inventory_levels=[0.7, 0.5, 0.65],
            supplier_performances=[
                {'on_time_delivery': 0.88, 'quality_compliance': 0.92, 'response_time_score': 0.8}
            ]
        )
        
        # Calculate metrics
        metrics_calculator = ResilienceMetrics()
        all_metrics = metrics_calculator.calculate_all_metrics(episode)
        
        logger.info("Calculated metrics:")
        for metric_name, metric_data in all_metrics.items():
            if isinstance(metric_data, dict) and len(metric_data) > 0:
                main_value = list(metric_data.values())[0]
                logger.info(f"  {metric_name}: {main_value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""
    logger.info("="*60)
    logger.info("REAL DATA INTEGRATION TESTS")
    logger.info("="*60)
    
    # Check if data files exist
    data_splits_path = Path('DATA_SPLITS')
    if not data_splits_path.exists():
        logger.error(f"DATA_SPLITS folder not found at {data_splits_path.absolute()}")
        return False
    
    csv_files = list(data_splits_path.glob('*.csv'))
    if len(csv_files) < 8:
        logger.error(f"Expected 8 CSV files, found {len(csv_files)} in DATA_SPLITS")
        return False
    
    logger.info(f"Found {len(csv_files)} CSV files in DATA_SPLITS folder")
    
    # Run tests
    tests = [
        ("Data Pipeline", test_data_pipeline),
        ("Causal Graph", test_causal_graph), 
        ("Environment", test_environment),
        ("Agents", test_agents),
        ("Metrics", test_metrics)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                logger.info(f"✓ {test_name} test PASSED")
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Real data integration is working correctly.")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed. Check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)