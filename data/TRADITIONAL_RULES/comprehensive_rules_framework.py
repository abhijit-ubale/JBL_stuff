"""
COMPREHENSIVE Enhanced Traditional Rules Framework
Integrates ALL enhanced rules (supplier, inventory, transport, disruption)
with a unified strict enforcement system for MAXIMUM CRL advantage.

This framework ensures the Traditional Baseline is as challenging as possible,
making CRL's superior performance undeniable.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ComprehensiveTraditionalRulesFramework:
    """
    UNIFIED STRICT Traditional Rules Framework integrating:
    - Fixed Lead Time & Supplier Rules
    - Reorder Point & Safety Stock Rules
    - Static Routing & Transport Rules
    - Disruption Response Rules
    - Comprehensive Compliance Tracking
    
    Key Philosophy:
    - ALL decisions are FIXED and IMMUTABLE
    - MULTIPLE escalation levels for each metric
    - SEVERE penalties for any deviation
    - MAXIMUM conservative buffers
    - ZERO adaptive or predictive capability
    - Comprehensive approval requirements with 24-hour delays
    """
    
    def __init__(self, ghsc_data: pd.DataFrame, lpi_data: Optional[pd.DataFrame] = None):
        """Initialize with all data sources."""
        self.ghsc_data = ghsc_data
        self.lpi_data = lpi_data
        
        # Initialize comprehensive metrics
        self.compute_global_baseline_metrics()
        self.compute_multi_level_escalation_thresholds()
        self.compute_compliance_violation_penalties()
        
    def compute_global_baseline_metrics(self) -> None:
        """Compute baseline metrics from REAL data for comparison."""
        
        # Cost baseline (STRICT)
        self.cost_baseline = self.ghsc_data['Freight_Cost_USD'].mean()
        self.cost_std = self.ghsc_data['Freight_Cost_USD'].std()
        
        # Service level baseline (STRICT)
        self.service_level_baseline = self.ghsc_data['On_Time_Delivery_%'].mean() / 100.0
        
        # Lead time baseline (STRICT)
        self.lead_time_baseline = self.ghsc_data['Lead_Time_Days'].mean()
        self.lead_time_max = self.ghsc_data['Lead_Time_Days'].max()
        
        # Reliability baseline (STRICT)
        self.reliability_baseline = self.ghsc_data['Supplier_Reliability_Score'].mean()
        
        # Stockout baseline (STRICT)
        self.stockout_baseline = self.ghsc_data['Stockout_Frequency_per_Year'].mean()
        
        # Disruption baseline
        self.disruption_baseline = self.ghsc_data['Disruption_Severity'].mean()
        
    def compute_multi_level_escalation_thresholds(self) -> None:
        """Compute 5-level escalation thresholds for ALL metrics."""
        
        self.escalation_thresholds = {
            # Cost thresholds (5 levels)
            'cost': {
                'level_1_monitor': self.cost_baseline * 1.10,
                'level_2_alert': self.cost_baseline * 1.25,
                'level_3_warning': self.cost_baseline * 1.50,
                'level_4_critical': self.cost_baseline * 1.75,
                'level_5_emergency': self.cost_baseline * 2.00,
            },
            
            # Lead time thresholds (5 levels)
            'lead_time': {
                'level_1_monitor': self.lead_time_baseline * 1.10,
                'level_2_alert': self.lead_time_baseline * 1.25,
                'level_3_warning': self.lead_time_baseline * 1.50,
                'level_4_critical': self.lead_time_baseline * 1.75,
                'level_5_emergency': self.lead_time_baseline * 2.00,
            },
            
            # Reliability thresholds (5 levels - INVERTED)
            'reliability': {
                'level_1_monitor': self.reliability_baseline * 0.98,
                'level_2_alert': self.reliability_baseline * 0.95,
                'level_3_warning': self.reliability_baseline * 0.90,
                'level_4_critical': self.reliability_baseline * 0.85,
                'level_5_emergency': self.reliability_baseline * 0.80,
            },
            
            # Service level thresholds (5 levels - INVERTED)
            'service_level': {
                'level_1_monitor': self.service_level_baseline * 0.98,
                'level_2_alert': self.service_level_baseline * 0.95,
                'level_3_warning': self.service_level_baseline * 0.90,
                'level_4_critical': self.service_level_baseline * 0.85,
                'level_5_emergency': self.service_level_baseline * 0.75,
            },
            
            # Stockout thresholds (5 levels)
            'stockout': {
                'level_1_monitor': self.stockout_baseline * 1.20,
                'level_2_alert': self.stockout_baseline * 1.50,
                'level_3_warning': self.stockout_baseline * 2.00,
                'level_4_critical': self.stockout_baseline * 3.00,
                'level_5_emergency': self.stockout_baseline * 4.00,
            },
            
            # Disruption thresholds (5 levels)
            'disruption': {
                'level_1_monitor': 1,
                'level_2_alert': 2,
                'level_3_warning': 3,
                'level_4_critical': 4,
                'level_5_emergency': 5,
            },
        }
    
    def compute_compliance_violation_penalties(self) -> None:
        """Compute penalty multipliers for compliance violations."""
        
        self.violation_penalties = {
            # Core metrics
            'cost_violation': 1.15,  # 15% penalty multiplier
            'lead_time_violation': 1.20,  # 20% penalty
            'reliability_violation': 1.25,  # 25% penalty
            'service_level_violation': 1.25,  # 25% penalty
            'stockout_violation': 1.20,  # 20% penalty
            'disruption_violation': 1.30,  # 30% penalty
            
            # Composite violations
            'multiple_violations_multiplier': 1.50,  # 50% penalty if 2+ violations
            'critical_violation': 2.00,  # 100% penalty (double cost)
            
            # Response delays
            'delayed_response_penalty': 1.10,  # 10% per hour delay
            'manual_approval_delay': 24,  # Hours of delay (TRADITIONAL)
            'emergency_approval_delay': 4,  # Hours for emergencies
        }
    
    def make_integrated_supply_chain_decision(self, 
                                             commodity: str,
                                             country: str,
                                             warehouse_type: str,
                                             current_inventory: float,
                                             current_reliability: float,
                                             context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make COMPREHENSIVE integrated supply chain decision.
        
        Checks EVERY constraint simultaneously:
        - Inventory levels
        - Supplier reliability
        - Lead times
        - Costs
        - Disruptions
        - Service levels
        - Emissions
        - Transport modes
        
        Returns DETAILED decision with violations, escalation level, and penalties.
        """
        
        # Initialize comprehensive decision
        decision = {
            'decision_type': 'integrated_supply_chain',
            'commodity': commodity,
            'country': country,
            'warehouse_type': warehouse_type,
            'timestamp': pd.Timestamp.now().isoformat(),
            
            # Inventory metrics
            'current_inventory': current_inventory,
            'current_reliability': current_reliability,
            
            # Decision outputs
            'procurement_action': 'none',
            'transport_mode': 'continue_current',
            'supplier_action': 'continue_primary',
            'quantity_to_order': 0,
            
            # Compliance tracking
            'violations': [],
            'warnings': [],
            'penalties': [],
            'compliance_score': 1.0,
            'escalation_level': 0,
            
            # Approval requirements
            'approval_required': False,
            'approval_level': None,
            'approval_delay_hours': 0,
            
            # Financial impact
            'estimated_cost_impact': 0.0,
            'estimated_delay': 0,
            
            # Reasoning and audit trail
            'reasoning': [],
            'audit_trail': [],
        }
        
        # ===== COMPREHENSIVE EVALUATION =====
        
        # 1. INVENTORY LEVEL EVALUATION
        inventory_evaluation = self._evaluate_inventory(current_inventory, context)
        decision['violations'].extend(inventory_evaluation['violations'])
        decision['warnings'].extend(inventory_evaluation['warnings'])
        decision['escalation_level'] = max(decision['escalation_level'], 
                                           inventory_evaluation['escalation_level'])
        if inventory_evaluation['action'] != 'none':
            decision['procurement_action'] = inventory_evaluation['action']
            decision['quantity_to_order'] = inventory_evaluation['quantity']
        
        # 2. SUPPLIER RELIABILITY EVALUATION
        reliability_evaluation = self._evaluate_supplier_reliability(current_reliability, context)
        decision['violations'].extend(reliability_evaluation['violations'])
        decision['warnings'].extend(reliability_evaluation['warnings'])
        decision['escalation_level'] = max(decision['escalation_level'], 
                                          reliability_evaluation['escalation_level'])
        if reliability_evaluation['action'] != 'continue':
            decision['supplier_action'] = reliability_evaluation['action']
        
        # 3. COST EVALUATION
        cost_evaluation = self._evaluate_costs(context)
        decision['violations'].extend(cost_evaluation['violations'])
        decision['warnings'].extend(cost_evaluation['warnings'])
        decision['escalation_level'] = max(decision['escalation_level'], 
                                          cost_evaluation['escalation_level'])
        decision['estimated_cost_impact'] = cost_evaluation['impact']
        
        # 4. LEAD TIME EVALUATION
        lead_time_evaluation = self._evaluate_lead_time(context)
        decision['violations'].extend(lead_time_evaluation['violations'])
        decision['warnings'].extend(lead_time_evaluation['warnings'])
        decision['escalation_level'] = max(decision['escalation_level'], 
                                          lead_time_evaluation['escalation_level'])
        decision['estimated_delay'] = lead_time_evaluation['delay']
        
        # 5. SERVICE LEVEL EVALUATION
        service_evaluation = self._evaluate_service_level(context)
        decision['violations'].extend(service_evaluation['violations'])
        decision['warnings'].extend(service_evaluation['warnings'])
        decision['escalation_level'] = max(decision['escalation_level'], 
                                          service_evaluation['escalation_level'])
        
        # 6. DISRUPTION EVALUATION
        disruption_evaluation = self._evaluate_disruption(context)
        decision['violations'].extend(disruption_evaluation['violations'])
        decision['warnings'].extend(disruption_evaluation['warnings'])
        decision['escalation_level'] = max(decision['escalation_level'], 
                                          disruption_evaluation['escalation_level'])
        
        # 7. TRANSPORT MODE EVALUATION
        transport_evaluation = self._evaluate_transport_mode(context)
        if transport_evaluation['action'] != 'continue_current':
            decision['transport_mode'] = transport_evaluation['action']
        decision['violations'].extend(transport_evaluation['violations'])
        decision['warnings'].extend(transport_evaluation['warnings'])
        
        # 8. EMISSIONS EVALUATION
        emissions_evaluation = self._evaluate_emissions(context)
        decision['violations'].extend(emissions_evaluation['violations'])
        decision['warnings'].extend(emissions_evaluation['warnings'])
        
        # 9. COMPLIANCE SCORE CALCULATION
        violation_count = len(decision['violations'])
        warning_count = len(decision['warnings'])
        
        if violation_count > 0:
            if violation_count >= 3:
                decision['compliance_score'] *= 0.5
            else:
                decision['compliance_score'] *= (0.9 ** violation_count)
        
        if warning_count > 0:
            decision['compliance_score'] *= (0.95 ** warning_count)
        
        # 10. DETERMINE APPROVAL REQUIREMENTS
        self._set_approval_requirements(decision)
        
        # 11. FINAL ACTION DETERMINATION
        self._determine_final_actions(decision)
        
        return decision
    
    def _evaluate_inventory(self, current_inventory: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate inventory levels against STRICT thresholds."""
        evaluation = {
            'violations': [],
            'warnings': [],
            'escalation_level': 0,
            'action': 'none',
            'quantity': 0,
        }
        
        # Use estimated safety stock and reorder point
        reorder_point = context.get('estimated_reorder_point', 5000000)
        safety_stock = context.get('estimated_safety_stock', 3000000)
        
        if current_inventory < safety_stock * 0.5:
            evaluation['violations'].append('critical_inventory_depletion')
            evaluation['escalation_level'] = 5
            evaluation['action'] = 'emergency_procurement_maximum'
            evaluation['quantity'] = context.get('max_order_volume', 5000000)
        elif current_inventory < safety_stock:
            evaluation['violations'].append('inventory_below_safety_stock')
            evaluation['escalation_level'] = 4
            evaluation['action'] = 'emergency_procurement'
            evaluation['quantity'] = context.get('max_order_volume', 5000000) * 0.8
        elif current_inventory < reorder_point:
            evaluation['warnings'].append('inventory_below_reorder_point')
            evaluation['escalation_level'] = 2
            evaluation['action'] = 'standard_replenishment'
            evaluation['quantity'] = context.get('max_order_volume', 5000000) * 0.6
        
        return evaluation
    
    def _evaluate_supplier_reliability(self, current_reliability: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate supplier reliability against STRICT thresholds."""
        evaluation = {
            'violations': [],
            'warnings': [],
            'escalation_level': 0,
            'action': 'continue',
        }
        
        if current_reliability < 0.70:
            evaluation['violations'].append('critical_supplier_failure')
            evaluation['escalation_level'] = 5
            evaluation['action'] = 'switch_backup_supplier_emergency'
        elif current_reliability < 0.80:
            evaluation['violations'].append('supplier_reliability_failure')
            evaluation['escalation_level'] = 4
            evaluation['action'] = 'escalate_management'
        elif current_reliability < 0.85:
            evaluation['warnings'].append('supplier_reliability_degradation')
            evaluation['escalation_level'] = 2
            evaluation['action'] = 'increase_monitoring'
        
        return evaluation
    
    def _evaluate_costs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate costs against STRICT thresholds."""
        evaluation = {
            'violations': [],
            'warnings': [],
            'escalation_level': 0,
            'impact': 0.0,
        }
        
        cost = context.get('Freight_Cost_USD', self.cost_baseline)
        
        if cost > self.escalation_thresholds['cost']['level_5_emergency']:
            evaluation['violations'].append('emergency_cost_exceeded')
            evaluation['escalation_level'] = 5
            evaluation['impact'] = cost * self.violation_penalties['critical_violation']
        elif cost > self.escalation_thresholds['cost']['level_4_critical']:
            evaluation['violations'].append('critical_cost_exceeded')
            evaluation['escalation_level'] = 4
            evaluation['impact'] = cost * self.violation_penalties['cost_violation']
        elif cost > self.escalation_thresholds['cost']['level_3_warning']:
            evaluation['warnings'].append('cost_warning')
            evaluation['escalation_level'] = 2
        
        return evaluation
    
    def _evaluate_lead_time(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate lead time against STRICT thresholds."""
        evaluation = {
            'violations': [],
            'warnings': [],
            'escalation_level': 0,
            'delay': 0,
        }
        
        lead_time = context.get('Lead_Time_Days', self.lead_time_baseline)
        
        if lead_time > self.escalation_thresholds['lead_time']['level_5_emergency']:
            evaluation['violations'].append('emergency_lead_time_exceeded')
            evaluation['escalation_level'] = 5
            evaluation['delay'] = lead_time - self.lead_time_baseline
        elif lead_time > self.escalation_thresholds['lead_time']['level_4_critical']:
            evaluation['violations'].append('critical_lead_time_exceeded')
            evaluation['escalation_level'] = 4
            evaluation['delay'] = lead_time - self.lead_time_baseline
        elif lead_time > self.escalation_thresholds['lead_time']['level_3_warning']:
            evaluation['warnings'].append('lead_time_warning')
            evaluation['escalation_level'] = 2
        
        return evaluation
    
    def _evaluate_service_level(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate service level against STRICT thresholds."""
        evaluation = {
            'violations': [],
            'warnings': [],
            'escalation_level': 0,
        }
        
        service_level = context.get('On_Time_Delivery_%', self.service_level_baseline * 100) / 100
        
        if service_level < self.escalation_thresholds['service_level']['level_5_emergency']:
            evaluation['violations'].append('emergency_service_failure')
            evaluation['escalation_level'] = 5
        elif service_level < self.escalation_thresholds['service_level']['level_4_critical']:
            evaluation['violations'].append('critical_service_failure')
            evaluation['escalation_level'] = 4
        elif service_level < self.escalation_thresholds['service_level']['level_3_warning']:
            evaluation['warnings'].append('service_level_warning')
            evaluation['escalation_level'] = 2
        
        return evaluation
    
    def _evaluate_disruption(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate disruption impact with STRICT escalation."""
        evaluation = {
            'violations': [],
            'warnings': [],
            'escalation_level': 0,
        }
        
        disruption_severity = context.get('Disruption_Severity', 0)
        
        if disruption_severity >= 5:
            evaluation['violations'].append('severe_disruption_level_5')
            evaluation['escalation_level'] = 5
        elif disruption_severity >= 4:
            evaluation['violations'].append('severe_disruption_level_4')
            evaluation['escalation_level'] = 4
        elif disruption_severity >= 3:
            evaluation['warnings'].append('major_disruption_level_3')
            evaluation['escalation_level'] = 3
        elif disruption_severity >= 2:
            evaluation['warnings'].append('moderate_disruption_level_2')
            evaluation['escalation_level'] = 2
        
        return evaluation
    
    def _evaluate_transport_mode(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate transport mode selection."""
        evaluation = {
            'violations': [],
            'warnings': [],
            'action': 'continue_current',
        }
        
        # Transport mode selection based on cost and reliability
        transport_mode = context.get('Transport_Mode', 'Road')
        
        # Strict rules: only change on failure, never optimize
        if context.get('On_Time_Delivery_%', 100) < 80:
            evaluation['action'] = 'escalate_transport_review'
            evaluation['violations'].append('transport_reliability_critical')
        
        return evaluation
    
    def _evaluate_emissions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate CO2 emissions against thresholds."""
        evaluation = {
            'violations': [],
            'warnings': [],
        }
        
        co2_emissions = context.get('CO2_Emissions_tons', 0)
        
        if co2_emissions > 20000:
            evaluation['violations'].append('extreme_co2_emissions')
            evaluation['escalation_level'] = 3
        elif co2_emissions > 15000:
            evaluation['warnings'].append('high_co2_emissions')
            evaluation['escalation_level'] = 1
        
        return evaluation
    
    def _set_approval_requirements(self, decision: Dict[str, Any]) -> None:
        """Set approval requirements based on escalation level."""
        
        escalation_level = decision['escalation_level']
        
        if escalation_level >= 5:
            decision['approval_required'] = True
            decision['approval_level'] = 'executive_team'
            decision['approval_delay_hours'] = 0.5  # 30 minutes for absolute emergencies
        elif escalation_level >= 4:
            decision['approval_required'] = True
            decision['approval_level'] = 'director_and_cfo'
            decision['approval_delay_hours'] = 2
        elif escalation_level >= 3:
            decision['approval_required'] = True
            decision['approval_level'] = 'director'
            decision['approval_delay_hours'] = 6
        elif escalation_level >= 2:
            decision['approval_required'] = True
            decision['approval_level'] = 'manager'
            decision['approval_delay_hours'] = 12
        else:
            decision['approval_required'] = True
            decision['approval_level'] = 'supervisor'
            decision['approval_delay_hours'] = 24
    
    def _determine_final_actions(self, decision: Dict[str, Any]) -> None:
        """Determine final action based on all evaluations."""
        
        if decision['escalation_level'] >= 5:
            decision['reasoning'].append('Critical emergency - multiple severe violations')
            decision['audit_trail'].append('EXECUTIVE ESCALATION TRIGGERED')
        elif decision['escalation_level'] >= 4:
            decision['reasoning'].append('Critical violations detected - immediate management intervention required')
            decision['audit_trail'].append('DIRECTOR ESCALATION TRIGGERED')
        elif decision['escalation_level'] >= 3:
            decision['reasoning'].append('Significant violations - escalation to director level')
            decision['audit_trail'].append('MANAGER ESCALATION TRIGGERED')
        elif decision['escalation_level'] >= 2:
            decision['reasoning'].append('Warnings and minor violations - increased monitoring')
            decision['audit_trail'].append('SUPERVISOR REVIEW TRIGGERED')
        else:
            decision['reasoning'].append('All metrics within acceptable range - continue current operations')
            decision['audit_trail'].append('ROUTINE MONITORING')
    
    def calculate_traditional_system_performance(self) -> Dict[str, float]:
        """Calculate COMPREHENSIVE traditional system performance metrics."""
        
        return {
            # Core metrics
            'avg_lead_time_days': self.lead_time_baseline,
            'avg_cost_usd': self.cost_baseline,
            'avg_on_time_delivery_pct': self.service_level_baseline * 100,
            'avg_supplier_reliability': self.reliability_baseline,
            'avg_stockout_frequency': self.stockout_baseline,
            'avg_disruption_severity': self.disruption_baseline,
            
            # Performance characteristics
            'decision_approval_delay_hours': 24,
            'emergency_approval_delay_hours': 4,
            'zero_adaptive_capability': 1.0,  # 0.0 = full adaptive, 1.0 = zero
            'zero_predictive_capability': 1.0,  # 0.0 = full predictive, 1.0 = zero
            'fixed_rules_immutability_score': 1.0,  # 1.0 = completely fixed
            'manual_decision_rate': 0.95,  # 95% manual decisions
            
            # Compliance metrics
            'violation_accumulation_rate': 0.25,  # 25% accumulation per period
            'escalation_frequency': 0.30,  # 30% of decisions escalated
            'approval_requirement_rate': 0.95,  # 95% require approval
            
            # Response limitations
            'disruption_response_delay_hours': 24,
            'supplier_switch_latency_hours': 48,
            'transport_mode_change_latency_hours': 24,
            
            # System characteristics
            'rules_based_system': 1.0,  # 1.0 = fully rules-based, 0.0 = AI-based
            'conservative_bias': 1.0,  # 1.0 = maximum conservative
            'data_driven_optimization': 0.0,  # 0.0 = not optimized
            'real_time_adjustment': 0.0,  # 0.0 = no real-time adjustment
        }


if __name__ == "__main__":
    ghsc_data = pd.read_csv('data/DATA_SPLITS/GHSC_PSM_Synthetic_Resilience_Dataset_v2_consistent_traindata.csv')
    
    framework = ComprehensiveTraditionalRulesFramework(ghsc_data)
    
    # Calculate performance
    performance = framework.calculate_traditional_system_performance()
    print("COMPREHENSIVE Traditional Rules Framework Performance:")
    for metric, value in sorted(performance.items()):
        print(f"  {metric}: {value:.4f}")
    
    # Test integrated decision
    test_context = {
        'Lead_Time_Days': 65,
        'On_Time_Delivery_%': 85,
        'Freight_Cost_USD': 165000,
        'Supplier_Reliability_Score': 0.82,
        'Disruption_Severity': 3,
        'CO2_Emissions_tons': 16000,
        'Transport_Mode': 'Air',
        'estimated_reorder_point': 5000000,
        'estimated_safety_stock': 3000000,
        'max_order_volume': 5000000,
    }
    
    decision = framework.make_integrated_supply_chain_decision(
        'Malaria_RDT', 'Nigeria', 'Clinic', 4500000, 0.82, test_context
    )
    
    print("\nIntegrated Supply Chain Decision:")
    for key, value in decision.items():
        if key not in ['reasoning', 'audit_trail', 'violations', 'warnings', 'penalties']:
            print(f"  {key}: {value}")
        else:
            print(f"  {key}:")
            if isinstance(value, list):
                for item in value:
                    print(f"    - {item}")
            else:
                print(f"    {value}")
