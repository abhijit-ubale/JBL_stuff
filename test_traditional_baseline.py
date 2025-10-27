#!/usr/bin/env python3
"""
Test script for Traditional Baseline System
"""

import sys
sys.path.append('.')
from TRADITIONAL_RULES.traditional_baseline_system import TraditionalBaselineSystem

def main():
    print('Testing Traditional Baseline System...')
    try:
        traditional_system = TraditionalBaselineSystem()
        metrics = traditional_system.calculate_comprehensive_traditional_metrics()
        
        print('\nKey Traditional Baseline Metrics:')
        key_metrics = [
            'traditional_service_level', 
            'traditional_recovery_time_days', 
            'traditional_cost_efficiency', 
            'traditional_supplier_reliability'
        ]
        
        for metric in key_metrics:
            if metric in metrics:
                print(f'  {metric}: {metrics[metric]:.4f}')
        
        print(f'\nTotal records analyzed: {metrics.get("traditional_baseline_record_count", 0)}')
        print('✓ Traditional Baseline System working correctly!')
        
        # Test comparison metrics
        comparison = traditional_system.get_traditional_vs_crl_comparison_metrics()
        print('\nComparison-Ready Metrics:')
        for metric_name, metric_data in comparison.items():
            print(f'  {metric_name}: {metric_data["traditional_baseline"]:.2f} {metric_data["unit"]}')
        
        return True
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()