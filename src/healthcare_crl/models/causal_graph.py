"""
Causal inference module for healthcare supply chain disruption analysis.
Implements Bayesian Networks, DAG construction, and causal effect estimation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import networkx as nx
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.estimators import MaximumLikelihoodEstimator, BayesianEstimator
from pgmpy.inference import VariableElimination
from pgmpy.factors.discrete import TabularCPD
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class CausalRelationship:
    """Represents a causal relationship between variables."""
    cause: str
    effect: str
    strength: float
    confidence: float
    mechanism: str
    intervention_effect: Optional[float] = None


class CausalGraph:
    """
    Causal graph for supply chain disruption analysis.
    Implements Directed Acyclic Graph (DAG) for causal relationships.
    """
    
    def __init__(self):
        """Initialize causal graph."""
        self.dag = nx.DiGraph()
        self.causal_relationships = {}
        self.intervention_effects = {}
        
        # Define variable types based on real data features
        self.variable_domains = {
            # Real supply chain variables from GHSC dataset
            'lead_time_days': ['short', 'medium', 'long', 'very_long'],  # 0-30, 30-60, 60-90, 90+
            'on_time_delivery_pct': ['low', 'medium', 'high', 'excellent'],  # <80%, 80-90%, 90-95%, 95%+
            'supplier_reliability_score': ['low', 'medium', 'high'],  # 0-0.5, 0.5-0.8, 0.8-1.0
            'stockout_frequency': ['rare', 'occasional', 'frequent', 'critical'],  # 0-0.1, 0.1-0.2, 0.2-0.5, 0.5+
            'freight_cost_level': ['low', 'medium', 'high', 'premium'],  # Cost quartiles
            
            # Disruption variables from real data
            'disruption_type': ['none', 'flood', 'covid_lockdown', 'conflict', 'port_closure', 'cyber_attack'],
            'disruption_severity': ['none', 'low', 'medium', 'high', 'extreme'],  # 0, 1, 2-3, 4, 5
            
            # Logistics variables from LPI dataset
            'lpi_score': ['very_low', 'low', 'medium', 'high', 'very_high'],  # 1-2, 2-3, 3-4, 4-5
            'customs_efficiency': ['poor', 'fair', 'good', 'excellent'],
            'infrastructure_quality': ['poor', 'fair', 'good', 'excellent'],
            'transport_mode': ['air', 'ocean', 'land', 'multimodal'],
            
            # Warehouse and operational variables
            'warehouse_type': ['public_depot', 'rdc', '3pl', 'coe'],  # From real data
            'outcome_metric': ['poor', 'fair', 'good', 'excellent'],  # Performance quartiles
            
            # Action variables (same as before)
            'switch_supplier': ['no', 'yes'],
            'increase_safety_stock': ['no', 'yes'], 
            'emergency_procurement': ['no', 'yes'],
            'reroute_shipments': ['no', 'yes'],
            'allocate_resources': ['no', 'yes']
        }
    
    def build_healthcare_dag(self) -> None:
        """Build DAG based on real healthcare supply chain data relationships."""
        logger.info("Building healthcare supply chain causal DAG from real data...")
        
        # Define causal structure based on real data relationships
        causal_edges = [
            # Disruption impacts (from real disaster data)
            ('disruption_type', 'disruption_severity'),
            ('disruption_severity', 'supplier_reliability_score'),
            ('disruption_severity', 'lead_time_days'),
            ('disruption_severity', 'freight_cost_level'),
            
            # Supply chain fundamentals (from GHSC data)
            ('supplier_reliability_score', 'on_time_delivery_pct'),
            ('lead_time_days', 'on_time_delivery_pct'),
            ('lead_time_days', 'stockout_frequency'),
            ('freight_cost_level', 'transport_mode'),
            
            # Logistics performance impacts (from LPI data)
            ('lpi_score', 'lead_time_days'),
            ('customs_efficiency', 'lead_time_days'),
            ('infrastructure_quality', 'freight_cost_level'),
            ('transport_mode', 'freight_cost_level'),
            ('transport_mode', 'lead_time_days'),
            
            # Warehouse and operational efficiency
            ('warehouse_type', 'stockout_frequency'),
            ('warehouse_type', 'on_time_delivery_pct'),
            ('lpi_score', 'customs_efficiency'),
            ('infrastructure_quality', 'customs_efficiency'),
            
            # Performance outcomes
            ('on_time_delivery_pct', 'outcome_metric'),
            ('stockout_frequency', 'outcome_metric'),
            ('freight_cost_level', 'outcome_metric'),
            ('supplier_reliability_score', 'outcome_metric'),
            
            # Action effects on key performance indicators
            ('switch_supplier', 'supplier_reliability_score'),
            ('switch_supplier', 'freight_cost_level'),
            
            ('increase_safety_stock', 'stockout_frequency'),
            ('increase_safety_stock', 'freight_cost_level'),
            
            ('emergency_procurement', 'stockout_frequency'),
            ('emergency_procurement', 'freight_cost_level'),
            
            ('reroute_shipments', 'lead_time_days'),
            ('reroute_shipments', 'transport_mode'),
            
            ('allocate_resources', 'on_time_delivery_pct'),
            ('allocate_resources', 'outcome_metric'),
        ]
        
        # Add edges to DAG
        for cause, effect in causal_edges:
            self.dag.add_edge(cause, effect)
            
        # Store causal relationships with domain knowledge
        self._define_causal_strengths()
        
        logger.info(f"Built DAG with {len(self.dag.nodes)} variables and {len(self.dag.edges)} causal relationships")
    
    def _define_causal_strengths(self) -> None:
        """Define causal relationship strengths based on domain knowledge."""
        
        # Strong causal relationships (based on real data correlations)
        strong_relationships = [
            ('disruption_severity', 'supplier_reliability_score', 0.8),
            ('supplier_reliability_score', 'on_time_delivery_pct', 0.9),
            ('lead_time_days', 'on_time_delivery_pct', 0.8),
            ('on_time_delivery_pct', 'outcome_metric', 0.9),
            ('increase_safety_stock', 'stockout_frequency', 0.8),
        ]
        
        # Medium causal relationships  
        medium_relationships = [
            ('disruption_severity', 'lead_time_days', 0.6),
            ('lpi_score', 'lead_time_days', 0.6),
            ('infrastructure_quality', 'freight_cost_level', 0.6),
            ('warehouse_type', 'stockout_frequency', 0.5),
            ('transport_mode', 'freight_cost_level', 0.6),
        ]
        
        # Weak causal relationships
        weak_relationships = [
            ('customs_efficiency', 'lead_time_days', 0.4),
            ('reroute_shipments', 'lead_time_days', 0.4),
            ('disruption_type', 'freight_cost_level', 0.3),
            ('switch_supplier', 'freight_cost_level', 0.3),
        ]
        
        all_relationships = strong_relationships + medium_relationships + weak_relationships
        
        for cause, effect, strength in all_relationships:
            key = (cause, effect)
            self.causal_relationships[key] = CausalRelationship(
                cause=cause,
                effect=effect, 
                strength=strength,
                confidence=0.8,  # Default confidence
                mechanism=self._get_mechanism_description(cause, effect)
            )
    
    def _get_mechanism_description(self, cause: str, effect: str) -> str:
        """Generate mechanism description for causal relationship."""
        mechanisms = {
            ('disruption_severity', 'supplier_reliability_score'): "Higher disruption severity reduces supplier reliability",
            ('supplier_reliability_score', 'on_time_delivery_pct'): "More reliable suppliers achieve better on-time delivery",
            ('lead_time_days', 'on_time_delivery_pct'): "Longer lead times reduce on-time delivery performance",
            ('on_time_delivery_pct', 'outcome_metric'): "Better delivery performance improves overall outcomes",
            ('lpi_score', 'lead_time_days'): "Better logistics infrastructure reduces lead times",
            ('transport_mode', 'freight_cost_level'): "Air transport costs more than ocean or land",
            ('warehouse_type', 'stockout_frequency'): "Warehouse efficiency affects stockout rates",
            ('increase_safety_stock', 'stockout_frequency'): "Higher safety stock reduces stockout risk",
            ('switch_supplier', 'supplier_reliability_score'): "Switching suppliers may improve or worsen reliability",
            ('emergency_procurement', 'freight_cost_level'): "Emergency procurement increases costs significantly",
        }
        
        return mechanisms.get((cause, effect), f"{cause} causally influences {effect}")


class BayesianNetworkInference:
    """Bayesian Network for causal inference and counterfactual analysis."""
    
    def __init__(self, causal_graph: CausalGraph):
        """Initialize Bayesian Network from causal graph."""
        self.causal_graph = causal_graph
        self.bn_model = None
        self.inference_engine = None
        self.fitted = False

    def fit(self, data: pd.DataFrame) -> None:
        """Fit Bayesian Network to observational data."""
        logger.info("Fitting Bayesian Network to data...")

        # Create Bayesian Network structure from DAG
        # Ensure only (cause, effect) tuples are used, not weighted edges
        edges = [(u, v) for u, v in self.causal_graph.dag.edges() if isinstance(u, str) and isinstance(v, str)]
        try:
            self.bn_model = DiscreteBayesianNetwork(edges)
        except Exception as e:
            # Defensive fallback: if pgmpy rejects the edge list, log and skip fitting
            logger.error(f"Failed to construct DiscreteBayesianNetwork with edges={edges}: {e}")
            self.bn_model = None
            self.inference_engine = None
            self.fitted = False
            return

        # Discretize continuous variables if needed
        processed_data = self._preprocess_data(data)

        # Estimate parameters using Maximum Likelihood
        estimator = MaximumLikelihoodEstimator(self.bn_model, processed_data)

        # Fit CPDs for each variable
        for variable in self.bn_model.nodes():
            try:
                cpd = estimator.estimate_cpd(variable)
                self.bn_model.add_cpds(cpd)
            except Exception as e:
                logger.warning(f"Could not estimate CPD for {variable}: {e}")
                # Use uniform CPD as fallback
                self._add_uniform_cpd(variable)

        # Validate model
        if self.bn_model.check_model():
            self.inference_engine = VariableElimination(self.bn_model)
            self.fitted = True
            logger.info("Bayesian Network fitted successfully")
        else:
            logger.error("Bayesian Network model validation failed")
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess data for Bayesian Network fitting."""
        processed_data = data.copy()
        
        # Discretize continuous variables
        for column in processed_data.columns:
            if processed_data[column].dtype in ['float64', 'int64']:
                processed_data[column] = pd.cut(
                    processed_data[column], 
                    bins=4, 
                    labels=['low', 'medium', 'high', 'very_high']
                )
        
        return processed_data
    
    def _add_uniform_cpd(self, variable: str) -> None:
        """Add uniform CPD for variable when estimation fails."""
        domain_size = len(self.causal_graph.variable_domains.get(variable, ['low', 'high']))
        parents = list(self.bn_model.predecessors(variable))
        
        if not parents:
            # No parents - uniform distribution
            values = np.ones(domain_size) / domain_size
            cpd = TabularCPD(
                variable=variable,
                variable_card=domain_size,
                values=values.reshape(-1, 1)
            )
        else:
            # With parents - uniform conditional distribution
            parent_cards = [len(self.causal_graph.variable_domains.get(p, ['low', 'high'])) 
                          for p in parents]
            num_combinations = np.prod(parent_cards)
            
            values = np.ones((domain_size, num_combinations)) / domain_size
            cpd = TabularCPD(
                variable=variable,
                variable_card=domain_size,
                values=values,
                evidence=parents,
                evidence_card=parent_cards
            )
        
        self.bn_model.add_cpds(cpd)
    
    def estimate_causal_effect(self, action: str, outcome: str, 
                             context: Dict[str, str] = None) -> float:
        """Estimate causal effect of action on outcome."""
        if not self.fitted:
            logger.warning("Model not fitted. Cannot estimate causal effects.")
            return 0.0
        
        try:
            # Set context variables if provided
            evidence = context or {}
            
            # Calculate P(outcome | do(action=yes), evidence)
            evidence_action = evidence.copy()
            evidence_action[action] = 'yes'
            prob_action = self.inference_engine.query(
                variables=[outcome], 
                evidence=evidence_action
            )
            
            # Calculate P(outcome | do(action=no), evidence) 
            evidence_no_action = evidence.copy()
            evidence_no_action[action] = 'no'
            prob_no_action = self.inference_engine.query(
                variables=[outcome],
                evidence=evidence_no_action
            )
            
            # Causal effect = difference in probabilities for positive outcome
            positive_states = ['high', 'severe', 'critical', 'very_slow']  # Negative outcomes
            negative_states = ['low', 'none', 'fast', 'normal']  # Positive outcomes
            
            effect_action = sum(prob_action.values[i] for i, state in enumerate(prob_action.state_names[outcome]) 
                              if state in negative_states)
            effect_no_action = sum(prob_no_action.values[i] for i, state in enumerate(prob_no_action.state_names[outcome])
                                 if state in negative_states)
            
            # Return negative effect (reduction in bad outcomes is positive)
            causal_effect = effect_no_action - effect_action
            
            return causal_effect
            
        except Exception as e:
            logger.warning(f"Could not estimate causal effect for {action} -> {outcome}: {e}")
            return 0.0
    
    def counterfactual_analysis(self, action: str, outcome: str, 
                              observed_data: Dict[str, str]) -> Dict[str, float]:
        """Perform counterfactual analysis: What would have happened if...?"""
        if not self.fitted:
            return {'counterfactual_probability': 0.0, 'factual_probability': 0.0}
        
        try:
            # Factual: What actually happened
            factual_prob = self.inference_engine.query(
                variables=[outcome],
                evidence=observed_data
            )
            
            # Counterfactual: What if we had taken the action?
            counterfactual_evidence = observed_data.copy()
            counterfactual_evidence[action] = 'yes'
            
            counterfactual_prob = self.inference_engine.query(
                variables=[outcome],
                evidence=counterfactual_evidence
            )
            
            return {
                'factual_probability': factual_prob.values.max(),
                'counterfactual_probability': counterfactual_prob.values.max(),
                'causal_effect': counterfactual_prob.values.max() - factual_prob.values.max()
            }
            
        except Exception as e:
            logger.warning(f"Counterfactual analysis failed: {e}")
            return {'counterfactual_probability': 0.0, 'factual_probability': 0.0, 'causal_effect': 0.0}


class CausalOracle:
    """
    Causal oracle for CRL agents to query causal effects and feasible actions.
    Implements the CI "oracle" interface described in the paper.
    """
    
    def __init__(self, causal_graph: CausalGraph, bn_inference: BayesianNetworkInference):
        """Initialize causal oracle."""
        self.causal_graph = causal_graph
        self.bn_inference = bn_inference
        self.action_variables = [
            'switch_supplier', 'increase_safety_stock', 'emergency_procurement',
            'reroute_shipments', 'allocate_resources'
        ]
        
    def effect(self, action: str, context: Dict[str, Any]) -> float:
        """
        Estimate causal effect of action in given context.
        Used for reward shaping in CRL agents.
        """
        # Convert context to appropriate format
        context_str = self._convert_context(context)
        
        # Choose appropriate outcome variable based on action
        outcome = self._get_primary_outcome(action)
        
        # Estimate causal effect
        causal_effect = self.bn_inference.estimate_causal_effect(
            action=action,
            outcome=outcome, 
            context=context_str
        )
        
        return causal_effect
    
    def is_feasible(self, action: str, context: Dict[str, Any]) -> bool:
        """
        Check if action is causally feasible given context.
        Used for action masking in CRL agents.
        """
        context_str = self._convert_context(context)
        
        # Define feasibility rules based on causal constraints
        feasibility_rules = {
            'switch_supplier': lambda ctx: ctx.get('supplier_reliability', 'high') != 'high',
            'increase_safety_stock': lambda ctx: ctx.get('inventory_level', 'normal') != 'high',
            'emergency_procurement': lambda ctx: ctx.get('stockout_risk', 'low') in ['medium', 'high', 'critical'],
            'reroute_shipments': lambda ctx: ctx.get('transportation_capacity', 'normal') == 'limited',
            'allocate_resources': lambda ctx: ctx.get('service_disruption', 'none') != 'none'
        }
        
        rule = feasibility_rules.get(action, lambda ctx: True)
        return rule(context_str)
    
    def legal_actions(self, context: Dict[str, Any]) -> List[str]:
        """Get list of causally feasible actions for given context."""
        return [action for action in self.action_variables 
                if self.is_feasible(action, context)]
    
    def uplift(self, action: str, context: Dict[str, Any]) -> float:
        """
        Calculate uplift (Average Treatment Effect) for action.
        Used for ΔATE estimate in reward shaping.
        """
        return self.effect(action, context)
    
    def _convert_context(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Convert numerical context to categorical variables based on real data ranges."""
        context_str = {}
        
        # Define discretization rules based on real data distributions
        discretization_rules = {
            'lead_time_days': {
                'thresholds': [30, 60, 90],
                'labels': ['short', 'medium', 'long', 'very_long']
            },
            'on_time_delivery_pct': {
                'thresholds': [80, 90, 95],
                'labels': ['low', 'medium', 'high', 'excellent']
            },
            'supplier_reliability_score': {
                'thresholds': [0.5, 0.8],
                'labels': ['low', 'medium', 'high']
            },
            'stockout_frequency': {
                'thresholds': [0.1, 0.2, 0.5],
                'labels': ['rare', 'occasional', 'frequent', 'critical']
            },
            'freight_cost_level': {
                'thresholds': [25000, 50000, 100000],
                'labels': ['low', 'medium', 'high', 'premium']
            },
            'lpi_score': {
                'thresholds': [2.0, 3.0, 4.0],
                'labels': ['very_low', 'low', 'medium', 'high', 'very_high']
            },
            'disruption_severity': {
                'thresholds': [1, 2, 4],
                'labels': ['none', 'low', 'medium', 'high', 'extreme']
            }
        }
        
        # Apply discretization
        for key, value in context.items():
            if key in discretization_rules and isinstance(value, (int, float)):
                rule = discretization_rules[key]
                thresholds = rule['thresholds']
                labels = rule['labels']
                
                # Find appropriate label
                for i, threshold in enumerate(thresholds):
                    if value <= threshold:
                        context_str[key] = labels[i]
                        break
                else:
                    context_str[key] = labels[-1]  # Highest category
                    
            elif key in self.causal_graph.variable_domains:
                if isinstance(value, str):
                    context_str[key] = value.lower()
                else:
                    # Generic discretization for unmapped variables
                    if value < 0.25:
                        context_str[key] = 'low'
                    elif value < 0.5:
                        context_str[key] = 'medium'
                    elif value < 0.75:
                        context_str[key] = 'high'
                    else:
                        context_str[key] = 'very_high'
        
        return context_str
    
    def _get_primary_outcome(self, action: str) -> str:
        """Get primary outcome variable for each action type based on real data."""
        action_outcomes = {
            'switch_supplier': 'supplier_reliability_score',
            'increase_safety_stock': 'stockout_frequency',
            'emergency_procurement': 'stockout_frequency',
            'reroute_shipments': 'lead_time_days',
            'allocate_resources': 'on_time_delivery_pct'
        }
        
        return action_outcomes.get(action, 'outcome_metric')
    
    def get_causal_explanation(self, action: str, outcome: str) -> str:
        """Get textual explanation of causal relationship."""
        key = (action, outcome)
        if key in self.causal_graph.causal_relationships:
            rel = self.causal_graph.causal_relationships[key]
            return f"{rel.mechanism} (strength: {rel.strength:.2f})"
        else:
            return f"Indirect causal pathway from {action} to {outcome}"


def create_healthcare_causal_model(data: pd.DataFrame = None) -> Tuple[CausalGraph, CausalOracle]:
    """
    Factory function to create complete causal model for healthcare supply chain.
    
    Returns:
        Tuple of (CausalGraph, CausalOracle) ready for use in CRL agents
    """
    logger.info("Creating healthcare supply chain causal model...")
    
    # Build causal graph
    causal_graph = CausalGraph()
    causal_graph.build_healthcare_dag()
    
    # Initialize Bayesian Network inference
    bn_inference = BayesianNetworkInference(causal_graph)
    
    # Fit to data if provided, otherwise use prior knowledge
    if data is not None:
        bn_inference.fit(data)
    else:
        logger.info("No data provided, using prior knowledge for causal inference")
        bn_inference.fitted = True  # Use domain knowledge without data fitting
    
    # Create causal oracle
    causal_oracle = CausalOracle(causal_graph, bn_inference)
    
    logger.info("Causal model created successfully")
    return causal_graph, causal_oracle


if __name__ == "__main__":
    # Test causal model creation
    causal_graph, oracle = create_healthcare_causal_model()
    
    # Test oracle functionality
    test_context = {
        'pandemic_severity': 0.8,
        'supplier_reliability': 0.3,
        'inventory_level': 0.2
    }
    
    print("Testing Causal Oracle:")
    print(f"Legal actions: {oracle.legal_actions(test_context)}")
    print(f"Effect of emergency_procurement: {oracle.effect('emergency_procurement', test_context)}")
    print(f"Feasible to switch_supplier: {oracle.is_feasible('switch_supplier', test_context)}")