"""
ENHANCED Traditional Baseline: Comprehensive Fixed Lead Time and Supplier Rules
Based on REAL GHSC, LPI, Disaster, and Emergency data with STRICT enforcement.

Uses actual column names from datasets:
GHSC columns: Lead_Time_Days, Supplier_Reliability_Score, Delivery_Delay_Days, 
              Disruption_Severity, CO2_Emissions_tons, Freight_Cost_USD, 
              Warehouse_Type, Transport_Mode, On_Time_Delivery_%, 
              Resupply_Time_Days, Stockout_Frequency_per_Year
LPI columns: LPI Score, Customs Score, Infrastructure Score, etc.
Disaster columns: Total Deaths, Total Damage, Start Month, End Month, etc.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EnhancedFixedLeadTimeSupplierRules:
    """
    STRICT Traditional supplier selection system with extensive rules enforcement.
    
    Key Characteristics:
    - Fixed rules that CANNOT adapt to changing conditions
    - Multiple escalation levels for each decision criterion
    - Comprehensive penalty system for any deviation
    - Strict compliance checking on ALL available metrics
    - Conservative thresholds that prioritize stability over efficiency
    """
    
    def __init__(self, ghsc_data: pd.DataFrame, lpi_data: Optional[pd.DataFrame] = None):
        """Initialize with GHSC supply chain data and optional LPI data."""
        self.ghsc_data = ghsc_data
        self.lpi_data = lpi_data
        
        # Calculate all fixed rules upfront (no adaptation)
        self.preferred_suppliers = self._establish_comprehensive_supplier_rules()
        self.fixed_lead_times = self._calculate_comprehensive_lead_times()
        self.transport_preferences = self._establish_strict_transport_rules()
        self.cost_constraints = self._establish_cost_thresholds()
        self.emissions_constraints = self._establish_emissions_thresholds()
        self.reliability_constraints = self._establish_reliability_thresholds()
        self.disruption_response_rules = self._establish_disruption_rules()
        self.warehouse_rules = self._establish_warehouse_type_rules()
        self.commodity_specific_rules = self._establish_commodity_specific_rules()
        
    def _establish_comprehensive_supplier_rules(self) -> Dict[str, Dict[str, Any]]:
        """Establish STRICT preferred supplier rules by commodity, country, and warehouse type."""
        supplier_rules = {}
        
        for commodity, commodity_group in self.ghsc_data.groupby('Commodity_Type'):
            commodity_rules = {}
            
            for country, country_group in commodity_group.groupby('Country'):
                country_rules = {}
                
                for warehouse_type, warehouse_group in country_group.groupby('Warehouse_Type'):
                    # STRICT: Calculate multiple thresholds
                    avg_reliability = warehouse_group['Supplier_Reliability_Score'].mean()
                    min_reliability = warehouse_group['Supplier_Reliability_Score'].min()
                    max_reliability = warehouse_group['Supplier_Reliability_Score'].max()
                    std_reliability = warehouse_group['Supplier_Reliability_Score'].std()
                    
                    avg_lead_time = warehouse_group['Lead_Time_Days'].mean()
                    avg_delay = warehouse_group['Delivery_Delay_Days'].mean()
                    max_delay = warehouse_group['Delivery_Delay_Days'].max()
                    
                    avg_on_time = warehouse_group['On_Time_Delivery_%'].mean()
                    min_on_time = warehouse_group['On_Time_Delivery_%'].min()
                    
                    avg_cost = warehouse_group['Freight_Cost_USD'].mean()
                    max_cost = warehouse_group['Freight_Cost_USD'].max()
                    cost_std = warehouse_group['Freight_Cost_USD'].std()
                    
                    avg_stockout_freq = warehouse_group['Stockout_Frequency_per_Year'].mean()
                    max_stockout_freq = warehouse_group['Stockout_Frequency_per_Year'].max()
                    
                    avg_resupply = warehouse_group['Resupply_Time_Days'].mean()
                    max_disruption = warehouse_group['Disruption_Severity'].max()
                    
                    key = f"{warehouse_type}"
                    country_rules[key] = {
                        # Primary supplier metrics (STRICT thresholds)
                        'primary_supplier_reliability': avg_reliability,
                        'reliability_min_acceptable': min(0.80, avg_reliability * 0.85),  # STRICT: 80% or below 85% of avg
                        'reliability_failure_threshold': 0.75,  # STRICT: fail if below 75%
                        'reliability_critical_threshold': 0.70,  # CRITICAL: below 70% triggers escalation
                        
                        # Lead time rules (STRICT, no flexibility)
                        'preferred_lead_time': avg_lead_time,
                        'max_acceptable_lead_time': avg_lead_time + 5,  # STRICT: max +5 days
                        'critical_lead_time': avg_lead_time + 10,  # CRITICAL: above this
                        'lead_time_safety_buffer': 0.20,  # 20% fixed buffer (STRICT)
                        'lead_time_seasonal_multiplier': 1.3,  # For peak seasons (STRICT)
                        
                        # On-time delivery (STRICT targets)
                        'on_time_target': max(0.95, avg_on_time),  # Target: 95% or current if higher
                        'on_time_min_acceptable': 0.90,  # STRICT: must be 90%+
                        'on_time_critical': 0.85,  # CRITICAL: below 85% triggers review
                        'on_time_failure': 0.80,  # FAILURE: below 80% requires action
                        
                        # Cost constraints (STRICT enforcement)
                        'preferred_cost': avg_cost,
                        'cost_tolerance': min(cost_std * 0.5, avg_cost * 0.10),  # Tight tolerance
                        'cost_warning_threshold': avg_cost * 1.15,  # 15% over budget = WARNING
                        'cost_critical_threshold': avg_cost * 1.30,  # 30% over budget = CRITICAL
                        'cost_failure_threshold': avg_cost * 1.50,  # 50% over budget = FAIL
                        
                        # Disruption handling (CONSERVATIVE)
                        'max_acceptable_disruption': 2,  # STRICT: max severity 2
                        'disruption_response_delay': 0.5,  # Days of lag before response
                        'backup_activation_disruption': 3,  # Activate backup at disruption >= 3
                        
                        # Stockout frequency (STRICT penalties)
                        'stockout_frequency_target': avg_stockout_freq,
                        'stockout_frequency_warning': avg_stockout_freq * 1.5,
                        'stockout_frequency_critical': max(0.08, avg_stockout_freq * 2.0),
                        
                        # Resupply time (STRICT)
                        'max_acceptable_resupply': max(avg_resupply, 30),
                        'resupply_critical': avg_resupply * 1.5,
                        
                        # Switching rules (VERY CONSERVATIVE)
                        'switching_allowed': False,  # Traditional: NO dynamic switching
                        'switching_requires_approval': True,  # Requires manual approval
                        'backup_switch_requires_multiple_failures': True,  # Multiple factors must fail
                        'min_failures_to_switch': 3,  # Must violate at least 3 constraints
                        
                        # Response latency (Traditional is slow)
                        'decision_approval_delay_hours': 24,  # 24 hours for decisions
                        'emergency_approval_delay_hours': 8,  # 8 hours for emergencies
                        
                        # Audit and compliance
                        'compliance_tracking': True,
                        'audit_frequency_days': 7,
                        'escalation_review': True,
                        'warehouse_type': warehouse_type,
                    }
                
                commodity_rules[country] = country_rules
            
            supplier_rules[commodity] = commodity_rules
        
        return supplier_rules
    
    def _calculate_comprehensive_lead_times(self) -> Dict[str, Dict[str, Any]]:
        """Calculate STRICT fixed lead time rules with NO dynamic adjustment."""
        lead_time_rules = {}
        
        grouping_cols = ['Commodity_Type', 'Country', 'Transport_Mode', 'Warehouse_Type']
        
        for group_key, group_data in self.ghsc_data.groupby(grouping_cols):
            commodity, country, transport_mode, warehouse_type = group_key
            
            # Calculate comprehensive lead time metrics
            base_lead_time = group_data['Lead_Time_Days'].mean()
            lead_time_std = group_data['Lead_Time_Days'].std()
            lead_time_min = group_data['Lead_Time_Days'].min()
            lead_time_max = group_data['Lead_Time_Days'].max()
            
            # Delivery delay analysis
            avg_delay = group_data['Delivery_Delay_Days'].mean()
            max_delay = group_data['Delivery_Delay_Days'].max()
            delay_std = group_data['Delivery_Delay_Days'].std()
            
            # On-time delivery analysis
            on_time_pct = group_data['On_Time_Delivery_%'].mean()
            
            # STRICT fixed buffers (NO dynamic adjustment)
            primary_buffer = 0.25  # 25% base buffer (STRICT)
            secondary_buffer = 0.40  # 40% high-risk buffer
            peak_season_buffer = 0.50  # 50% peak season buffer
            disruption_buffer = 0.75  # 75% disruption buffer
            
            # Calculate fixed lead times with buffers
            fixed_lead_time = base_lead_time * (1 + primary_buffer)
            fixed_high_risk_lead_time = base_lead_time * (1 + secondary_buffer)
            fixed_peak_lead_time = base_lead_time * (1 + peak_season_buffer)
            fixed_disruption_lead_time = base_lead_time * (1 + disruption_buffer)
            
            key = f"{commodity}_{country}_{transport_mode}_{warehouse_type}"
            lead_time_rules[key] = {
                # Base calculations (FIXED, not updated)
                'base_lead_time': base_lead_time,
                'lead_time_std': lead_time_std,
                'lead_time_min': lead_time_min,
                'lead_time_max': lead_time_max,
                
                # Fixed buffers (NO dynamic adjustment)
                'primary_buffer': primary_buffer,
                'secondary_buffer': secondary_buffer,
                'peak_season_buffer': peak_season_buffer,
                'disruption_buffer': disruption_buffer,
                'fixed_lead_time': fixed_lead_time,
                'fixed_high_risk_lead_time': fixed_high_risk_lead_time,
                'fixed_peak_lead_time': fixed_peak_lead_time,
                'fixed_disruption_lead_time': fixed_disruption_lead_time,
                
                # Delay analysis (used for penalties, not adjustment)
                'average_delay': avg_delay,
                'max_delay': max_delay,
                'delay_std': delay_std,
                'on_time_delivery_pct': on_time_pct,
                
                # STRICT policies (NO flexibility)
                'disruption_adjustment': 0.0,  # TRADITIONAL: zero dynamic adjustment
                'seasonal_adjustment': 0.0,  # TRADITIONAL: no seasonal optimization
                'weather_adjustment': 0.0,  # TRADITIONAL: ignore weather
                'demand_forecast_adjustment': 0.0,  # TRADITIONAL: ignore forecasts
                'predictive_adjustment': 0.0,  # TRADITIONAL: no ML/AI adjustments
                
                # Manual approval requirements (SLOW)
                'requires_manual_approval': True,
                'approval_delay_hours': 24,
                'emergency_approval_hours': 8,
                'emergency_requires_director_approval': True,
            }
        
        return lead_time_rules
    
    def _establish_strict_transport_rules(self) -> Dict[str, Dict[str, Any]]:
        """Establish VERY STRICT transport mode preferences with NO switching."""
        transport_preferences = {}
        
        for commodity, commodity_group in self.ghsc_data.groupby('Commodity_Type'):
            mode_analysis = {}
            
            for transport_mode, mode_group in commodity_group.groupby('Transport_Mode'):
                # Calculate comprehensive metrics
                avg_cost = mode_group['Freight_Cost_USD'].mean()
                cost_std = mode_group['Freight_Cost_USD'].std()
                min_cost = mode_group['Freight_Cost_USD'].min()
                max_cost = mode_group['Freight_Cost_USD'].max()
                
                avg_lead_time = mode_group['Lead_Time_Days'].mean()
                lead_time_std = mode_group['Lead_Time_Days'].std()
                
                avg_reliability = mode_group['On_Time_Delivery_%'].mean()
                min_reliability = mode_group['On_Time_Delivery_%'].min()
                
                avg_delay = mode_group['Delivery_Delay_Days'].mean()
                max_delay = mode_group['Delivery_Delay_Days'].max()
                
                avg_co2 = mode_group['CO2_Emissions_tons'].mean()
                max_co2 = mode_group['CO2_Emissions_tons'].max()
                
                avg_resupply = mode_group['Resupply_Time_Days'].mean()
                
                mode_analysis[transport_mode] = {
                    'avg_cost': avg_cost,
                    'cost_std': cost_std,
                    'min_cost': min_cost,
                    'max_cost': max_cost,
                    'cost_tolerance': cost_std * 0.5,  # Tight tolerance
                    'cost_warning': avg_cost * 1.20,  # 20% warning threshold
                    'cost_critical': avg_cost * 1.50,  # 50% critical threshold
                    
                    'avg_lead_time': avg_lead_time,
                    'lead_time_std': lead_time_std,
                    'lead_time_acceptable': avg_lead_time + (lead_time_std * 1.0),
                    'lead_time_critical': avg_lead_time + (lead_time_std * 2.0),
                    
                    'avg_reliability': avg_reliability,
                    'min_reliability': min_reliability,
                    'reliability_target': max(0.95, avg_reliability),
                    'reliability_critical': 0.85,
                    
                    'avg_delay': avg_delay,
                    'max_delay': max_delay,
                    'delay_critical_threshold': avg_delay + (max_delay * 0.5),
                    
                    'avg_co2': avg_co2,
                    'max_co2': max_co2,
                    'co2_warning_threshold': avg_co2 * 1.25,
                    'co2_critical_threshold': avg_co2 * 1.50,
                    
                    'avg_resupply': avg_resupply,
                    'usage_frequency': len(mode_group),
                    'reliability_score': (avg_reliability * 0.4) + (1 - (avg_cost / max_cost)) * 0.3 + (1 - (avg_lead_time / (avg_lead_time * 2))) * 0.3
                }
            
            # Select PRIMARY mode (STRICTLY adhered to)
            best_mode = min(mode_analysis.keys(), 
                          key=lambda x: (mode_analysis[x]['avg_cost'] / max(mode_analysis[x]['avg_reliability'], 1)))
            
            transport_preferences[commodity] = {
                'primary_mode': best_mode,
                'mode_analysis': mode_analysis,
                
                # STRICT switching policy (NO flexibility)
                'switching_policy': 'failure_only',
                'backup_modes': [m for m in mode_analysis.keys() if m != best_mode],
                'switching_requires_approval': True,
                'approval_delay_hours': 24,
                
                # Cost thresholds (VERY STRICT)
                'cost_threshold': mode_analysis[best_mode]['avg_cost'] * 1.20,  # 20% threshold
                'emergency_cost_threshold': mode_analysis[best_mode]['avg_cost'] * 1.50,  # 50% threshold
                
                # Lead time thresholds (STRICT)
                'lead_time_threshold': mode_analysis[best_mode]['avg_lead_time'] * 1.25,
                'lead_time_emergency': mode_analysis[best_mode]['avg_lead_time'] * 1.75,
                
                # Reliability thresholds (STRICT)
                'reliability_threshold': 0.90,
                'reliability_critical': 0.80,
                
                # Emissions constraints (NEW: environmental compliance)
                'co2_threshold': mode_analysis[best_mode]['avg_co2'] * 1.20,
                'co2_critical': mode_analysis[best_mode]['avg_co2'] * 1.50,
                'prefer_low_emission_modes': True,
                
                # Penalty escalation
                'penalty_multiplier_per_violation': 1.15,
                'max_violations_before_escalation': 2,
            }
        
        return transport_preferences
    
    def _establish_cost_thresholds(self) -> Dict[str, Any]:
        """Establish STRICT cost control thresholds with penalties."""
        cost_rules = {}
        
        overall_avg_cost = self.ghsc_data['Freight_Cost_USD'].mean()
        overall_std_cost = self.ghsc_data['Freight_Cost_USD'].std()
        overall_min_cost = self.ghsc_data['Freight_Cost_USD'].min()
        overall_max_cost = self.ghsc_data['Freight_Cost_USD'].max()
        
        cost_rules['overall'] = {
            'avg_cost': overall_avg_cost,
            'std_cost': overall_std_cost,
            'min_cost': overall_min_cost,
            'max_cost': overall_max_cost,
            
            # STRICT enforcement levels
            'budget_target': overall_avg_cost,
            'budget_acceptable': overall_avg_cost * 1.10,  # 10% tolerance
            'budget_warning': overall_avg_cost * 1.20,  # 20% warning
            'budget_critical': overall_avg_cost * 1.35,  # 35% critical
            'budget_failure': overall_avg_cost * 1.50,  # 50% requires escalation
            
            # Cost per unit penalties
            'cost_per_unit_target': overall_avg_cost / self.ghsc_data['Order_Volume_Units'].mean(),
            'cost_per_unit_warning': (overall_avg_cost * 1.20) / self.ghsc_data['Order_Volume_Units'].mean(),
            'cost_per_unit_critical': (overall_avg_cost * 1.50) / self.ghsc_data['Order_Volume_Units'].mean(),
        }
        
        # Cost rules by commodity
        for commodity, commodity_group in self.ghsc_data.groupby('Commodity_Type'):
            avg_cost = commodity_group['Freight_Cost_USD'].mean()
            std_cost = commodity_group['Freight_Cost_USD'].std()
            
            cost_rules[commodity] = {
                'avg_cost': avg_cost,
                'std_cost': std_cost,
                'budget_tolerance': std_cost * 0.5,
                'warning_threshold': avg_cost * 1.15,
                'critical_threshold': avg_cost * 1.40,
                'escalation_required_above': avg_cost * 1.60,
            }
        
        return cost_rules
    
    def _establish_emissions_thresholds(self) -> Dict[str, Any]:
        """Establish STRICT CO2 emissions constraints (environmental compliance)."""
        emissions_rules = {}
        
        overall_avg_co2 = self.ghsc_data['CO2_Emissions_tons'].mean()
        overall_std_co2 = self.ghsc_data['CO2_Emissions_tons'].std()
        overall_max_co2 = self.ghsc_data['CO2_Emissions_tons'].max()
        
        emissions_rules['overall'] = {
            'avg_co2': overall_avg_co2,
            'std_co2': overall_std_co2,
            'max_co2': overall_max_co2,
            
            # STRICT environmental targets
            'co2_target': overall_avg_co2 * 0.85,  # Reduce by 15%
            'co2_acceptable': overall_avg_co2,
            'co2_warning': overall_avg_co2 * 1.15,
            'co2_critical': overall_avg_co2 * 1.35,
            'co2_penalty_threshold': overall_avg_co2 * 1.50,
            'co2_violation_triggers_audit': True,
        }
        
        # By transport mode
        for transport_mode, mode_group in self.ghsc_data.groupby('Transport_Mode'):
            avg_co2 = mode_group['CO2_Emissions_tons'].mean()
            std_co2 = mode_group['CO2_Emissions_tons'].std()
            
            emissions_rules[transport_mode] = {
                'avg_co2': avg_co2,
                'std_co2': std_co2,
                'co2_target': avg_co2 * 0.80,
                'co2_warning': avg_co2 * 1.20,
                'co2_critical': avg_co2 * 1.50,
            }
        
        return emissions_rules
    
    def _establish_reliability_thresholds(self) -> Dict[str, Any]:
        """Establish STRICT reliability metrics with NO tolerance."""
        reliability_rules = {}
        
        overall_avg_reliability = self.ghsc_data['Supplier_Reliability_Score'].mean()
        overall_min_reliability = self.ghsc_data['Supplier_Reliability_Score'].min()
        
        reliability_rules['overall'] = {
            'avg_reliability': overall_avg_reliability,
            'min_reliability': overall_min_reliability,
            
            # STRICT thresholds (NO tolerance for poor performance)
            'target_reliability': 0.95,
            'acceptable_reliability': 0.90,
            'warning_reliability': 0.85,
            'critical_reliability': 0.80,
            'failure_reliability': 0.75,
            'require_supplier_replacement': 0.70,
            
            # On-time delivery targets
            'on_time_target': 0.98,
            'on_time_acceptable': 0.95,
            'on_time_warning': 0.90,
            'on_time_critical': 0.85,
        }
        
        return reliability_rules
    
    def _establish_disruption_rules(self) -> Dict[str, Any]:
        """Establish STRICT disruption response rules with multiple severity levels."""
        disruption_rules = {}
        
        max_disruption = self.ghsc_data['Disruption_Severity'].max()
        avg_disruption = self.ghsc_data['Disruption_Severity'].mean()
        
        # By disruption type
        disruption_types = self.ghsc_data['Disruption_Type'].unique()
        
        for disruption_type in disruption_types:
            disruption_group = self.ghsc_data[self.ghsc_data['Disruption_Type'] == disruption_type]
            
            avg_severity = disruption_group['Disruption_Severity'].mean()
            max_severity = disruption_group['Disruption_Severity'].max()
            avg_impact_on_delivery = disruption_group['Delivery_Delay_Days'].mean()
            avg_impact_on_reliability = 1 - (disruption_group['On_Time_Delivery_%'].mean() / 100)
            
            disruption_rules[disruption_type] = {
                'avg_severity': avg_severity,
                'max_severity': max_severity,
                'avg_delay_impact': avg_impact_on_delivery,
                'avg_reliability_impact': avg_impact_on_reliability,
                
                # Escalation levels (STRICT, NO proactive switching)
                'response_level_1': 1,  # Monitor only
                'response_level_2': 2,  # Increased monitoring
                'response_level_3': 3,  # Consider alternatives
                'response_level_4': 4,  # Activate backup supplier
                'response_level_5': 5,  # Emergency protocols + escalation
                
                # Response delays (SLOW, Traditional)
                'level_1_response_delay_hours': 24,
                'level_2_response_delay_hours': 18,
                'level_3_response_delay_hours': 12,
                'level_4_response_delay_hours': 6,
                'level_5_response_delay_hours': 2,
                
                # Approval requirements
                'level_1_approval': 'supervisor',
                'level_2_approval': 'manager',
                'level_3_approval': 'director',
                'level_4_approval': 'director+cfo',
                'level_5_approval': 'executive_team',
            }
        
        return disruption_rules
    
    def _establish_warehouse_type_rules(self) -> Dict[str, Dict[str, Any]]:
        """Establish STRICT warehouse type operational rules."""
        warehouse_rules = {}
        
        for warehouse_type, warehouse_group in self.ghsc_data.groupby('Warehouse_Type'):
            avg_stockout = warehouse_group['Stockout_Frequency_per_Year'].mean()
            avg_resupply = warehouse_group['Resupply_Time_Days'].mean()
            avg_delay = warehouse_group['Delivery_Delay_Days'].mean()
            
            warehouse_rules[warehouse_type] = {
                'avg_stockout_freq': avg_stockout,
                'stockout_critical_threshold': max(0.05, avg_stockout * 1.5),
                'stockout_requires_investigation': avg_stockout * 1.25,
                
                'avg_resupply_time': avg_resupply,
                'resupply_target': avg_resupply * 0.90,
                'resupply_acceptable': avg_resupply * 1.05,
                'resupply_critical': avg_resupply * 1.30,
                
                'avg_delivery_delay': avg_delay,
                'delay_target': avg_delay * 0.80,
                'delay_acceptable': avg_delay * 1.15,
                'delay_critical': avg_delay * 1.50,
                
                'requires_daily_audit': avg_stockout > 0.05,
                'requires_weekly_review': True,
            }
        
        return warehouse_rules
    
    def _establish_commodity_specific_rules(self) -> Dict[str, Dict[str, Any]]:
        """Establish STRICT commodity-specific rules."""
        commodity_rules = {}
        
        for commodity, commodity_group in self.ghsc_data.groupby('Commodity_Type'):
            avg_volume = commodity_group['Order_Volume_Units'].mean()
            std_volume = commodity_group['Order_Volume_Units'].std()
            avg_stockout = commodity_group['Stockout_Frequency_per_Year'].mean()
            
            commodity_rules[commodity] = {
                'avg_order_volume': avg_volume,
                'std_order_volume': std_volume,
                'min_order_volume': max(avg_volume * 0.7, commodity_group['Order_Volume_Units'].min()),
                'max_order_volume': min(avg_volume * 1.3, commodity_group['Order_Volume_Units'].max()),
                'order_tolerance': std_volume * 0.5,
                
                'target_stockout_freq': max(0, avg_stockout * 0.8),
                'acceptable_stockout_freq': avg_stockout * 1.2,
                'critical_stockout_freq': avg_stockout * 2.0,
                
                'critical_commodity': avg_stockout > 0.05,  # High-value/critical
                'requires_daily_tracking': avg_stockout > 0.05,
                'requires_backup_supplier': avg_stockout > 0.10,
            }
        
        return commodity_rules
    
    def get_enhanced_supplier_decision(self, commodity: str, country: str, 
                                       warehouse_type: str,
                                       current_reliability: float,
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make supplier selection decision using STRICT, COMPREHENSIVE rules.
        
        STRICT logic:
        - Multiple criteria checked simultaneously
        - No exceptions to established thresholds
        - Conservative bias (prefer stability over efficiency)
        - Comprehensive penalty accumulation
        """
        
        if commodity not in self.preferred_suppliers:
            return self._get_default_enhanced_decision()
        
        commodity_rules = self.preferred_suppliers[commodity]
        
        if country not in commodity_rules:
            return self._get_default_enhanced_decision()
        
        country_rules = commodity_rules[country]
        
        if warehouse_type not in country_rules:
            warehouse_type = list(country_rules.keys())[0] if country_rules else 'default'
        
        supplier_rule = country_rules.get(warehouse_type, {})
        if not supplier_rule:
            return self._get_default_enhanced_decision()
        
        # Initialize decision with COMPREHENSIVE tracking
        decision = {
            'action': 'continue_primary_supplier',
            'supplier_type': 'primary',
            'reasoning': 'within_acceptable_range',
            'current_reliability': current_reliability,
            'threshold': supplier_rule.get('reliability_failure_threshold', 0.75),
            
            # Comprehensive metrics tracking
            'violations': [],
            'warnings': [],
            'penalties': [],
            'escalation_level': 0,
            'approval_required': False,
            'approval_level': None,
            'approval_delay_hours': 0,
            'strict_compliance_score': 1.0,
        }
        
        # STRICT evaluation on ALL dimensions
        
        # 1. RELIABILITY (most critical)
        if current_reliability < supplier_rule.get('reliability_critical_threshold', 0.70):
            decision['violations'].append('critical_reliability_failure')
            decision['escalation_level'] = max(decision['escalation_level'], 5)
        elif current_reliability < supplier_rule.get('reliability_failure_threshold', 0.75):
            decision['violations'].append('reliability_failure')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
        elif current_reliability < supplier_rule.get('reliability_min_acceptable', 0.80):
            decision['warnings'].append('reliability_below_acceptable')
            decision['escalation_level'] = max(decision['escalation_level'], 3)
        
        # 2. LEAD TIME (STRICT - no flexibility)
        lead_time = context.get('Lead_Time_Days', 0)
        max_acceptable_lt = supplier_rule.get('max_acceptable_lead_time', 100)
        critical_lt = supplier_rule.get('critical_lead_time', 110)
        
        if lead_time > critical_lt:
            decision['violations'].append('critical_lead_time_exceeded')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
        elif lead_time > max_acceptable_lt:
            decision['warnings'].append('lead_time_exceeds_acceptable')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
        
        # 3. ON-TIME DELIVERY (STRICT target)
        on_time_pct = context.get('On_Time_Delivery_%', 100) / 100
        on_time_min = supplier_rule.get('on_time_min_acceptable', 0.90)
        on_time_critical = supplier_rule.get('on_time_critical', 0.85)
        on_time_failure = supplier_rule.get('on_time_failure', 0.80)
        
        if on_time_pct < on_time_failure:
            decision['violations'].append('on_time_delivery_failure')
            decision['escalation_level'] = max(decision['escalation_level'], 5)
        elif on_time_pct < on_time_critical:
            decision['violations'].append('on_time_delivery_critical')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
        elif on_time_pct < on_time_min:
            decision['warnings'].append('on_time_delivery_below_target')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
        
        # 4. COST (STRICT enforcement)
        cost = context.get('Freight_Cost_USD', 0)
        cost_warning = supplier_rule.get('cost_warning_threshold', float('inf'))
        cost_critical = supplier_rule.get('cost_critical_threshold', float('inf'))
        cost_failure = supplier_rule.get('cost_failure_threshold', float('inf'))
        
        if cost > cost_failure:
            decision['violations'].append('cost_failure_threshold_exceeded')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
            decision['strict_compliance_score'] *= 0.7
        elif cost > cost_critical:
            decision['violations'].append('cost_critical_threshold_exceeded')
            decision['escalation_level'] = max(decision['escalation_level'], 3)
            decision['strict_compliance_score'] *= 0.8
        elif cost > cost_warning:
            decision['warnings'].append('cost_warning_threshold_exceeded')
            decision['escalation_level'] = max(decision['escalation_level'], 1)
            decision['strict_compliance_score'] *= 0.9
        
        # 5. DISRUPTION (CONSERVATIVE response)
        disruption_severity = context.get('Disruption_Severity', 0)
        max_acceptable_disruption = supplier_rule.get('max_acceptable_disruption', 2)
        
        if disruption_severity > max_acceptable_disruption:
            decision['violations'].append(f'disruption_severity_critical_{disruption_severity}')
            decision['escalation_level'] = max(decision['escalation_level'], 4)
        
        # 6. STOCKOUT FREQUENCY (STRICT penalties)
        stockout_freq = context.get('Stockout_Frequency_per_Year', 0)
        stockout_warning = supplier_rule.get('stockout_frequency_warning', float('inf'))
        stockout_critical = supplier_rule.get('stockout_frequency_critical', float('inf'))
        
        if stockout_freq > stockout_critical:
            decision['violations'].append('stockout_frequency_critical')
            decision['escalation_level'] = max(decision['escalation_level'], 3)
        elif stockout_freq > stockout_warning:
            decision['warnings'].append('stockout_frequency_warning')
            decision['escalation_level'] = max(decision['escalation_level'], 2)
        
        # 7. DELIVERY DELAY (NEW metric - STRICT)
        delivery_delay = context.get('Delivery_Delay_Days', 0)
        max_delay = supplier_rule.get('max_acceptable_lead_time', 100) * 0.3  # 30% of lead time
        
        if delivery_delay > max_delay * 1.5:
            decision['violations'].append('excessive_delivery_delay')
            decision['escalation_level'] = max(decision['escalation_level'], 3)
        elif delivery_delay > max_delay:
            decision['warnings'].append('delivery_delay_exceeded')
            decision['escalation_level'] = max(decision['escalation_level'], 1)
        
        # 8. CO2 EMISSIONS (NEW - environmental compliance)
        co2_emissions = context.get('CO2_Emissions_tons', 0)
        co2_critical = supplier_rule.get('cost_critical_threshold', float('inf')) * 0.1  # Estimate based on cost
        
        if co2_emissions > co2_critical:
            decision['penalties'].append('high_co2_emissions_penalty')
            decision['strict_compliance_score'] *= 0.85
        
        # DECISION LOGIC with STRICT enforcement
        
        if decision['escalation_level'] >= 5:
            decision['action'] = 'switch_to_backup_supplier'
            decision['supplier_type'] = 'backup'
            decision['reasoning'] = 'critical_failures_detected'
            decision['urgency'] = 'emergency'
            decision['approval_required'] = True
            decision['approval_level'] = 'director+cfo'
            decision['approval_delay_hours'] = 2
        
        elif decision['escalation_level'] >= 4:
            decision['action'] = 'escalate_to_management'
            decision['supplier_type'] = 'primary_under_review'
            decision['reasoning'] = 'multiple_critical_violations'
            decision['urgency'] = 'high'
            decision['approval_required'] = True
            decision['approval_level'] = 'director'
            decision['approval_delay_hours'] = 6
        
        elif decision['escalation_level'] >= 3:
            decision['action'] = 'activate_contingency_protocols'
            decision['supplier_type'] = 'primary_with_backup_ready'
            decision['reasoning'] = 'significant_violations_detected'
            decision['urgency'] = 'medium'
            decision['approval_required'] = True
            decision['approval_level'] = 'manager'
            decision['approval_delay_hours'] = 12
        
        elif decision['escalation_level'] >= 2:
            decision['action'] = 'increase_monitoring'
            decision['supplier_type'] = 'primary_monitored'
            decision['reasoning'] = 'warnings_detected_requires_attention'
            decision['urgency'] = 'medium'
            decision['approval_required'] = True
            decision['approval_level'] = 'supervisor'
            decision['approval_delay_hours'] = 18
        
        else:
            decision['action'] = 'continue_primary_supplier'
            decision['supplier_type'] = 'primary'
            decision['reasoning'] = 'all_metrics_within_acceptable_range'
            decision['urgency'] = 'none'
            decision['approval_required'] = False
        
        return decision
    
    def _get_default_enhanced_decision(self) -> Dict[str, Any]:
        """Default decision with conservative STRICT assumptions."""
        return {
            'action': 'continue_primary_supplier',
            'supplier_type': 'primary',
            'reasoning': 'default_conservative_rule',
            'current_reliability': 0.80,
            'threshold': 0.75,
            'violations': [],
            'warnings': [],
            'penalties': [],
            'escalation_level': 0,
            'approval_required': False,
            'strict_compliance_score': 1.0,
        }
    
    def calculate_enhanced_traditional_performance(self) -> Dict[str, float]:
        """Calculate traditional system performance with STRICT metrics."""
        
        # Core metrics from data
        avg_supplier_reliability = self.ghsc_data['Supplier_Reliability_Score'].mean()
        avg_lead_time = self.ghsc_data['Lead_Time_Days'].mean()
        on_time_delivery = self.ghsc_data['On_Time_Delivery_%'].mean() / 100.0
        avg_freight_cost = self.ghsc_data['Freight_Cost_USD'].mean()
        avg_delivery_delay = self.ghsc_data['Delivery_Delay_Days'].mean()
        avg_resupply_time = self.ghsc_data['Resupply_Time_Days'].mean()
        avg_stockout_freq = self.ghsc_data['Stockout_Frequency_per_Year'].mean()
        avg_co2 = self.ghsc_data['CO2_Emissions_tons'].mean()
        avg_on_time_pct = self.ghsc_data['On_Time_Delivery_%'].mean()
        
        # Disruption impact
        disrupted_data = self.ghsc_data[self.ghsc_data['Disruption_Severity'] > 2]
        if len(disrupted_data) > 0:
            disruption_impact = (disrupted_data['On_Time_Delivery_%'].mean() / 
                               self.ghsc_data['On_Time_Delivery_%'].mean())
            disruption_recovery_time = 7.0 + (disrupted_data['Disruption_Severity'].mean() * 2.0)
        else:
            disruption_impact = 1.0
            disruption_recovery_time = 7.0
        
        # Compliance violations (STRICT metric)
        reliability_failures = len(self.ghsc_data[self.ghsc_data['Supplier_Reliability_Score'] < 0.80])
        on_time_violations = len(self.ghsc_data[self.ghsc_data['On_Time_Delivery_%'] < 90])
        cost_violations = len(self.ghsc_data[self.ghsc_data['Freight_Cost_USD'] > avg_freight_cost * 1.30])
        delay_violations = len(self.ghsc_data[self.ghsc_data['Delivery_Delay_Days'] > 7])
        
        total_violations = reliability_failures + on_time_violations + cost_violations + delay_violations
        violation_rate = total_violations / len(self.ghsc_data)
        
        return {
            # Primary metrics
            'traditional_supplier_reliability': avg_supplier_reliability,
            'traditional_lead_time_days': avg_lead_time,
            'traditional_on_time_delivery_pct': on_time_delivery * 100,
            'traditional_freight_cost_usd': avg_freight_cost,
            'traditional_delivery_delay_days': avg_delivery_delay,
            'traditional_resupply_time_days': avg_resupply_time,
            'traditional_stockout_frequency': avg_stockout_freq,
            'traditional_co2_emissions_tons': avg_co2,
            
            # Disruption metrics
            'traditional_disruption_resilience_factor': disruption_impact,
            'traditional_disruption_recovery_time_days': disruption_recovery_time,
            
            # Compliance metrics (STRICT)
            'traditional_reliability_failure_rate': reliability_failures / len(self.ghsc_data),
            'traditional_on_time_violation_rate': on_time_violations / len(self.ghsc_data),
            'traditional_cost_violation_rate': cost_violations / len(self.ghsc_data),
            'traditional_delay_violation_rate': delay_violations / len(self.ghsc_data),
            'traditional_total_violation_rate': violation_rate,
            
            # Traditional characteristics
            'decision_approval_delay_hours': 24,
            'manual_response_delay_hours': 24,
            'zero_predictive_capability': True,
            'dynamic_adjustment_enabled': False,
            'proactive_switching_enabled': False,
            'data_source': 'GHSC_comprehensive_analysis'
        }
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of enhanced traditional rules."""
        total_supplier_rules = sum(
            sum(len(rules) for rules in commodity_rules.values()) 
            for commodity_rules in self.preferred_suppliers.values()
        )
        
        return {
            'total_supplier_rules': total_supplier_rules,
            'total_lead_time_rules': len(self.fixed_lead_times),
            'transport_mode_preferences': len(self.transport_preferences),
            'cost_constraint_levels': 4,  # warning, critical, failure
            'emissions_constraint_levels': 3,
            'reliability_constraint_levels': 5,
            'disruption_response_levels': 5,
            'warehouse_type_rules': len(self.warehouse_rules),
            'commodity_specific_rules': len(self.commodity_specific_rules),
            
            # Enforcement characteristics (STRICT)
            'dynamic_adjustment_enabled': False,
            'proactive_switching_enabled': False,
            'maximum_approval_delay_hours': 24,
            'minimum_approval_delay_hours': 2,
            'avg_decision_latency_hours': 12,
            'zero_predictive_capability': True,
            'rules_update_frequency_days': 90,  # Quarterly
            'all_rules_fixed_and_immutable': True,
        }


if __name__ == "__main__":
    import sys
    
    ghsc_data = pd.read_csv('data/DATA_SPLITS/GHSC_PSM_Synthetic_Resilience_Dataset_v2_consistent_traindata.csv')
    
    enhanced_rules = EnhancedFixedLeadTimeSupplierRules(ghsc_data)
    
    performance = enhanced_rules.calculate_enhanced_traditional_performance()
    
    print("ENHANCED Traditional Baseline Performance (from GHSC data):")
    for metric, value in sorted(performance.items()):
        print(f"  {metric}: {value:.4f}")
    
    # Test decision making
    test_context = {
        'Lead_Time_Days': 60,
        'On_Time_Delivery_%': 88,
        'Delivery_Delay_Days': 8,
        'Disruption_Severity': 3,
        'Freight_Cost_USD': 180000,
        'Stockout_Frequency_per_Year': 0.12,
        'CO2_Emissions_tons': 18000,
    }
    
    decision = enhanced_rules.get_enhanced_supplier_decision(
        'Malaria_RDT', 'Nigeria', 'Clinic', 0.78, test_context
    )
    print(f"\nSample Enhanced Decision:")
    for key, value in decision.items():
        print(f"  {key}: {value}")
    
    # Statistics
    stats = enhanced_rules.get_statistics_summary()
    print(f"\nRules Summary:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
