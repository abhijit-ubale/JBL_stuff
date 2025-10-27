"""
Traditional Baseline: Fixed Lead Time and Supplier Rules
Based on GHSC data using static supplier preferences and constant lead time assumptions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FixedLeadTimeSupplierRules:
    """
    Traditional supplier selection and lead time management using fixed rules.
    
    Uses actual GHSC data columns:
    - Lead_Time_Days: Historical lead time data treated as constants
    - Supplier_Reliability_Score: Used to establish preferred supplier rankings
    - Country: Geographic supplier preferences
    - Transport_Mode: Fixed transport preferences
    """
    
    def __init__(self, ghsc_data: pd.DataFrame):
        """Initialize with GHSC supply chain data."""
        self.ghsc_data = ghsc_data
        self.preferred_suppliers = self._establish_preferred_supplier_rules()
        self.fixed_lead_times = self._calculate_fixed_lead_times()
        self.transport_preferences = self._establish_transport_mode_preferences()
        
    def _establish_preferred_supplier_rules(self) -> Dict[str, Dict[str, Any]]:
        """Establish preferred supplier rules by commodity and country using historical performance."""
        supplier_rules = {}
        
        # Group by commodity to find preferred suppliers per country
        for commodity, group in self.ghsc_data.groupby('Commodity_Type'):
            country_suppliers = {}
            
            for country in group['Country'].unique():
                country_data = group[group['Country'] == country]
                
                # Traditional approach: Select supplier with highest reliability score as primary
                avg_reliability = country_data['Supplier_Reliability_Score'].mean()
                avg_lead_time = country_data['Lead_Time_Days'].mean()
                avg_cost = country_data['Freight_Cost_USD'].mean()
                
                # Traditional rule: Single preferred supplier (no dynamic switching)
                country_suppliers[country] = {
                    'primary_supplier_reliability': avg_reliability,
                    'backup_threshold': 0.7,  # Fixed threshold for supplier switching
                    'preferred_lead_time': avg_lead_time,
                    'preferred_cost': avg_cost,
                    'switching_allowed': False,  # Traditional: stick with primary unless failure
                    'failure_threshold': 0.5  # Only switch if reliability drops below 50%
                }
            
            supplier_rules[commodity] = country_suppliers
            
        return supplier_rules
    
    def _calculate_fixed_lead_times(self) -> Dict[str, Dict[str, float]]:
        """Calculate fixed lead time assumptions by commodity, country, and transport mode."""
        lead_time_rules = {}
        
        # Traditional approach: Use historical averages as fixed constants
        grouping_cols = ['Commodity_Type', 'Country', 'Transport_Mode']
        
        for group_key, group_data in self.ghsc_data.groupby(grouping_cols):
            commodity, country, transport_mode = group_key
            
            # Fixed lead time calculation (traditional: ignore disruption factors)
            base_lead_time = group_data['Lead_Time_Days'].mean()
            
            # Traditional buffer (fixed percentage)
            safety_buffer = 0.15  # Fixed 15% buffer
            fixed_lead_time = base_lead_time * (1 + safety_buffer)
            
            key = f"{commodity}_{country}_{transport_mode}"
            lead_time_rules[key] = {
                'base_lead_time': base_lead_time,
                'fixed_lead_time': fixed_lead_time,
                'safety_buffer': safety_buffer,
                'disruption_adjustment': 0.0,  # Traditional: no dynamic adjustment
                'seasonal_adjustment': 0.0     # Traditional: no seasonal consideration
            }
            
        return lead_time_rules
    
    def _establish_transport_mode_preferences(self) -> Dict[str, Dict[str, Any]]:
        """Establish fixed transport mode preferences by commodity and route."""
        transport_preferences = {}
        
        for commodity, group in self.ghsc_data.groupby('Commodity_Type'):
            mode_analysis = {}
            
            for transport_mode in group['Transport_Mode'].unique():
                mode_data = group[group['Transport_Mode'] == transport_mode]
                
                # Traditional metrics for mode selection
                avg_cost = mode_data['Freight_Cost_USD'].mean()
                avg_lead_time = mode_data['Lead_Time_Days'].mean()
                avg_reliability = mode_data['On_Time_Delivery_%'].mean()
                
                mode_analysis[transport_mode] = {
                    'avg_cost': avg_cost,
                    'avg_lead_time': avg_lead_time,
                    'avg_reliability': avg_reliability,
                    'usage_frequency': len(mode_data)
                }
            
            # Traditional rule: Select mode with best cost-reliability balance as primary
            best_mode = min(mode_analysis.keys(), 
                          key=lambda x: (mode_analysis[x]['avg_cost'] / max(mode_analysis[x]['avg_reliability'], 1)))
            
            transport_preferences[commodity] = {
                'primary_mode': best_mode,
                'mode_analysis': mode_analysis,
                'switching_policy': 'failure_only',  # Traditional: only switch on failure
                'cost_threshold': mode_analysis[best_mode]['avg_cost'] * 1.5  # Switch if 50% cost increase
            }
            
        return transport_preferences
    
    def get_traditional_supplier_decision(self, commodity: str, country: str, 
                                        current_reliability: float,
                                        disruption_active: bool = False) -> Dict[str, Any]:
        """
        Make supplier selection decision using traditional fixed rules.
        
        Traditional logic:
        - Stick with preferred supplier unless reliability drops below failure threshold
        - No proactive switching based on disruption predictions
        - Simple binary decision: primary or backup
        """
        
        if commodity not in self.preferred_suppliers:
            return self._get_default_supplier_decision()
        
        commodity_rules = self.preferred_suppliers[commodity]
        
        if country not in commodity_rules:
            return self._get_default_supplier_decision()
        
        supplier_rule = commodity_rules[country]
        
        # Traditional decision logic
        decision = {
            'action': 'continue_primary_supplier',
            'supplier_type': 'primary',
            'reasoning': 'within_acceptable_range',
            'current_reliability': current_reliability,
            'threshold': supplier_rule['failure_threshold']
        }
        
        # Traditional switching rule: only switch on clear failure
        if current_reliability < supplier_rule['failure_threshold']:
            decision.update({
                'action': 'switch_to_backup_supplier',
                'supplier_type': 'backup', 
                'reasoning': 'primary_supplier_failure',
                'urgency': 'high'
            })
        
        # Traditional approach: ignore disruption signals for proactive switching
        if disruption_active and current_reliability < supplier_rule['backup_threshold']:
            # Still conservative - only switch if reliability already degraded
            decision.update({
                'action': 'switch_to_backup_supplier',
                'supplier_type': 'backup',
                'reasoning': 'reliability_degradation_during_disruption'
            })
        
        return decision
    
    def get_traditional_lead_time_estimate(self, commodity: str, country: str, 
                                         transport_mode: str) -> Dict[str, float]:
        """
        Get fixed lead time estimate (traditional: no dynamic adjustment).
        """
        key = f"{commodity}_{country}_{transport_mode}"
        
        if key in self.fixed_lead_times:
            return self.fixed_lead_times[key]
        else:
            # Default traditional lead time rules
            return {
                'base_lead_time': 45.0,  # Default assumption
                'fixed_lead_time': 51.75,  # 45 * 1.15
                'safety_buffer': 0.15,
                'disruption_adjustment': 0.0,
                'seasonal_adjustment': 0.0
            }
    
    def calculate_traditional_supplier_performance(self) -> Dict[str, float]:
        """Calculate traditional supplier management performance metrics."""
        
        # Supplier reliability (no dynamic optimization)
        avg_supplier_reliability = self.ghsc_data['Supplier_Reliability_Score'].mean()
        
        # Lead time performance (fixed assumptions vs reality)
        actual_lead_times = self.ghsc_data['Lead_Time_Days'].mean()
        
        # Delivery performance under traditional fixed rules
        on_time_delivery = self.ghsc_data['On_Time_Delivery_%'].mean() / 100.0
        
        # Cost efficiency (no dynamic optimization)
        avg_freight_cost = self.ghsc_data['Freight_Cost_USD'].mean()
        
        # Traditional response to disruptions (manual, slow)
        disrupted_data = self.ghsc_data[self.ghsc_data['Disruption_Severity'] > 2]
        if len(disrupted_data) > 0:
            disruption_impact_on_delivery = (disrupted_data['On_Time_Delivery_%'].mean() / 
                                           self.ghsc_data['On_Time_Delivery_%'].mean())
            recovery_time_estimate = 7.0 + (disrupted_data['Disruption_Severity'].mean() * 1.5)
        else:
            disruption_impact_on_delivery = 1.0
            recovery_time_estimate = 7.0  # Default manual recovery time
        
        # Traditional switching frequency (low, only on failures)
        reliability_failures = len(self.ghsc_data[self.ghsc_data['Supplier_Reliability_Score'] < 0.5])
        switching_frequency = reliability_failures / len(self.ghsc_data)
        
        return {
            'traditional_supplier_reliability': avg_supplier_reliability,
            'traditional_lead_time_accuracy': actual_lead_times,
            'traditional_delivery_performance': on_time_delivery,
            'traditional_cost_efficiency': avg_freight_cost,
            'traditional_disruption_resilience': disruption_impact_on_delivery,
            'traditional_recovery_time_days': recovery_time_estimate,
            'traditional_supplier_switching_rate': switching_frequency,
            'manual_response_delay': 2.0,  # Days for manual decision making
            'data_source': 'GHSC_supplier_historical_patterns'
        }
    
    def _get_default_supplier_decision(self) -> Dict[str, Any]:
        """Default supplier decision for unknown combinations."""
        return {
            'action': 'continue_primary_supplier',
            'supplier_type': 'primary',
            'reasoning': 'default_rule_no_change',
            'current_reliability': 0.8,  # Default assumption
            'threshold': 0.5
        }
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get summary statistics of traditional supplier rules."""
        total_supplier_rules = sum(len(rules) for rules in self.preferred_suppliers.values())
        
        return {
            'total_supplier_rules': total_supplier_rules,
            'total_lead_time_rules': len(self.fixed_lead_times),
            'transport_mode_preferences': len(self.transport_preferences),
            'avg_reliability_threshold': 0.7,  # Fixed
            'avg_failure_threshold': 0.5,     # Fixed
            'dynamic_adjustment_enabled': False,  # Traditional characteristic
            'proactive_switching_enabled': False  # Traditional characteristic
        }


if __name__ == "__main__":
    # Test with GHSC data
    import sys
    import os
    
    ghsc_data = pd.read_csv('../DATA_SPLITS/GHSC_PSM_Synthetic_Resilience_Dataset_v2_consistent_traindata.csv')
    
    traditional_supplier_rules = FixedLeadTimeSupplierRules(ghsc_data)
    
    # Test performance calculation
    performance = traditional_supplier_rules.calculate_traditional_supplier_performance()
    
    print("Traditional Supplier Management Performance (from GHSC data):")
    for metric, value in performance.items():
        print(f"  {metric}: {value}")
    
    # Test decision making
    decision = traditional_supplier_rules.get_traditional_supplier_decision(
        'Malaria_RDT', 'Nigeria', 0.6, disruption_active=True
    )
    print(f"\nSample Supplier Decision: {decision}")