"""
Traditional Baseline: Single-Shock Planning Rules
Based on disaster data using isolated disruption planning without multi-shock consideration.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SingleShockPlanningRules:
    """
    Traditional single-shock planning system using isolated disruption scenarios.
    
    Uses actual disaster data columns:
    - Disaster Type (Disaster data): Historical disaster patterns
    - Total Deaths, No. Affected (Disaster data): Impact severity metrics
    - Start Year, End Year (Disaster data): Temporal patterns
    - Disruption_Severity (GHSC): Supply chain impact levels
    """
    
    def __init__(self, ghsc_data: pd.DataFrame, disaster_data: pd.DataFrame, 
                 public_emergency_data: pd.DataFrame):
        """Initialize with GHSC, disaster, and emergency data."""
        self.ghsc_data = ghsc_data
        self.disaster_data = disaster_data
        self.public_emergency_data = public_emergency_data
        self.single_shock_scenarios = self._build_single_shock_scenarios()
        self.response_protocols = self._establish_traditional_response_protocols()
        self.capacity_assumptions = self._calculate_single_shock_capacity_assumptions()
        
    def _build_single_shock_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Build traditional single-shock planning scenarios from historical data."""
        scenarios = {}
        
        # Analyze individual disaster types in isolation
        if 'Disaster Type' in self.disaster_data.columns:
            for disaster_type, group in self.disaster_data.groupby('Disaster Type'):
                # Traditional approach: analyze each disaster type independently
                avg_deaths = group['Total Deaths'].fillna(0).mean()
                avg_affected = group['No. Affected'].fillna(0).mean()
                frequency = len(group)
                
                # Traditional severity classification (simple thresholds)
                if avg_deaths > 1000 or avg_affected > 100000:
                    severity_class = 'high'
                elif avg_deaths > 100 or avg_affected > 10000:
                    severity_class = 'medium'
                else:
                    severity_class = 'low'
                
                scenarios[disaster_type] = {
                    'avg_deaths': avg_deaths,
                    'avg_affected': avg_affected,
                    'historical_frequency': frequency,
                    'severity_class': severity_class,
                    'planning_assumptions': self._get_traditional_planning_assumptions(disaster_type, severity_class),
                    'concurrent_event_consideration': False,  # Traditional: single-shock only
                    'cascading_effect_planning': False       # Traditional: no cascade planning
                }
        
        # Add supply chain disruption scenarios from GHSC data
        for disruption_type, group in self.ghsc_data.groupby('Disruption_Type'):
            if disruption_type != 'None' and pd.notna(disruption_type):
                avg_severity = group['Disruption_Severity'].mean()
                avg_impact_on_delivery = (group['On_Time_Delivery_%'].mean() / 
                                        self.ghsc_data['On_Time_Delivery_%'].mean())
                
                scenarios[f"supply_chain_{disruption_type}"] = {
                    'avg_severity': avg_severity,
                    'delivery_impact': avg_impact_on_delivery,
                    'historical_frequency': len(group),
                    'severity_class': 'high' if avg_severity > 3 else 'medium' if avg_severity > 1 else 'low',
                    'planning_assumptions': self._get_supply_chain_planning_assumptions(disruption_type, avg_severity),
                    'concurrent_event_consideration': False,
                    'cascading_effect_planning': False
                }
        
        return scenarios
    
    def _get_traditional_planning_assumptions(self, disaster_type: str, 
                                           severity_class: str) -> Dict[str, Any]:
        """Get traditional planning assumptions for single disasters."""
        
        # Traditional planning assumptions (isolated, conservative)
        base_assumptions = {
            'duration_days': 7,      # Standard assumption: 1 week duration
            'resource_multiplier': 2.0,  # Double normal resources
            'recovery_time_days': 14,     # Standard 2-week recovery
            'supply_buffer': 0.3,         # 30% additional supply
            'staff_availability': 0.8     # 20% staff unavailable
        }
        
        # Traditional severity adjustments (simple multipliers)
        severity_multipliers = {
            'low': {'duration_days': 0.5, 'resource_multiplier': 1.2, 'recovery_time_days': 0.7},
            'medium': {'duration_days': 1.0, 'resource_multiplier': 2.0, 'recovery_time_days': 1.0},
            'high': {'duration_days': 1.5, 'resource_multiplier': 3.0, 'recovery_time_days': 1.5}
        }
        
        multiplier = severity_multipliers.get(severity_class, severity_multipliers['medium'])
        
        for key, base_value in base_assumptions.items():
            if key in multiplier:
                base_assumptions[key] = base_value * multiplier[key]
        
        # Disaster-specific traditional assumptions
        disaster_specific = {
            'Flood': {'equipment_impact': 0.4, 'transport_disruption': 0.7},
            'Storm': {'infrastructure_impact': 0.5, 'power_outage_probability': 0.8},
            'Earthquake': {'structural_damage': 0.6, 'communication_disruption': 0.9},
            'Epidemic': {'staff_availability': 0.6, 'supply_demand_increase': 2.5}
        }
        
        if disaster_type in disaster_specific:
            base_assumptions.update(disaster_specific[disaster_type])
        
        return base_assumptions
    
    def _get_supply_chain_planning_assumptions(self, disruption_type: str, 
                                             severity: float) -> Dict[str, Any]:
        """Get supply chain specific planning assumptions."""
        
        # Traditional supply chain assumptions (single disruption focus)
        return {
            'lead_time_extension_days': min(severity * 5, 20),  # Max 20 days extension
            'cost_increase_percentage': min(severity * 15, 50),  # Max 50% cost increase
            'supplier_availability': max(0.5, 1.0 - (severity * 0.1)),  # Min 50% availability
            'transport_capacity_reduction': min(severity * 0.2, 0.6),  # Max 60% reduction
            'inventory_buffer_required': min(severity * 0.1, 0.5),  # Max 50% buffer
            'manual_intervention_required': True,  # Traditional: always requires manual intervention
            'concurrent_disruption_probability': 0.0  # Traditional: assumes single disruption
        }
    
    def _establish_traditional_response_protocols(self) -> Dict[str, Dict[str, Any]]:
        """Establish traditional response protocols for single-shock scenarios."""
        
        protocols = {}
        
        # Traditional response phases (sequential, not parallel)
        standard_phases = {
            'assessment': {'duration_hours': 24, 'parallel_execution': False},
            'mobilization': {'duration_hours': 48, 'parallel_execution': False},
            'implementation': {'duration_hours': 72, 'parallel_execution': False},
            'monitoring': {'duration_hours': 168, 'parallel_execution': False}  # 1 week
        }
        
        for scenario_name in self.single_shock_scenarios.keys():
            severity_class = self.single_shock_scenarios[scenario_name]['severity_class']
            
            # Traditional protocol scaling (simple time multipliers)
            time_multipliers = {
                'low': 0.8,
                'medium': 1.0,
                'high': 1.5
            }
            
            multiplier = time_multipliers.get(severity_class, 1.0)
            
            scenario_protocol = {}
            for phase, details in standard_phases.items():
                scenario_protocol[phase] = {
                    'duration_hours': details['duration_hours'] * multiplier,
                    'parallel_execution': False,  # Traditional: sequential execution
                    'automation_level': 0.2,      # Traditional: 20% automated
                    'manual_checkpoints': 3,      # Multiple manual approvals required
                    'escalation_threshold': 0.7   # High threshold for escalation
                }
            
            protocols[scenario_name] = {
                'phases': scenario_protocol,
                'total_response_time_hours': sum(p['duration_hours'] for p in scenario_protocol.values()),
                'concurrent_scenario_handling': False,  # Traditional: one at a time
                'adaptive_protocol_adjustment': False   # Traditional: fixed protocols
            }
        
        return protocols
    
    def _calculate_single_shock_capacity_assumptions(self) -> Dict[str, Dict[str, float]]:
        """Calculate capacity assumptions for single-shock planning."""
        
        # Traditional capacity planning (isolated scenarios)
        capacity_assumptions = {}
        
        # Base capacity calculations from historical data
        base_freight_capacity = self.ghsc_data['Freight_Cost_USD'].mean()
        base_order_volume = self.ghsc_data['Order_Volume_Units'].mean()
        
        for scenario_name, scenario_data in self.single_shock_scenarios.items():
            severity_class = scenario_data['severity_class']
            
            # Traditional capacity scaling (simple linear scaling)
            capacity_multipliers = {
                'low': {'freight': 1.2, 'volume': 1.1, 'staff': 1.0, 'time': 1.2},
                'medium': {'freight': 1.5, 'volume': 1.3, 'staff': 0.8, 'time': 1.5},
                'high': {'freight': 2.0, 'volume': 1.6, 'staff': 0.6, 'time': 2.0}
            }
            
            multiplier = capacity_multipliers.get(severity_class, capacity_multipliers['medium'])
            
            capacity_assumptions[scenario_name] = {
                'required_freight_capacity': base_freight_capacity * multiplier['freight'],
                'required_volume_capacity': base_order_volume * multiplier['volume'],
                'available_staff_ratio': multiplier['staff'],
                'response_time_multiplier': multiplier['time'],
                'concurrent_scenario_capacity': 0.0,  # Traditional: no concurrent planning
                'cascade_buffer_capacity': 0.0,       # Traditional: no cascade planning
                'adaptive_capacity_enabled': False     # Traditional: fixed capacity
            }
        
        return capacity_assumptions
    
    def get_traditional_single_shock_response(self, disruption_type: str, 
                                            severity_level: float,
                                            current_resources: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate traditional single-shock response plan.
        
        Traditional logic:
        - Plan for one disruption at a time
        - Use predetermined response protocols
        - No consideration of concurrent or cascading events
        """
        
        # Find matching scenario
        matching_scenario = None
        for scenario_name, scenario_data in self.single_shock_scenarios.items():
            if disruption_type.lower() in scenario_name.lower():
                matching_scenario = scenario_name
                break
        
        if not matching_scenario:
            return self._get_default_single_shock_response()
        
        scenario_data = self.single_shock_scenarios[matching_scenario]
        protocol = self.response_protocols.get(matching_scenario, {})
        capacity = self.capacity_assumptions.get(matching_scenario, {})
        
        # Traditional response plan (single-focus)
        response_plan = {
            'primary_disruption': disruption_type,
            'severity_class': scenario_data['severity_class'],
            'planning_approach': 'single_shock_isolation',
            'response_phases': protocol.get('phases', {}),
            'total_response_time_hours': protocol.get('total_response_time_hours', 240),
            'resource_requirements': capacity,
            'concurrent_event_preparation': False,  # Traditional limitation
            'cascade_mitigation_plans': [],         # Traditional limitation
            'adaptive_response_enabled': False      # Traditional limitation
        }
        
        # Traditional resource allocation (simple scaling)
        resource_allocation = self._calculate_traditional_resource_allocation(
            scenario_data, current_resources
        )
        response_plan['resource_allocation'] = resource_allocation
        
        return response_plan
    
    def _calculate_traditional_resource_allocation(self, scenario_data: Dict[str, Any], 
                                                 current_resources: Dict[str, float]) -> Dict[str, float]:
        """Calculate traditional resource allocation for single shock."""
        
        planning_assumptions = scenario_data['planning_assumptions']
        
        # Traditional allocation (simple percentage increases)
        allocation = {}
        
        # Financial resources
        allocation['financial_resources'] = current_resources.get('budget', 1000000) * planning_assumptions.get('resource_multiplier', 2.0)
        
        # Inventory resources
        allocation['inventory_buffer'] = current_resources.get('inventory', 10000) * (1 + planning_assumptions.get('supply_buffer', 0.3))
        
        # Staff resources
        allocation['available_staff'] = current_resources.get('staff', 100) * planning_assumptions.get('staff_availability', 0.8)
        
        # Transport resources (no dynamic optimization)
        allocation['transport_capacity'] = current_resources.get('transport', 50) * planning_assumptions.get('resource_multiplier', 2.0)
        
        return allocation
    
    def calculate_traditional_single_shock_performance(self) -> Dict[str, float]:
        """Calculate traditional single-shock planning performance metrics."""
        
        # Response time performance (single-shock focus)
        avg_response_time = np.mean([
            protocol['total_response_time_hours'] 
            for protocol in self.response_protocols.values()
        ]) / 24.0  # Convert to days
        
        # Resource efficiency (no optimization for multiple scenarios)
        total_scenarios = len(self.single_shock_scenarios)
        avg_resource_multiplier = np.mean([
            capacity.get('response_time_multiplier', 1.5)
            for capacity in self.capacity_assumptions.values()
        ])
        
        # Planning coverage (single disruptions only)
        disrupted_records = self.ghsc_data[self.ghsc_data['Disruption_Severity'] > 1]
        single_disruption_coverage = len(disrupted_records) / len(self.ghsc_data) if len(self.ghsc_data) > 0 else 0
        
        # Adaptation capability (limited - fixed protocols)
        adaptation_score = 0.3  # Traditional systems: low adaptation capability
        
        # Concurrent event handling capability (none)
        concurrent_handling_score = 0.0  # Traditional limitation
        
        # Recovery effectiveness (isolated scenario basis)
        if len(disrupted_records) > 0:
            recovery_effectiveness = (disrupted_records['Outcome_Metric'].mean() / 
                                   self.ghsc_data['Outcome_Metric'].mean())
        else:
            recovery_effectiveness = 0.8  # Assumed traditional effectiveness
        
        return {
            'traditional_single_shock_response_time_days': avg_response_time,
            'traditional_resource_efficiency': 1.0 / avg_resource_multiplier,  # Inverse - lower is better
            'traditional_planning_coverage': single_disruption_coverage,
            'traditional_adaptation_capability': adaptation_score,
            'traditional_concurrent_handling_capability': concurrent_handling_score,
            'traditional_recovery_effectiveness': recovery_effectiveness,
            'traditional_protocol_flexibility': 0.2,  # Low flexibility
            'manual_intervention_dependency': 0.8,     # High manual dependency
            'data_source': 'GHSC_disaster_single_shock_patterns'
        }
    
    def _get_default_single_shock_response(self) -> Dict[str, Any]:
        """Default single-shock response for unknown disruptions."""
        return {
            'primary_disruption': 'unknown',
            'severity_class': 'medium',
            'planning_approach': 'generic_single_shock',
            'total_response_time_hours': 168,  # 1 week default
            'concurrent_event_preparation': False,
            'adaptive_response_enabled': False
        }
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get summary statistics of traditional single-shock planning."""
        
        return {
            'total_single_shock_scenarios': len(self.single_shock_scenarios),
            'total_response_protocols': len(self.response_protocols),
            'avg_response_time_hours': np.mean([
                p['total_response_time_hours'] for p in self.response_protocols.values()
            ]),
            'concurrent_scenario_planning': False,  # Traditional limitation
            'adaptive_protocol_capability': False,  # Traditional limitation
            'cascade_effect_consideration': False,  # Traditional limitation
            'multi_shock_preparedness': 0.0        # Traditional limitation
        }


if __name__ == "__main__":
    # Test with disaster and GHSC data
    import sys
    import os
    
    ghsc_data = pd.read_csv('../DATA_SPLITS/GHSC_PSM_Synthetic_Resilience_Dataset_v2_consistent_traindata.csv')
    disaster_data = pd.read_csv('../DATA_SPLITS/NaturalDisaster_public_emdat_custom_request_traindata.csv')
    public_emergency_data = pd.read_csv('../DATA_SPLITS/Public_emdat_custom_request_2025-10-23_traindata.csv')
    
    traditional_planning = SingleShockPlanningRules(ghsc_data, disaster_data, public_emergency_data)
    
    # Test performance calculation
    performance = traditional_planning.calculate_traditional_single_shock_performance()
    
    print("Traditional Single-Shock Planning Performance:")
    for metric, value in performance.items():
        print(f"  {metric}: {value}")
    
    # Test response generation
    response = traditional_planning.get_traditional_single_shock_response(
        'flood', 3.0, {'budget': 1000000, 'staff': 100, 'inventory': 10000}
    )
    print(f"\nSample Single-Shock Response Plan:")
    for key, value in response.items():
        if isinstance(value, dict) and len(value) > 3:
            print(f"  {key}: {list(value.keys())}")  # Show keys for complex dicts
        else:
            print(f"  {key}: {value}")