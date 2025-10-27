"""
Traditional Baseline: Static Routing and Transport Policies
Based on LPI and GHSC data using pre-approved transport modes and routes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StaticRoutingTransportRules:
    """
    Traditional routing and transport policies using fixed pre-approved routes.
    
    Uses actual data columns:
    - Transport_Mode (GHSC): Historical transport preferences
    - Freight_Cost_USD (GHSC): Cost baselines for route selection
    - LPI Score (LPI): Country infrastructure capabilities
    - Infrastructure Score (LPI): Transport infrastructure ratings
    """
    
    def __init__(self, ghsc_data: pd.DataFrame, lpi_data: pd.DataFrame):
        """Initialize with GHSC and LPI data."""
        self.ghsc_data = ghsc_data
        self.lpi_data = lpi_data
        self.approved_routes = self._establish_approved_routes()
        self.transport_mode_hierarchy = self._establish_transport_hierarchy()
        self.cost_baselines = self._calculate_route_cost_baselines()
        
    def _establish_approved_routes(self) -> Dict[str, Dict[str, Any]]:
        """Establish pre-approved routes by country using historical patterns."""
        approved_routes = {}
        
        # Merge GHSC with LPI data for infrastructure context
        merged_data = self.ghsc_data.merge(
            self.lpi_data[['Economy', 'Infrastructure Score', 'LPI Score']], 
            left_on='Country', 
            right_on='Economy', 
            how='left'
        )
        
        for country, group in merged_data.groupby('Country'):
            # Traditional approach: establish fixed approved transport modes
            transport_usage = group['Transport_Mode'].value_counts(normalize=True)
            
            # Get infrastructure capability from LPI data
            infrastructure_score = group['Infrastructure Score'].fillna(2.5).iloc[0]
            lpi_score = group['LPI Score'].fillna(2.5).iloc[0]
            
            # Traditional routing rules based on infrastructure and historical usage
            primary_mode = transport_usage.index[0] if len(transport_usage) > 0 else 'Air'
            
            # Traditional backup selection (simple hierarchy)
            backup_modes = list(transport_usage.index[1:3]) if len(transport_usage) > 1 else ['Air']
            
            approved_routes[country] = {
                'primary_transport_mode': primary_mode,
                'backup_transport_modes': backup_modes,
                'infrastructure_score': infrastructure_score,
                'lpi_score': lpi_score,
                'route_flexibility': 'low',  # Traditional: limited flexibility
                'approved_ports': self._get_traditional_ports(country, infrastructure_score),
                'seasonal_restrictions': {},  # Traditional: not considered
                'disruption_alternatives': []  # Traditional: no proactive alternatives
            }
            
        return approved_routes
    
    def _establish_transport_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Establish traditional transport mode hierarchy by cost and reliability."""
        
        # Analyze transport modes from GHSC data
        transport_analysis = {}
        
        for mode, group in self.ghsc_data.groupby('Transport_Mode'):
            avg_cost = group['Freight_Cost_USD'].mean()
            avg_lead_time = group['Lead_Time_Days'].mean()
            reliability = group['On_Time_Delivery_%'].mean() / 100.0
            
            # Traditional scoring (simple weighted average)
            cost_score = 1.0 / (avg_cost / 50000)  # Normalize around 50K baseline
            speed_score = 1.0 / (avg_lead_time / 30)  # Normalize around 30 days
            reliability_score = reliability
            
            # Traditional hierarchy score (equal weights)
            hierarchy_score = (cost_score + speed_score + reliability_score) / 3.0
            
            transport_analysis[mode] = {
                'avg_cost': avg_cost,
                'avg_lead_time': avg_lead_time,
                'reliability': reliability,
                'hierarchy_score': hierarchy_score,
                'usage_frequency': len(group),
                'preferred_for': []  # Will be filled based on scenarios
            }
        
        # Traditional mode preferences by scenario
        modes_by_score = sorted(transport_analysis.keys(), 
                               key=lambda x: transport_analysis[x]['hierarchy_score'], 
                               reverse=True)
        
        # Traditional scenario-based preferences (fixed rules)
        for i, mode in enumerate(modes_by_score):
            if transport_analysis[mode]['avg_lead_time'] < 30:
                transport_analysis[mode]['preferred_for'].append('urgent')
            if transport_analysis[mode]['avg_cost'] < 75000:
                transport_analysis[mode]['preferred_for'].append('cost_sensitive')
            if transport_analysis[mode]['reliability'] > 0.85:
                transport_analysis[mode]['preferred_for'].append('reliable')
        
        return transport_analysis
    
    def _calculate_route_cost_baselines(self) -> Dict[str, Dict[str, float]]:
        """Calculate baseline costs for route selection using historical data."""
        cost_baselines = {}
        
        # Traditional baseline calculation by country and transport mode
        for (country, mode), group in self.ghsc_data.groupby(['Country', 'Transport_Mode']):
            avg_cost = group['Freight_Cost_USD'].mean()
            min_cost = group['Freight_Cost_USD'].min()
            max_cost = group['Freight_Cost_USD'].max()
            
            # Traditional cost thresholds (fixed percentages)
            acceptable_cost = avg_cost * 1.1  # 10% above average
            emergency_cost = avg_cost * 1.5   # 50% above average (emergency threshold)
            
            key = f"{country}_{mode}"
            cost_baselines[key] = {
                'baseline_cost': avg_cost,
                'acceptable_threshold': acceptable_cost,
                'emergency_threshold': emergency_cost,
                'historical_min': min_cost,
                'historical_max': max_cost,
                'cost_volatility': (max_cost - min_cost) / avg_cost
            }
        
        return cost_baselines
    
    def _get_traditional_ports(self, country: str, infrastructure_score: float) -> List[str]:
        """Generate traditional approved ports based on infrastructure score."""
        # Traditional approach: limited port options based on infrastructure
        if infrastructure_score >= 3.5:
            return ['primary_port', 'backup_port_1', 'backup_port_2']
        elif infrastructure_score >= 2.5:
            return ['primary_port', 'backup_port_1']
        else:
            return ['primary_port']
    
    def get_traditional_routing_decision(self, country: str, commodity: str, 
                                       disruption_type: Optional[str] = None,
                                       cost_constraint: Optional[float] = None) -> Dict[str, Any]:
        """
        Make routing decision using traditional static rules.
        
        Traditional logic:
        - Use pre-approved primary route unless failure
        - Limited consideration of disruption type
        - Simple cost-based switching with high thresholds
        """
        
        if country not in self.approved_routes:
            return self._get_default_routing_decision()
        
        route_info = self.approved_routes[country]
        primary_mode = route_info['primary_transport_mode']
        
        # Traditional decision (static, rule-based)
        decision = {
            'selected_transport_mode': primary_mode,
            'route_type': 'primary_approved',
            'reasoning': 'standard_operating_procedure',
            'cost_impact': 'baseline',
            'flexibility': 'low'
        }
        
        # Traditional disruption response (limited, reactive)
        if disruption_type:
            disruption_response = self._get_traditional_disruption_response(
                disruption_type, route_info
            )
            decision.update(disruption_response)
        
        # Traditional cost consideration (high threshold for switching)
        if cost_constraint:
            cost_response = self._get_traditional_cost_response(
                country, primary_mode, cost_constraint
            )
            if cost_response['switch_required']:
                decision.update(cost_response)
        
        return decision
    
    def _get_traditional_disruption_response(self, disruption_type: str, 
                                           route_info: Dict[str, Any]) -> Dict[str, Any]:
        """Traditional response to disruptions (limited, reactive)."""
        
        # Traditional disruption rules (simple, limited scope)
        traditional_responses = {
            'flood': {
                'avoid_transport_modes': ['Land'],
                'preferred_alternative': 'Air',
                'response_delay': 2.0,  # Days to recognize and respond
                'reasoning': 'manual_flood_response_protocol'
            },
            'port_closure': {
                'avoid_transport_modes': ['Ocean'], 
                'preferred_alternative': 'Air',
                'response_delay': 1.5,
                'reasoning': 'manual_port_closure_protocol'
            },
            'pandemic': {
                'avoid_transport_modes': [],  # Traditional: no specific avoidance
                'preferred_alternative': route_info['primary_transport_mode'],
                'response_delay': 3.0,  # Slow manual assessment
                'reasoning': 'limited_pandemic_protocols'
            },
            'cyber_attack': {
                'avoid_transport_modes': [],  # Traditional: minimal cyber consideration
                'preferred_alternative': route_info['primary_transport_mode'],
                'response_delay': 4.0,  # Manual systems less affected but slower response
                'reasoning': 'manual_backup_systems'
            }
        }
        
        if isinstance(disruption_type, str) and disruption_type.lower() in traditional_responses:
            response = traditional_responses[disruption_type.lower()]
            
            # Check if current primary mode should be avoided
            if route_info['primary_transport_mode'] in response['avoid_transport_modes']:
                alternative = response['preferred_alternative']
                if alternative in route_info['backup_transport_modes']:
                    return {
                        'selected_transport_mode': alternative,
                        'route_type': 'disruption_backup',
                        'reasoning': response['reasoning'],
                        'response_delay': response['response_delay'],
                        'cost_impact': 'increased'
                    }
        
        # Default: stick with primary (traditional conservative approach)
        return {
            'route_type': 'primary_maintained',
            'reasoning': 'insufficient_disruption_protocols',
            'response_delay': 5.0  # Slow manual assessment
        }
    
    def _get_traditional_cost_response(self, country: str, transport_mode: str, 
                                     cost_constraint: float) -> Dict[str, Any]:
        """Traditional cost-based route switching (high thresholds)."""
        
        key = f"{country}_{transport_mode}"
        
        if key not in self.cost_baselines:
            return {'switch_required': False}
        
        baseline_info = self.cost_baselines[key]
        
        # Traditional switching thresholds (conservative)
        if cost_constraint > baseline_info['emergency_threshold']:
            # Only switch in extreme cost scenarios
            return {
                'switch_required': True,
                'selected_transport_mode': 'Air',  # Default emergency mode
                'route_type': 'emergency_cost_switch',
                'reasoning': 'extreme_cost_threshold_exceeded',
                'cost_impact': 'emergency_premium'
            }
        
        return {'switch_required': False}
    
    def calculate_traditional_routing_performance(self) -> Dict[str, float]:
        """Calculate traditional routing system performance metrics."""
        
        # Route efficiency (limited optimization)
        avg_freight_cost = self.ghsc_data['Freight_Cost_USD'].mean()
        avg_lead_time = self.ghsc_data['Lead_Time_Days'].mean()
        
        # Route reliability (fixed route dependency)
        on_time_performance = self.ghsc_data['On_Time_Delivery_%'].mean() / 100.0
        
        # Disruption resilience (poor - relies on single routes)
        disrupted_shipments = self.ghsc_data[self.ghsc_data['Disruption_Severity'] > 2]
        if len(disrupted_shipments) > 0:
            disruption_cost_impact = (disrupted_shipments['Freight_Cost_USD'].mean() / 
                                    self.ghsc_data['Freight_Cost_USD'].mean())
            disruption_time_impact = (disrupted_shipments['Lead_Time_Days'].mean() / 
                                    self.ghsc_data['Lead_Time_Days'].mean())
        else:
            disruption_cost_impact = 1.0
            disruption_time_impact = 1.0
        
        # Route flexibility (low - fixed approved routes)
        transport_mode_diversity = len(self.ghsc_data['Transport_Mode'].unique())
        total_possible_modes = 4  # Air, Ocean, Land, Rail
        flexibility_score = transport_mode_diversity / total_possible_modes
        
        # Response time to route changes (manual process)
        manual_route_change_time = 3.0  # Days for manual route approval and implementation
        
        return {
            'traditional_routing_cost_efficiency': avg_freight_cost,
            'traditional_routing_time_efficiency': avg_lead_time,
            'traditional_route_reliability': on_time_performance,
            'traditional_disruption_cost_impact': disruption_cost_impact,
            'traditional_disruption_time_impact': disruption_time_impact,
            'traditional_route_flexibility': flexibility_score,
            'traditional_route_change_response_time': manual_route_change_time,
            'approved_route_dependency': 0.8,  # High dependency on pre-approved routes
            'data_source': 'GHSC_LPI_routing_historical_patterns'
        }
    
    def _get_default_routing_decision(self) -> Dict[str, Any]:
        """Default routing decision for unknown countries."""
        return {
            'selected_transport_mode': 'Air',  # Safe default
            'route_type': 'default_emergency',
            'reasoning': 'no_approved_route_available',
            'cost_impact': 'premium',
            'flexibility': 'minimal'
        }
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get summary statistics of traditional routing rules."""
        total_approved_routes = len(self.approved_routes)
        total_transport_modes = len(self.transport_mode_hierarchy)
        
        avg_flexibility = np.mean([1 if route['route_flexibility'] == 'low' else 2 
                                 for route in self.approved_routes.values()])
        
        return {
            'total_approved_routes': total_approved_routes,
            'transport_modes_available': total_transport_modes,
            'avg_route_flexibility': avg_flexibility / 2.0,  # Normalize
            'proactive_rerouting_enabled': False,  # Traditional characteristic
            'dynamic_mode_selection': False,       # Traditional characteristic
            'disruption_response_protocols': 4,    # Limited set of manual protocols
            'cost_optimization_enabled': False     # Traditional characteristic
        }


if __name__ == "__main__":
    # Test with GHSC and LPI data
    import sys
    import os
    
    ghsc_data = pd.read_csv('../DATA_SPLITS/GHSC_PSM_Synthetic_Resilience_Dataset_v2_consistent_traindata.csv')
    lpi_data = pd.read_csv('../DATA_SPLITS/International_LPI_from_2007_to_2023_traindata.csv')
    
    traditional_routing = StaticRoutingTransportRules(ghsc_data, lpi_data)
    
    # Test performance calculation
    performance = traditional_routing.calculate_traditional_routing_performance()
    
    print("Traditional Routing Performance (from GHSC & LPI data):")
    for metric, value in performance.items():
        print(f"  {metric}: {value}")
    
    # Test decision making
    decision = traditional_routing.get_traditional_routing_decision(
        'Nigeria', 'Malaria_RDT', disruption_type='flood', cost_constraint=120000
    )
    print(f"\nSample Routing Decision: {decision}")