"""
ENHANCED Traditional Baseline: Comprehensive Reorder Point and Safety Stock Rules
Based on REAL GHSC, LPI, Disaster, and Emergency data with MAXIMUM STRICT enforcement.

Uses actual column names:
- Order_Volume_Units, Stockout_Frequency_per_Year, Lead_Time_Days
- Supplier_Reliability_Score, On_Time_Delivery_%
- Disruption_Severity, Disruption_Type
- CO2_Emissions_tons, Freight_Cost_USD
- Warehouse_Type, Transport_Mode, Resupply_Time_Days
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EnhancedReorderSafetyStockRules:
    """
    EXTREMELY STRICT traditional inventory system with comprehensive multi-factor rules.
    
    Key Characteristics:
    - Fixed inventory thresholds that NEVER change
    - Maximum safety buffers (conservative)
    - Multiple emergency escalation levels
    - Comprehensive penalty system for any deviation
    - Strict compliance tracking on all dimensions
    """
    
    def __init__(self, ghsc_data: pd.DataFrame):
        """Initialize with GHSC supply chain data."""
        self.ghsc_data = ghsc_data
        
        # Calculate all rules upfront (IMMUTABLE)
        self.reorder_rules = self._calculate_comprehensive_reorder_points()
        self.safety_stock_rules = self._calculate_comprehensive_safety_stocks()
        self.emergency_triggers = self._establish_emergency_trigger_rules()
        self.disruption_inventory_rules = self._establish_disruption_inventory_rules()
        self.commodity_inventory_rules = self._establish_commodity_specific_inventory_rules()
        self.warehouse_inventory_rules = self._establish_warehouse_specific_rules()
        self.critical_item_rules = self._establish_critical_item_rules()
        
    def _calculate_comprehensive_reorder_points(self) -> Dict[str, Dict[str, float]]:
        """Calculate STRICT reorder points with NO dynamic adjustment."""
        reorder_points = {}
        
        for (country, commodity, warehouse_type), group in self.ghsc_data.groupby(['Country', 'Commodity_Type', 'Warehouse_Type']):
            if len(group) == 0:
                continue
                
            key = f"{country}_{commodity}_{warehouse_type}"
            
            # Base calculations with NaN handling
            avg_lead_time = group['Lead_Time_Days'].mean()
            lead_time_max = group['Lead_Time_Days'].max()
            lead_time_std = group['Lead_Time_Days'].std()
            if pd.isna(lead_time_std):
                lead_time_std = avg_lead_time * 0.1  # Fallback to 10% of mean
            
            avg_order_volume = group['Order_Volume_Units'].mean()
            order_volume_std = group['Order_Volume_Units'].std()
            if pd.isna(order_volume_std):
                order_volume_std = avg_order_volume * 0.1  # Fallback to 10% of mean
            order_volume_min = group['Order_Volume_Units'].min()
            order_volume_max = group['Order_Volume_Units'].max()
            
            # Daily consumption (FIXED assumption, not dynamic)
            daily_consumption = avg_order_volume / 30.0
            daily_consumption_std = order_volume_std / 30.0
            
            # STRICT reorder point calculations (multiple levels)
            
            # Level 1: Basic reorder point = daily consumption * lead time
            basic_reorder_point = daily_consumption * avg_lead_time
            
            # Level 2: Conservative reorder point with buffers
            conservative_multiplier = 1.40  # 40% safety buffer (STRICT)
            conservative_reorder_point = daily_consumption * avg_lead_time * conservative_multiplier
            
            # Level 3: High-risk reorder point (for critical items)
            high_risk_multiplier = 1.75  # 75% safety buffer (MAXIMUM CONSERVATIVE)
            high_risk_reorder_point = daily_consumption * avg_lead_time * high_risk_multiplier
            
            # Level 4: Peak demand reorder point
            peak_multiplier = 2.0  # 100% safety buffer (extreme caution)
            peak_reorder_point = daily_consumption * avg_lead_time * peak_multiplier
            
            # Emergency trigger at critical low
            emergency_reorder_multiplier = 2.5  # 150% buffer for emergencies
            emergency_reorder_point = daily_consumption * avg_lead_time * emergency_reorder_multiplier
            
            reorder_points[key] = {
                # Base metrics
                'country': country,
                'commodity': commodity,
                'warehouse_type': warehouse_type,
                'daily_consumption': daily_consumption,
                'daily_consumption_std': daily_consumption_std,
                'avg_lead_time': avg_lead_time,
                'lead_time_max': lead_time_max,
                'lead_time_std': lead_time_std,
                
                # Reorder point levels (FIXED, NO adjustment)
                'basic_reorder_point': basic_reorder_point,
                'conservative_reorder_point': conservative_reorder_point,
                'high_risk_reorder_point': high_risk_reorder_point,
                'peak_demand_reorder_point': peak_reorder_point,
                'emergency_reorder_point': emergency_reorder_point,
                
                # Default to CONSERVATIVE for traditional system
                'reorder_point': conservative_reorder_point,
                'reorder_point_alt_high_risk': high_risk_reorder_point,
                'reorder_point_alt_peak': peak_reorder_point,
                
                # Safety margins (FIXED percentages)
                'safety_margin_primary': 0.40,
                'safety_margin_secondary': 0.75,
                'safety_margin_emergency': 1.50,
                
                # Min and Max order volumes
                'min_order_volume': order_volume_min,
                'max_order_volume': order_volume_max,
                'suggested_order_volume': order_volume_max,  # Order at max for safety
                
                # No dynamic adjustment (TRADITIONAL)
                'disruption_adjustment': 0.0,
                'seasonal_adjustment': 0.0,
                'demand_forecast_adjustment': 0.0,
                'stockout_history_adjustment': 0.0,
            }
        
        return reorder_points
    
    def _calculate_comprehensive_safety_stocks(self) -> Dict[str, Dict[str, float]]:
        """Calculate STRICT safety stock levels with MAXIMUM buffers."""
        safety_stocks = {}
        
        for (country, commodity, warehouse_type), group in self.ghsc_data.groupby(['Country', 'Commodity_Type', 'Warehouse_Type']):
            if len(group) == 0:
                continue
                
            key = f"{country}_{commodity}_{warehouse_type}"
            
            # Demand analysis with NaN handling
            avg_order_volume = group['Order_Volume_Units'].mean()
            std_order_volume = group['Order_Volume_Units'].std()
            if pd.isna(std_order_volume):
                std_order_volume = avg_order_volume * 0.1  # Fallback to 10% of mean
            min_order_volume = group['Order_Volume_Units'].min()
            max_order_volume = group['Order_Volume_Units'].max()
            
            avg_lead_time = group['Lead_Time_Days'].mean()
            lead_time_std = group['Lead_Time_Days'].std()
            if pd.isna(lead_time_std):
                lead_time_std = avg_lead_time * 0.1  # Fallback to 10% of mean
            
            # Service level factors (STRICT targets)
            service_level_99 = 2.33  # 99% service level (MAXIMUM)
            service_level_97 = 2.17  # 97% service level
            service_level_95 = 1.645  # 95% service level (Traditional default)
            service_level_90 = 1.28  # 90% service level (minimum acceptable)
            
            daily_demand_mean = avg_order_volume / 30.0
            daily_demand_std = std_order_volume / 30.0 if not pd.isna(std_order_volume) else (avg_order_volume * 0.25 / 30.0)
            
            lead_time_factor = np.sqrt(avg_lead_time)
            lead_time_factor_conservative = np.sqrt(avg_lead_time + lead_time_std)  # STRICT: add std
            lead_time_factor_extreme = np.sqrt(avg_lead_time + (lead_time_std * 2))  # EXTREME: add 2*std
            
            # Multiple safety stock levels
            
            # Level 1: Standard safety stock (95% service level)
            ss_standard = service_level_95 * daily_demand_std * lead_time_factor
            
            # Level 2: Conservative safety stock (97% service level)
            ss_conservative = service_level_97 * daily_demand_std * lead_time_factor_conservative
            
            # Level 3: High-risk safety stock (99% service level + extreme lead time)
            ss_high_risk = service_level_99 * daily_demand_std * lead_time_factor_extreme
            
            # Level 4: Maximum safety stock (emergency reserve)
            ss_maximum = service_level_99 * (daily_demand_std * 2) * lead_time_factor_extreme
            
            # Stockout frequency analysis
            avg_stockout_freq = group['Stockout_Frequency_per_Year'].mean()
            max_stockout_freq = group['Stockout_Frequency_per_Year'].max()
            
            # Multiplier for critical items (high stockout history)
            critical_multiplier = 1.5 if avg_stockout_freq > 0.05 else 1.0
            
            # Apply critical multiplier to safety stocks
            ss_standard_critical = ss_standard * critical_multiplier
            ss_conservative_critical = ss_conservative * critical_multiplier
            ss_high_risk_critical = ss_high_risk * critical_multiplier
            ss_maximum_critical = ss_maximum * critical_multiplier
            
            # Disruption impact analysis
            disrupted_group = group[group['Disruption_Severity'] > 2]
            if len(disrupted_group) > 0:
                disruption_lead_time_increase = (disrupted_group['Lead_Time_Days'].mean() / avg_lead_time)
                disruption_demand_increase = (disrupted_group['Order_Volume_Units'].mean() / avg_order_volume)
                disruption_multiplier = disruption_lead_time_increase * disruption_demand_increase
            else:
                disruption_multiplier = 1.0
            
            # Disruption-adjusted safety stocks
            ss_disruption = ss_conservative * disruption_multiplier * 1.5
            
            safety_stocks[key] = {
                # Service level targets (STRICT, NO compromise)
                'service_level_target': 0.99,  # 99% (MAXIMUM for traditional)
                'service_level_acceptable': 0.97,
                'service_level_minimum': 0.95,
                'service_level_failure': 0.90,  # Below 90% = failure
                
                # Demand parameters
                'daily_demand_mean': daily_demand_mean,
                'daily_demand_std': daily_demand_std,
                'demand_variability_factor': daily_demand_std / daily_demand_mean if daily_demand_mean > 0 else 0.25,
                
                # Lead time parameters
                'lead_time_mean': avg_lead_time,
                'lead_time_std': lead_time_std,
                'lead_time_factor': lead_time_factor,
                'lead_time_factor_conservative': lead_time_factor_conservative,
                'lead_time_factor_extreme': lead_time_factor_extreme,
                
                # Safety stock levels (MULTIPLE escalation levels)
                'safety_stock_standard': ss_standard,
                'safety_stock_conservative': ss_conservative,
                'safety_stock_high_risk': ss_high_risk,
                'safety_stock_maximum': ss_maximum,
                'safety_stock_critical_item': ss_conservative_critical,
                'safety_stock_high_risk_critical': ss_high_risk_critical,
                'safety_stock_maximum_critical': ss_maximum_critical,
                'safety_stock_disruption': ss_disruption,
                
                # Default (CONSERVATIVE for traditional system)
                'safety_stock': ss_conservative,
                
                # Stockout history triggers
                'avg_stockout_freq': avg_stockout_freq,
                'max_stockout_freq': max_stockout_freq,
                'critical_stockout_threshold': max(0.05, avg_stockout_freq * 1.5),
                'use_critical_multiplier': avg_stockout_freq > 0.05,
                'use_maximum_buffers': max_stockout_freq > 0.10,
                
                # Disruption triggers
                'avg_disruption_multiplier': disruption_multiplier,
                'use_disruption_buffers': disruption_multiplier > 1.1,
                
                # Order volume constraints
                'min_order_volume': min_order_volume,
                'max_order_volume': max_order_volume,
                'suggested_order_volume': max_order_volume,  # Conservative: order max
            }
        
        return safety_stocks
    
    def _establish_emergency_trigger_rules(self) -> Dict[str, Dict[str, Any]]:
        """Establish MULTIPLE emergency trigger levels for escalation."""
        emergency_rules = {}
        
        # Overall emergency thresholds
        overall_avg_cost = self.ghsc_data['Freight_Cost_USD'].mean()
        overall_avg_on_time = self.ghsc_data['On_Time_Delivery_%'].mean()
        overall_avg_delivery_delay = self.ghsc_data['Delivery_Delay_Days'].mean()
        overall_avg_reliability = self.ghsc_data['Supplier_Reliability_Score'].mean()
        overall_avg_stockout = self.ghsc_data['Stockout_Frequency_per_Year'].mean()
        overall_avg_resupply = self.ghsc_data['Resupply_Time_Days'].mean()
        overall_avg_disruption = self.ghsc_data['Disruption_Severity'].mean()
        
        emergency_rules['overall'] = {
            # Level 1: Monitor (data anomalies detected)
            'level_1_monitor': {
                'cost_threshold': overall_avg_cost * 1.10,
                'on_time_threshold': overall_avg_on_time * 0.95,
                'delay_threshold': overall_avg_delivery_delay * 1.20,
                'reliability_threshold': overall_avg_reliability * 0.95,
                'stockout_threshold': overall_avg_stockout * 1.15,
                'resupply_threshold': overall_avg_resupply * 1.10,
                'disruption_threshold': 1,
                'action': 'increase_monitoring',
                'approval_hours': 24,
            },
            
            # Level 2: Alert (multiple metrics degraded)
            'level_2_alert': {
                'cost_threshold': overall_avg_cost * 1.25,
                'on_time_threshold': overall_avg_on_time * 0.92,
                'delay_threshold': overall_avg_delivery_delay * 1.50,
                'reliability_threshold': overall_avg_reliability * 0.90,
                'stockout_threshold': overall_avg_stockout * 1.50,
                'resupply_threshold': overall_avg_resupply * 1.30,
                'disruption_threshold': 2,
                'action': 'activate_contingency',
                'approval_hours': 12,
            },
            
            # Level 3: Warning (significant degradation)
            'level_3_warning': {
                'cost_threshold': overall_avg_cost * 1.50,
                'on_time_threshold': overall_avg_on_time * 0.88,
                'delay_threshold': overall_avg_delivery_delay * 2.00,
                'reliability_threshold': overall_avg_reliability * 0.85,
                'stockout_threshold': overall_avg_stockout * 2.00,
                'resupply_threshold': overall_avg_resupply * 1.75,
                'disruption_threshold': 3,
                'action': 'emergency_procurement',
                'approval_hours': 6,
            },
            
            # Level 4: Critical (severe issues)
            'level_4_critical': {
                'cost_threshold': overall_avg_cost * 1.75,
                'on_time_threshold': overall_avg_on_time * 0.82,
                'delay_threshold': overall_avg_delivery_delay * 3.00,
                'reliability_threshold': overall_avg_reliability * 0.78,
                'stockout_threshold': overall_avg_stockout * 3.00,
                'resupply_threshold': overall_avg_resupply * 2.50,
                'disruption_threshold': 4,
                'action': 'crisis_management',
                'approval_hours': 2,
            },
            
            # Level 5: Emergency (extreme crisis)
            'level_5_emergency': {
                'cost_threshold': overall_avg_cost * 2.00,
                'on_time_threshold': overall_avg_on_time * 0.75,
                'delay_threshold': overall_avg_delivery_delay * 4.00,
                'reliability_threshold': overall_avg_reliability * 0.70,
                'stockout_threshold': overall_avg_stockout * 4.00,
                'resupply_threshold': overall_avg_resupply * 3.50,
                'disruption_threshold': 5,
                'action': 'emergency_executive_escalation',
                'approval_hours': 0.5,  # 30 minutes
            },
        }
        
        return emergency_rules
    
    def _establish_disruption_inventory_rules(self) -> Dict[str, Dict[str, Any]]:
        """Establish STRICT inventory rules for disruption scenarios."""
        disruption_rules = {}
        
        for disruption_type in self.ghsc_data['Disruption_Type'].unique():
            disruption_group = self.ghsc_data[self.ghsc_data['Disruption_Type'] == disruption_type]
            
            avg_severity = disruption_group['Disruption_Severity'].mean()
            if pd.isna(avg_severity):
                avg_severity = 2.0  # Default severity level
            max_severity = disruption_group['Disruption_Severity'].max()
            if pd.isna(max_severity):
                max_severity = avg_severity
            
            avg_lead_time_increase = (disruption_group['Lead_Time_Days'].mean() / 
                                     self.ghsc_data['Lead_Time_Days'].mean())
            avg_demand_increase = (disruption_group['Order_Volume_Units'].mean() / 
                                  self.ghsc_data['Order_Volume_Units'].mean())
            
            avg_delivery_delay = disruption_group['Delivery_Delay_Days'].mean()
            max_delivery_delay = disruption_group['Delivery_Delay_Days'].max()
            
            avg_on_time_impact = (disruption_group['On_Time_Delivery_%'].mean() / 
                                 self.ghsc_data['On_Time_Delivery_%'].mean())
            
            # Inventory multipliers for disruption
            lead_time_multiplier = max(1.0, avg_lead_time_increase)
            demand_multiplier = max(1.0, avg_demand_increase)
            combined_multiplier = lead_time_multiplier * demand_multiplier
            
            disruption_rules[disruption_type] = {
                'avg_severity': avg_severity,
                'max_severity': max_severity,
                'lead_time_multiplier': lead_time_multiplier,
                'demand_multiplier': demand_multiplier,
                'combined_multiplier': combined_multiplier,
                'reorder_point_multiplier': combined_multiplier * 1.5,  # 50% extra multiplier
                'safety_stock_multiplier': combined_multiplier * 2.0,  # 100% extra multiplier
                'max_acceptable_delay': max_delivery_delay,
                'avg_delay': avg_delivery_delay,
                'on_time_impact': avg_on_time_impact,
                
                # Escalation protocols
                'trigger_level': min(5, max(1, int(avg_severity))),
                'requires_emergency_procurement': avg_severity > 2.5,
                'requires_manual_approval': avg_severity > 2,
                'requires_director_escalation': avg_severity > 3.5,
                'stockpile_recommendation': combined_multiplier > 1.5,
            }
        
        return disruption_rules
    
    def _establish_commodity_specific_inventory_rules(self) -> Dict[str, Dict[str, Any]]:
        """Establish COMMODITY-SPECIFIC strict inventory rules."""
        commodity_rules = {}
        
        for commodity in self.ghsc_data['Commodity_Type'].unique():
            commodity_group = self.ghsc_data[self.ghsc_data['Commodity_Type'] == commodity]
            
            avg_volume = commodity_group['Order_Volume_Units'].mean()
            std_volume = commodity_group['Order_Volume_Units'].std()
            avg_stockout = commodity_group['Stockout_Frequency_per_Year'].mean()
            max_stockout = commodity_group['Stockout_Frequency_per_Year'].max()
            avg_on_time = commodity_group['On_Time_Delivery_%'].mean()
            avg_reliability = commodity_group['Supplier_Reliability_Score'].mean()
            
            # Determine criticality
            is_critical = avg_stockout > 0.05 or avg_on_time < 90
            
            # Multipliers based on criticality
            criticality_multiplier = 2.0 if is_critical else 1.0
            
            commodity_rules[commodity] = {
                'avg_order_volume': avg_volume,
                'std_order_volume': std_volume,
                'volume_tolerance': std_volume * 0.5,
                
                'avg_stockout_freq': avg_stockout,
                'max_stockout_freq': max_stockout,
                'stockout_critical_threshold': max(0.05, avg_stockout * 1.5),
                'use_critical_buffers': avg_stockout > 0.05,
                'use_maximum_buffers': max_stockout > 0.10,
                
                'is_critical_commodity': is_critical,
                'criticality_multiplier': criticality_multiplier,
                'requires_daily_tracking': is_critical,
                'requires_backup_supplier': max_stockout > 0.08,
                
                'avg_on_time_delivery': avg_on_time,
                'on_time_critical': avg_on_time < 90,
                'on_time_failure': avg_on_time < 85,
                
                'avg_supplier_reliability': avg_reliability,
                'reliability_critical': avg_reliability < 0.90,
                
                # Recommended inventory levels
                'reorder_point_multiplier': criticality_multiplier * 1.3,
                'safety_stock_multiplier': criticality_multiplier * 1.8,
                'max_recommended_order': avg_volume * 1.5,  # Conservative upper bound
                'min_recommended_order': avg_volume * 0.8,  # Conservative lower bound
            }
        
        return commodity_rules
    
    def _establish_warehouse_specific_rules(self) -> Dict[str, Dict[str, Any]]:
        """Establish WAREHOUSE-TYPE specific strict rules."""
        warehouse_rules = {}
        
        for warehouse_type in self.ghsc_data['Warehouse_Type'].unique():
            warehouse_group = self.ghsc_data[self.ghsc_data['Warehouse_Type'] == warehouse_type]
            
            avg_stockout = warehouse_group['Stockout_Frequency_per_Year'].mean()
            avg_resupply = warehouse_group['Resupply_Time_Days'].mean()
            avg_delivery_delay = warehouse_group['Delivery_Delay_Days'].mean()
            avg_on_time = warehouse_group['On_Time_Delivery_%'].mean()
            
            warehouse_rules[warehouse_type] = {
                'avg_stockout_freq': avg_stockout,
                'stockout_critical': avg_stockout > 0.05,
                'stockout_requires_investigation': avg_stockout > 0.03,
                
                'avg_resupply_time': avg_resupply,
                'resupply_target': avg_resupply * 0.85,
                'resupply_acceptable': avg_resupply * 1.10,
                'resupply_critical': avg_resupply * 1.50,
                
                'avg_delivery_delay': avg_delivery_delay,
                'delay_target': avg_delivery_delay * 0.75,
                'delay_acceptable': avg_delivery_delay * 1.25,
                'delay_critical': avg_delivery_delay * 2.00,
                
                'avg_on_time_delivery': avg_on_time,
                'on_time_target': 0.98,
                'on_time_acceptable': 0.95,
                'on_time_critical': 0.85,
                
                'requires_daily_audit': avg_stockout > 0.05,
                'requires_weekly_review': True,
                'requires_monthly_compliance_check': True,
            }
        
        return warehouse_rules
    
    def _establish_critical_item_rules(self) -> Dict[str, Dict[str, Any]]:
        """Identify CRITICAL items requiring MAXIMUM safety stocks."""
        critical_rules = {}
        
        # Identify critical items based on multiple factors
        for (country, commodity), group in self.ghsc_data.groupby(['Country', 'Commodity_Type']):
            avg_stockout = group['Stockout_Frequency_per_Year'].mean()
            avg_on_time = group['On_Time_Delivery_%'].mean()
            avg_delay = group['Delivery_Delay_Days'].mean()
            max_disruption = group['Disruption_Severity'].max()
            
            criticality_score = 0
            criticality_factors = []
            
            if avg_stockout > 0.08:
                criticality_score += 3
                criticality_factors.append(f'high_stockout_{avg_stockout:.3f}')
            if avg_on_time < 88:
                criticality_score += 2
                criticality_factors.append(f'low_on_time_{avg_on_time:.1f}%')
            if avg_delay > 10:
                criticality_score += 2
                criticality_factors.append(f'high_delay_{avg_delay:.1f}days')
            if max_disruption >= 4:
                criticality_score += 3
                criticality_factors.append(f'severe_disruption_{max_disruption}')
            
            key = f"{country}_{commodity}"
            critical_rules[key] = {
                'criticality_score': criticality_score,
                'is_critical_item': criticality_score >= 3,
                'criticality_factors': criticality_factors,
                'safety_stock_multiplier': 2.5 if criticality_score >= 5 else (1.8 if criticality_score >= 3 else 1.0),
                'reorder_point_multiplier': 2.0 if criticality_score >= 5 else (1.5 if criticality_score >= 3 else 1.0),
                'requires_backup_supplier': criticality_score >= 4,
                'requires_daily_monitoring': criticality_score >= 3,
                'requires_executive_escalation': criticality_score >= 6,
            }
        
        return critical_rules
    
    def get_comprehensive_inventory_decision(self, country: str, commodity: str, 
                                            warehouse_type: str,
                                            current_inventory: float,
                                            context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make inventory decision using EXTREMELY STRICT, COMPREHENSIVE rules.
        
        MAXIMUM CONSERVATIVE approach:
        - Check EVERY possible metric
        - Multiple escalation levels
        - Default to emergency procurement
        - Accumulate penalties for any deviation
        """
        
        key = f"{country}_{commodity}_{warehouse_type}"
        
        # Get rules (or defaults)
        reorder_info = self.reorder_rules.get(key, self._get_default_reorder())
        safety_info = self.safety_stock_rules.get(key, self._get_default_safety_stock())
        critical_key = f"{country}_{commodity}"
        critical_info = self.critical_item_rules.get(critical_key, {})
        
        # Determine which safety stock level to use (STRICT)
        use_critical = critical_info.get('is_critical_item', False)
        is_high_risk = context.get('Disruption_Severity', 0) > 2
        
        if use_critical and is_high_risk:
            safety_stock = safety_info.get('safety_stock_maximum_critical', safety_info['safety_stock'])
            reorder_point = reorder_info['emergency_reorder_point']
        elif use_critical:
            safety_stock = safety_info.get('safety_stock_high_risk_critical', safety_info['safety_stock'])
            reorder_point = reorder_info['high_risk_reorder_point']
        elif is_high_risk:
            safety_stock = safety_info.get('safety_stock_disruption', safety_info['safety_stock'])
            reorder_point = reorder_info['peak_demand_reorder_point']
        else:
            safety_stock = safety_info['safety_stock']
            reorder_point = reorder_info['reorder_point']
        
        # Initialize decision with COMPREHENSIVE tracking
        decision = {
            'action': 'no_action',
            'quantity': 0,
            'reasoning': 'inventory_adequate',
            'current_inventory': current_inventory,
            'reorder_point': reorder_point,
            'safety_stock': safety_stock,
            
            # Comprehensive violation tracking
            'violations': [],
            'warnings': [],
            'penalties': [],
            'escalation_level': 0,
            'approval_required': False,
            'approval_level': None,
            'approval_hours': 0,
            'compliance_score': 1.0,
        }
        
        # COMPREHENSIVE metrics checking (STRICT enforcement)
        
        # 1. INVENTORY LEVEL (primary decision driver)
        if current_inventory < safety_stock * 0.5:
            decision['violations'].append('critical_inventory_depletion')
            decision['escalation_level'] = max(decision['escalation_level'], 5)
            decision['compliance_score'] *= 0.5
        elif current_inventory < safety_stock:
            decision['violations'].append('inventory_below_safety_stock')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
            decision['compliance_score'] *= 0.7
        elif current_inventory < reorder_point:
            decision['warnings'].append('inventory_below_reorder_point')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
            decision['compliance_score'] *= 0.85
        
        # 2. STOCKOUT FREQUENCY (STRICT penalties)
        stockout_freq = context.get('Stockout_Frequency_per_Year', 0)
        if stockout_freq > 0.15:
            decision['violations'].append('critical_stockout_frequency')
            decision['escalation_level'] = max(decision['escalation_level'], 5)
        elif stockout_freq > 0.10:
            decision['violations'].append('high_stockout_frequency')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
        elif stockout_freq > 0.05:
            decision['warnings'].append('elevated_stockout_frequency')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
            decision['penalties'].append('stockout_frequency_elevated')
        
        # 3. DELIVERY DELAY (STRICT metric)
        delivery_delay = context.get('Delivery_Delay_Days', 0)
        max_acceptable_delay = reorder_info.get('lead_time_max', 100) * 0.3
        
        if delivery_delay > max_acceptable_delay * 2.0:
            decision['violations'].append('extreme_delivery_delay')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
        elif delivery_delay > max_acceptable_delay * 1.5:
            decision['violations'].append('severe_delivery_delay')
            decision['escalation_level'] = max(decision['escalation_level'], 3)
        elif delivery_delay > max_acceptable_delay:
            decision['warnings'].append('elevated_delivery_delay')
            decision['escalation_level'] = max(decision['escalation_level'], 1)
        
        # 4. SUPPLIER RELIABILITY (STRICT target)
        reliability = context.get('Supplier_Reliability_Score', 1.0)
        if reliability < 0.75:
            decision['violations'].append('critical_reliability_failure')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
        elif reliability < 0.85:
            decision['violations'].append('reliability_degradation')
            decision['escalation_level'] = max(decision['escalation_level'], 3)
        elif reliability < 0.90:
            decision['warnings'].append('reliability_below_target')
            decision['escalation_level'] = max(decision['escalation_level'], 1)
        
        # 5. ON-TIME DELIVERY (STRICT targets)
        on_time = context.get('On_Time_Delivery_%', 100) / 100
        if on_time < 0.80:
            decision['violations'].append('critical_on_time_failure')
            decision['escalation_level'] = max(decision['escalation_level'], 5)
        elif on_time < 0.90:
            decision['violations'].append('on_time_delivery_failure')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
        elif on_time < 0.95:
            decision['warnings'].append('on_time_delivery_degraded')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
            decision['penalties'].append('on_time_below_95_percent')
        
        # 6. DISRUPTION SEVERITY (AGGRESSIVE escalation)
        disruption_severity = context.get('Disruption_Severity', 0)
        if disruption_severity >= 4:
            decision['violations'].append(f'severe_disruption_level_{disruption_severity}')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
        elif disruption_severity >= 3:
            decision['violations'].append(f'major_disruption_level_{disruption_severity}')
            decision['escalation_level'] = max(decision['escalation_level'], 3)
        elif disruption_severity >= 2:
            decision['warnings'].append(f'moderate_disruption_level_{disruption_severity}')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
        elif disruption_severity >= 1:
            decision['warnings'].append(f'minor_disruption_level_{disruption_severity}')
        
        # 7. COST CONSTRAINTS (STRICT enforcement)
        freight_cost = context.get('Freight_Cost_USD', 0)
        cost_critical = reorder_info.get('daily_consumption', 0) * reorder_info.get('avg_lead_time', 50) * 0.4
        
        if freight_cost > cost_critical * 2.0:
            decision['violations'].append('extreme_cost_violation')
            decision['escalation_level'] = max(decision['escalation_level'], 3)
        elif freight_cost > cost_critical * 1.5:
            decision['violations'].append('severe_cost_violation')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
        
        # 8. CO2 EMISSIONS (environmental compliance)
        co2_emissions = context.get('CO2_Emissions_tons', 0)
        if co2_emissions > 15000:
            decision['penalties'].append('high_co2_emissions')
            decision['compliance_score'] *= 0.9
        
        # 9. RESUPPLY TIME (STRICT)
        resupply_time = context.get('Resupply_Time_Days', 0)
        if resupply_time > 50:
            decision['warnings'].append('excessive_resupply_time')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
        
        # 10. CRITICAL ITEM STATUS (MAXIMUM safeguards)
        if use_critical:
            decision['penalties'].append('critical_commodity_status')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
        
        # DECISION LOGIC with STRICT escalation
        
        if decision['escalation_level'] >= 5:
            emergency_quantity = reorder_info['daily_consumption'] * reorder_info['lead_time'] * 3.0
            decision.update({
                'action': 'emergency_procurement_maximum',
                'quantity': emergency_quantity,
                'reasoning': 'critical_emergency_detected',
                'urgency': 'emergency',
                'approval_required': True,
                'approval_level': 'executive_team',
                'approval_hours': 0.5,
            })
        
        elif decision['escalation_level'] >= 4:
            emergency_quantity = reorder_info['daily_consumption'] * reorder_info['lead_time'] * 2.5
            decision.update({
                'action': 'emergency_procurement',
                'quantity': emergency_quantity,
                'reasoning': 'critical_violations_multiple',
                'urgency': 'critical',
                'approval_required': True,
                'approval_level': 'director+cfo',
                'approval_hours': 1,
            })
        
        elif decision['escalation_level'] >= 3:
            high_quantity = reorder_info['daily_consumption'] * reorder_info['lead_time'] * 2.0
            decision.update({
                'action': 'high_priority_replenishment',
                'quantity': high_quantity,
                'reasoning': 'significant_violations_triggered',
                'urgency': 'high',
                'approval_required': True,
                'approval_level': 'manager',
                'approval_hours': 2,
            })
        
        elif decision['escalation_level'] >= 2:
            regular_quantity = reorder_info['daily_consumption'] * reorder_info['lead_time'] * 1.5
            decision.update({
                'action': 'standard_replenishment',
                'quantity': regular_quantity,
                'reasoning': 'warnings_and_minor_violations',
                'urgency': 'medium',
                'approval_required': True,
                'approval_level': 'supervisor',
                'approval_hours': 4,
            })
        
        elif current_inventory < reorder_point or decision['penalties']:
            regular_quantity = reorder_info['daily_consumption'] * reorder_info['lead_time'] * 1.3
            decision.update({
                'action': 'standard_replenishment',
                'quantity': regular_quantity,
                'reasoning': 'reorder_point_triggered_or_penalties',
                'urgency': 'medium',
                'approval_required': True,
                'approval_level': 'coordinator',
                'approval_hours': 8,
            })
        
        else:
            decision.update({
                'action': 'continue_monitoring',
                'quantity': 0,
                'reasoning': 'inventory_levels_acceptable',
                'urgency': 'none',
                'approval_required': False,
            })
        
        return decision
    
    def _get_default_reorder(self) -> Dict[str, float]:
        """Default reorder rules."""
        return {
            'daily_consumption': 100000,
            'lead_time': 50,
            'basic_reorder_point': 5000000,
            'conservative_reorder_point': 7000000,
            'high_risk_reorder_point': 8750000,
            'peak_demand_reorder_point': 10000000,
            'emergency_reorder_point': 12500000,
            'reorder_point': 7000000,
            'lead_time_max': 100,
        }
    
    def _get_default_safety_stock(self) -> Dict[str, float]:
        """Default safety stock rules."""
        return {
            'safety_stock_standard': 2000000,
            'safety_stock_conservative': 3000000,
            'safety_stock_high_risk': 4000000,
            'safety_stock_maximum': 5000000,
            'safety_stock_critical_item': 4500000,
            'safety_stock_high_risk_critical': 6000000,
            'safety_stock_maximum_critical': 7500000,
            'safety_stock_disruption': 5500000,
            'safety_stock': 3000000,
        }
    
    def calculate_traditional_inventory_metrics(self) -> Dict[str, float]:
        """Calculate traditional inventory management performance."""
        
        avg_stockout_freq = self.ghsc_data['Stockout_Frequency_per_Year'].mean()
        avg_resupply = self.ghsc_data['Resupply_Time_Days'].mean()
        on_time_delivery = self.ghsc_data['On_Time_Delivery_%'].mean() / 100.0
        avg_reliability = self.ghsc_data['Supplier_Reliability_Score'].mean()
        avg_delivery_delay = self.ghsc_data['Delivery_Delay_Days'].mean()
        
        # Violation rates
        stockout_violations = len(self.ghsc_data[self.ghsc_data['Stockout_Frequency_per_Year'] > 0.08])
        delay_violations = len(self.ghsc_data[self.ghsc_data['Delivery_Delay_Days'] > 10])
        on_time_violations = len(self.ghsc_data[self.ghsc_data['On_Time_Delivery_%'] < 90])
        
        return {
            'traditional_stockout_frequency': avg_stockout_freq,
            'traditional_resupply_time_days': avg_resupply,
            'traditional_on_time_delivery_pct': on_time_delivery * 100,
            'traditional_supplier_reliability': avg_reliability,
            'traditional_delivery_delay_days': avg_delivery_delay,
            'traditional_stockout_violation_rate': stockout_violations / len(self.ghsc_data),
            'traditional_delay_violation_rate': delay_violations / len(self.ghsc_data),
            'traditional_on_time_violation_rate': on_time_violations / len(self.ghsc_data),
            'manual_decision_delay_hours': 24,
        }


if __name__ == "__main__":
    ghsc_data = pd.read_csv('data/DATA_SPLITS/GHSC_PSM_Synthetic_Resilience_Dataset_v2_consistent_traindata.csv')
    
    enhanced_inventory = EnhancedReorderSafetyStockRules(ghsc_data)
    
    performance = enhanced_inventory.calculate_traditional_inventory_metrics()
    print("ENHANCED Traditional Inventory Performance:")
    for metric, value in sorted(performance.items()):
        print(f"  {metric}: {value:.4f}")
    
    test_context = {
        'Stockout_Frequency_per_Year': 0.12,
        'Delivery_Delay_Days': 8,
        'Supplier_Reliability_Score': 0.78,
        'On_Time_Delivery_%': 88,
        'Disruption_Severity': 3,
        'Freight_Cost_USD': 180000,
        'CO2_Emissions_tons': 18000,
        'Resupply_Time_Days': 35,
    }
    
    decision = enhanced_inventory.get_comprehensive_inventory_decision(
        'Nigeria', 'Malaria_RDT', 'Clinic', 5000000, test_context
    )
    print(f"\nSample Comprehensive Inventory Decision:")
    for key, value in decision.items():
        print(f"  {key}: {value}")
