"""
Traditional Baseline: Reorder Point and Safety Stock Rules
Based on GHSC supply chain data using fixed thresholds and historical consumption patterns.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class ReorderSafetyStockRules:
    """
    Traditional rule-based system for inventory management using fixed thresholds.
    
    Uses actual GHSC data columns:
    - Order_Volume_Units: Historical consumption data
    - Stockout_Frequency_per_Year: Historical stockout patterns  
    - Lead_Time_Days: Fixed lead time assumptions
    - Supplier_Reliability_Score: Historical supplier performance
    """
    
    def __init__(self, ghsc_data: pd.DataFrame):
        """Initialize with GHSC supply chain data."""
        self.ghsc_data = ghsc_data
        self.reorder_rules = self._calculate_fixed_reorder_points()
        self.safety_stock_rules = self._calculate_fixed_safety_stocks()
        
    def _calculate_fixed_reorder_points(self) -> Dict[str, Dict[str, float]]:
        """Calculate fixed reorder points by commodity and country using historical data."""
        reorder_points = {}
        
        # Group by Country and Commodity_Type to establish fixed rules
        for (country, commodity), group in self.ghsc_data.groupby(['Country', 'Commodity_Type']):
            key = f"{country}_{commodity}"
            
            # Traditional rule: Reorder point = Average consumption during lead time + Safety margin
            avg_lead_time = group['Lead_Time_Days'].mean()
            avg_order_volume = group['Order_Volume_Units'].mean()
            
            # Assume monthly consumption pattern (traditional approach)
            daily_consumption = avg_order_volume / 30.0  # Fixed assumption
            
            # Traditional reorder point calculation
            reorder_point = daily_consumption * avg_lead_time * 1.2  # 20% safety margin (fixed)
            
            reorder_points[key] = {
                'reorder_point': reorder_point,
                'daily_consumption': daily_consumption,
                'lead_time': avg_lead_time,
                'safety_margin': 0.2  # Fixed 20%
            }
            
        return reorder_points
    
    def _calculate_fixed_safety_stocks(self) -> Dict[str, Dict[str, float]]:
        """Calculate fixed safety stock levels using traditional formulas."""
        safety_stocks = {}
        
        for (country, commodity), group in self.ghsc_data.groupby(['Country', 'Commodity_Type']):
            key = f"{country}_{commodity}"
            
            # Traditional safety stock formula: SS = Z * σ * √(LT)
            # Where Z = service level factor (fixed), σ = demand std dev, LT = lead time
            
            avg_order_volume = group['Order_Volume_Units'].mean()
            std_order_volume = group['Order_Volume_Units'].std()
            avg_lead_time = group['Lead_Time_Days'].mean()
            
            # Traditional assumptions
            service_level_factor = 1.65  # 95% service level (fixed)
            daily_demand_std = (std_order_volume / 30.0) if not pd.isna(std_order_volume) else (avg_order_volume * 0.2 / 30.0)
            
            safety_stock = service_level_factor * daily_demand_std * np.sqrt(avg_lead_time)
            
            safety_stocks[key] = {
                'safety_stock': safety_stock,
                'service_level': 0.95,  # Fixed target
                'demand_variability': daily_demand_std,
                'lead_time_factor': np.sqrt(avg_lead_time)
            }
            
        return safety_stocks
    
    def get_traditional_inventory_decision(self, country: str, commodity: str, 
                                        current_inventory: float, 
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make inventory decision using expanded, strictly enforced rules.
        Strictly penalize deviations and add more emergency triggers.
        """
        key = f"{country}_{commodity}"
        if key not in self.reorder_rules:
            return self._get_default_decision(current_inventory)
        reorder_info = self.reorder_rules[key]
        safety_info = self.safety_stock_rules[key]
        reorder_point = reorder_info['reorder_point']
        safety_stock = safety_info['safety_stock']
        # Strict enforcement: check all relevant columns
        decision = {
            'action': 'no_action',
            'quantity': 0,
            'reasoning': 'inventory_adequate',
            'current_inventory': current_inventory,
            'reorder_point': reorder_point,
            'safety_stock': safety_stock,
            'strict_compliance': True,
            'penalties': [],
        }
        # Emergency triggers for low inventory, high stockout, high delay, low reliability
        emergency = False
        penalties = []
        # Emergency if inventory below safety stock
        if current_inventory < safety_stock:
            emergency = True
            penalties.append('inventory_below_safety_stock')
        # Emergency if stockout frequency high
        if context.get('Stockout_Frequency_per_Year', 0) > 0.1:
            emergency = True
            penalties.append('high_stockout_frequency')
        # Emergency if delivery delay high
        if context.get('Delivery_Delay_Days', 0) > 10:
            emergency = True
            penalties.append('high_delivery_delay')
        # Emergency if supplier reliability low
        if context.get('Supplier_Reliability_Score', 1.0) < 0.7:
            emergency = True
            penalties.append('low_supplier_reliability')
        # Emergency if disruption severity high
        if context.get('Disruption_Severity', 0) > 2:
            emergency = True
            penalties.append('high_disruption_severity')
        # Emergency if CO2 emissions high (environmental compliance)
        if context.get('CO2_Emissions_tons', 0) > 10000:
            penalties.append('high_co2_emissions')
        # Emergency if cost per unit high
        if context.get('Freight_Cost_USD', 0) / max(context.get('Order_Volume_Units', 1), 1) > 10:
            penalties.append('high_cost_per_unit')
        # Strict enforcement: always penalize any deviation from targets
        if context.get('On_Time_Delivery_%', 100) < 95:
            penalties.append('low_on_time_delivery')
        # Decision logic
        if emergency:
            emergency_quantity = reorder_info['daily_consumption'] * reorder_info['lead_time'] * 2
            decision.update({
                'action': 'emergency_procurement',
                'quantity': emergency_quantity,
                'reasoning': 'strict_emergency_triggered',
                'urgency': 'critical',
                'penalties': penalties
            })
        elif current_inventory < reorder_point or penalties:
            regular_quantity = reorder_info['daily_consumption'] * reorder_info['lead_time'] * 1.5
            decision.update({
                'action': 'regular_replenishment', 
                'quantity': regular_quantity,
                'reasoning': 'strict_replenishment_triggered',
                'urgency': 'high' if penalties else 'medium',
                'penalties': penalties
            })
        else:
            decision['penalties'] = penalties
        return decision
    
    def _get_default_decision(self, current_inventory: float) -> Dict[str, Any]:
        """Default decision for unknown commodity-country combinations."""
        # Generic traditional rules
        default_reorder_point = 1000  # Fixed assumption
        default_safety_stock = 500   # Fixed assumption
        
        if current_inventory < default_safety_stock:
            return {
                'action': 'emergency_procurement',
                'quantity': 2000,
                'reasoning': 'default_emergency_rule'
            }
        elif current_inventory < default_reorder_point:
            return {
                'action': 'regular_replenishment',
                'quantity': 1500,
                'reasoning': 'default_reorder_rule'
            }
        else:
            return {
                'action': 'no_action',
                'quantity': 0,
                'reasoning': 'default_adequate_stock'
            }
    
    def calculate_traditional_performance_metrics(self) -> Dict[str, float]:
        """Calculate traditional system performance using historical data patterns."""
        
        # Stockout frequency from actual data
        avg_stockout_freq = self.ghsc_data['Stockout_Frequency_per_Year'].mean()
        
        # Service level calculation (traditional method)
        avg_on_time_delivery = self.ghsc_data['On_Time_Delivery_%'].mean() / 100.0
        
        # Traditional inventory turnover calculation
        total_volume = self.ghsc_data['Order_Volume_Units'].sum()
        total_lead_time = self.ghsc_data['Lead_Time_Days'].sum()
        traditional_turnover = (total_volume * 365) / (total_lead_time * total_volume / len(self.ghsc_data))
        
        # Traditional cost efficiency 
        avg_freight_cost = self.ghsc_data['Freight_Cost_USD'].mean()
        
        # Recovery time estimation (traditional manual processes)
        # Based on disruption severity and manual response capabilities
        disruption_severity = self.ghsc_data['Disruption_Severity'].mean()
        manual_response_days = 5 + (disruption_severity * 2)  # Base 5 days + severity factor
        
        return {
            'traditional_service_level': avg_on_time_delivery,
            'traditional_stockout_frequency': avg_stockout_freq, 
            'traditional_inventory_turnover': traditional_turnover,
            'traditional_avg_cost': avg_freight_cost,
            'traditional_recovery_time_days': manual_response_days,
            'traditional_delivery_reliability': avg_on_time_delivery,
            'data_source': 'GHSC_historical_patterns'
        }
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get summary statistics of traditional rules."""
        return {
            'total_reorder_rules': len(self.reorder_rules),
            'total_safety_stock_rules': len(self.safety_stock_rules),
            'avg_reorder_point': np.mean([r['reorder_point'] for r in self.reorder_rules.values()]),
            'avg_safety_stock': np.mean([s['safety_stock'] for s in self.safety_stocks.values()]),
            'fixed_service_level_target': 0.95,
            'data_based_rules': True
        }


if __name__ == "__main__":
    # Test with GHSC data
    import sys
    import os
    
    ghsc_data = pd.read_csv('../DATA_SPLITS/GHSC_PSM_Synthetic_Resilience_Dataset_v2_consistent_traindata.csv')
    
    traditional_rules = ReorderSafetyStockRules(ghsc_data)
    
    # Test performance calculation
    performance = traditional_rules.calculate_traditional_performance_metrics()
    
    print("Traditional Baseline Performance Metrics (from GHSC data):")
    for metric, value in performance.items():
        print(f"  {metric}: {value}")
    
    # Test decision making
    decision = traditional_rules.get_traditional_inventory_decision(
        'Nigeria', 'Malaria_RDT', 500, {}
    )
    print(f"\nSample Decision: {decision}")