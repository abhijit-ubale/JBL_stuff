"""
Traditional Baseline: Static Routing and Transport Policies
Based on LPI and GHSC data using pre-approved transport modes and routes.
"""


import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional


class StaticRoutingTransportRules:
    """
    Traditional routing and transport policies using fixed pre-approved routes.
    
    Uses actual data columns:
    - Transport_Mode (GHSC): Historical transport preferences
    - Freight_Cost_USD (GHSC): Cost baselines for route selection
    - LPI Score (LPI): Country infrastructure capabilities
    - Infrastructure Score (LPI): Transport infrastructure ratings
    """
    
    def __init__(self, working_rules: Dict[str, pd.DataFrame]):
        """Initialize with WORKING_RULES data for all categories."""
        self.working_rules = working_rules
        self.approved_routes = self._establish_approved_routes()
        
    def _establish_approved_routes(self) -> Dict[str, Dict[str, Any]]:
        """Load pre-approved routes from WORKING_RULES CSVs only."""
        approved_routes = {}
        for category, df in self.working_rules.items():
            for _, row in df.iterrows():
                country = row.get('Country', row.get('Economy', None))
                if not country:
                    continue
                approved_routes[country] = {
                    'primary_transport_mode': row.get('Transport_Mode', 'Air'),
                    'backup_transport_modes': [row.get('Backup_Transport_Mode', 'Air')],
                    'infrastructure_score': row.get('Infrastructure_Score', np.nan),
                    'lpi_score': row.get('LPI_Score', np.nan),
                    'route_flexibility': row.get('Route_Flexibility', 'low'),
                    'approved_ports': [row.get('Port', 'primary_port')],
                    'seasonal_restrictions': {},
                    'disruption_alternatives': []
                }
        return approved_routes
    
    def _establish_transport_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Load transport mode hierarchy from WORKING_RULES only."""
        transport_analysis = {}
        for category, df in self.working_rules.items():
            for mode in df['Transport_Mode'].unique():
                mode_df = df[df['Transport_Mode'] == mode]
                avg_cost = mode_df['Freight_Cost_USD'].mean() if 'Freight_Cost_USD' in mode_df else np.nan
                avg_lead_time = mode_df['Lead_Time_Days'].mean() if 'Lead_Time_Days' in mode_df else np.nan
                reliability = mode_df['On_Time_Delivery_%'].mean() / 100.0 if 'On_Time_Delivery_%' in mode_df else np.nan
                transport_analysis[mode] = {
                    'avg_cost': avg_cost,
                    'avg_lead_time': avg_lead_time,
                    'reliability': reliability,
                    'hierarchy_score': np.nan,
                    'usage_frequency': len(mode_df),
                    'preferred_for': []
                }
        return transport_analysis
    
    def _calculate_route_cost_baselines(self) -> Dict[str, Dict[str, float]]:
        """Calculate baseline costs for route selection using WORKING_RULES only."""
        cost_baselines = {}
        for category, df in self.working_rules.items():
            for _, row in df.iterrows():
                country = row.get('Country', row.get('Economy', None))
                mode = row.get('Transport_Mode', None)
                if not country or not mode:
                    continue
                avg_cost = row.get('Freight_Cost_USD', np.nan)
                min_cost = row.get('Freight_Cost_USD', np.nan)
                max_cost = row.get('Freight_Cost_USD', np.nan)
                acceptable_cost = avg_cost * 1.1 if not np.isnan(avg_cost) else np.nan
                emergency_cost = avg_cost * 1.5 if not np.isnan(avg_cost) else np.nan
                key = f"{country}_{mode}"
                cost_baselines[key] = {
                    'baseline_cost': avg_cost,
                    'acceptable_threshold': acceptable_cost,
                    'emergency_threshold': emergency_cost,
                    'historical_min': min_cost,
                    'historical_max': max_cost,
                    'cost_volatility': 0.0
                }
        return cost_baselines
    
    def _get_traditional_ports(self, country: str) -> List[str]:
        """Get approved ports from WORKING_RULES only."""
        for category, df in self.working_rules.items():
            ports = df[df['Country'] == country]['Port'].unique()
            if len(ports) > 0:
                return list(ports)
        return ['primary_port']
    
    def get_traditional_routing_decision(self, country: str, commodity: str, 
                                       disruption_type: Optional[str] = None,
                                       cost_constraint: Optional[float] = None) -> Dict[str, Any]:
        """
        Make routing decision using WORKING_RULES only.
        """
        if country not in self.approved_routes:
            return self._get_default_routing_decision()
        route_info = self.approved_routes[country]
        primary_mode = route_info['primary_transport_mode']
        decision = {
            'selected_transport_mode': primary_mode,
            'route_type': 'primary_approved',
            'reasoning': 'standard_operating_procedure',
            'cost_impact': 'baseline',
            'flexibility': route_info.get('route_flexibility', 'low')
        }
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
        """Calculate traditional routing system performance metrics from WORKING_RULES only."""
        all_data = pd.concat(list(self.working_rules.values()), ignore_index=True)
        avg_freight_cost = all_data['Freight_Cost_USD'].mean() if 'Freight_Cost_USD' in all_data else np.nan
        avg_lead_time = all_data['Lead_Time_Days'].mean() if 'Lead_Time_Days' in all_data else np.nan
        on_time_performance = all_data['On_Time_Delivery_%'].mean() / 100.0 if 'On_Time_Delivery_%' in all_data else np.nan
        flexibility_score = len(all_data['Transport_Mode'].unique()) / 4 if 'Transport_Mode' in all_data else np.nan
        manual_route_change_time = 3.0
        # Disruption metrics: fallback to ratio of max/min cost and lead time if available
        disruption_cost_impact = 1.0
        disruption_time_impact = 1.0
        if 'Freight_Cost_USD' in all_data and all_data['Freight_Cost_USD'].max() > 0:
            disruption_cost_impact = all_data['Freight_Cost_USD'].max() / (avg_freight_cost if avg_freight_cost else 1)
        if 'Lead_Time_Days' in all_data and all_data['Lead_Time_Days'].max() > 0:
            disruption_time_impact = all_data['Lead_Time_Days'].max() / (avg_lead_time if avg_lead_time else 1)
        return {
            'traditional_routing_cost_efficiency': avg_freight_cost,
            'traditional_routing_time_efficiency': avg_lead_time,
            'traditional_route_reliability': on_time_performance,
            'traditional_disruption_cost_impact': disruption_cost_impact,
            'traditional_disruption_time_impact': disruption_time_impact,
            'traditional_route_flexibility': flexibility_score,
            'traditional_route_change_response_time': manual_route_change_time,
            'approved_route_dependency': 0.8,
            'data_source': 'WORKING_RULES'
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
    import sys
    import os
    working_rules = {}
    working_rules['GHSC'] = pd.read_csv('../WORKING_RULES/GHSC.csv')
    working_rules['LPI'] = pd.read_csv('../WORKING_RULES/International_LPI.csv')
    working_rules['Emergency'] = pd.read_csv('../WORKING_RULES/Public_Emergency.csv')
    working_rules['Disasters'] = pd.read_csv('../WORKING_RULES/Natural_Disasters.csv')
    traditional_routing = StaticRoutingTransportRules(working_rules)
    performance = traditional_routing.calculate_traditional_routing_performance()
    print("Traditional Routing Performance (from WORKING_RULES):")
    for metric, value in performance.items():
        print(f"  {metric}: {value}")
    decision = traditional_routing.get_traditional_routing_decision(
        'Nigeria', 'Malaria_RDT')
    print(f"\nSample Routing Decision: {decision}")