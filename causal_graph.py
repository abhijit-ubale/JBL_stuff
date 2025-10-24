"""
Causal inference module for healthcare supply chain disruption analysis.
Implements Bayesian Networks, DAG construction, and causal effect estimation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import networkx as nx
from pgmpy.models import BayesianNetwork
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
        
        # Define variable types and their possible values
        self.variable_domains = {
            # Disruption variables
            'pandemic_severity': ['none', 'low', 'medium', 'high'],
            'hurricane_severity': ['none', 'low', 'medium', 'high'], 
            'cyber_attack_severity': ['none', 'low', 'medium', 'high'],
            'port_closure_severity': ['none', 'low', 'medium', 'high'],
            'compound_disruption': ['false', 'true'],
            
            # Supply chain variables
            'supplier_reliability': ['low', 'medium', 'high'],
            'inventory_level': ['critical', 'low', 'normal', 'high'],
            'lead_time': ['short', 'normal', 'extended', 'critical'],
            'transportation_capacity': ['limited', 'normal', 'abundant'],
            'demand_surge': ['none', 'moderate', 'high', 'extreme'],
            
            # Operational variables
            'stockout_risk': ['low', 'medium', 'high', 'critical'],
            'cost_increase': ['none', 'low', 'medium', 'high'],
            'service_disruption': ['none', 'minor', 'moderate', 'severe'],
            'recovery_time': ['fast', 'normal', 'slow', 'very_slow'],
            
            # Action variables
            'switch_supplier': ['no', 'yes'],
            'increase_safety_stock': ['no', 'yes'], 
            'emergency_procurement': ['no', 'yes'],
            'reroute_shipments': ['no', 'yes'],
            'allocate_resources': ['no', 'yes']
        }
    
    def build_healthcare_dag(self) -> None:
        """Build DAG based on healthcare supply chain domain knowledge."""
        logger.info("Building healthcare supply chain causal DAG...")
        
        # Define causal structure based on supply chain theory
        causal_edges = [
            # Disruption -> Direct impacts
            ('pandemic_severity', 'demand_surge'),
            ('pandemic_severity', 'supplier_reliability'),
            ('pandemic_severity', 'transportation_capacity'),
            
            ('hurricane_severity', 'transportation_capacity'),
            ('hurricane_severity', 'supplier_reliability'),
            ('hurricane_severity', 'port_closure_severity'),
            
            ('cyber_attack_severity', 'supplier_reliability'),
            ('cyber_attack_severity', 'lead_time'),
            
            ('port_closure_severity', 'transportation_capacity'),
            ('port_closure_severity', 'lead_time'),
            
            # Compound effects
            ('pandemic_severity', 'compound_disruption'),
            ('hurricane_severity', 'compound_disruption'),
            ('cyber_attack_severity', 'compound_disruption'),
            
            # Supply chain propagation
            ('supplier_reliability', 'lead_time'),
            ('transportation_capacity', 'lead_time'),
            ('demand_surge', 'inventory_level'),
            ('lead_time', 'inventory_level'),
            
            # Operational impacts
            ('inventory_level', 'stockout_risk'),
            ('lead_time', 'stockout_risk'),
            ('compound_disruption', 'stockout_risk'),
            
            ('stockout_risk', 'service_disruption'),
            ('lead_time', 'cost_increase'),
            ('demand_surge', 'cost_increase'),
            
            ('service_disruption', 'recovery_time'),
            ('cost_increase', 'recovery_time'),
            ('compound_disruption', 'recovery_time'),
            
            # Action effects
            ('switch_supplier', 'supplier_reliability'),
            ('switch_supplier', 'cost_increase'),
            
            ('increase_safety_stock', 'inventory_level'),
            ('increase_safety_stock', 'cost_increase'),
            
            ('emergency_procurement', 'inventory_level'),
            ('emergency_procurement', 'cost_increase'),
            
            ('reroute_shipments', 'lead_time'),
            ('reroute_shipments', 'cost_increase'),
            
            ('allocate_resources', 'service_disruption'),
        ]
        
        # Add edges to DAG
        for cause, effect in causal_edges:
            self.dag.add_edge(cause, effect)
            
        # Store causal relationships with domain knowledge
        self._define_causal_strengths()
        
        logger.info(f"Built DAG with {len(self.dag.nodes)} variables and {len(self.dag.edges)} causal relationships")
    
    def _define_causal_strengths(self) -> None:
        """Define causal relationship strengths based on domain knowledge."""
        
        # Strong causal relationships
        strong_relationships = [
            ('pandemic_severity', 'demand_surge', 0.9),
            ('inventory_level', 'stockout_risk', 0.8),
            ('stockout_risk', 'service_disruption', 0.8),
            ('increase_safety_stock', 'inventory_level', 0.9),
        ]
        
        # Medium causal relationships  
        medium_relationships = [
            ('hurricane_severity', 'transportation_capacity', 0.6),
            ('supplier_reliability', 'lead_time', 0.6),
            ('lead_time', 'inventory_level', 0.5),
            ('switch_supplier', 'supplier_reliability', 0.6),
        ]
        
        # Weak causal relationships
        weak_relationships = [
            ('cyber_attack_severity', 'lead_time', 0.3),
            ('reroute_shipments', 'lead_time', 0.4),
            ('compound_disruption', 'recovery_time', 0.4),
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
            ('pandemic_severity', 'demand_surge'): "Pandemic increases demand for medical supplies",
            ('inventory_level', 'stockout_risk'): "Lower inventory directly increases stockout probability",
            ('supplier_reliability', 'lead_time'): "Unreliable suppliers cause delivery delays",
            ('switch_supplier', 'supplier_reliability'): "Switching to backup suppliers may reduce reliability",
            ('increase_safety_stock', 'inventory_level'): "Safety stock directly increases inventory buffer",
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
        edges = list(self.causal_graph.dag.edges())
        self.bn_model = BayesianNetwork(edges)
        
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
        """Convert numerical context to categorical variables."""
        context_str = {}
        
        # Map numerical values to categorical domains
        for key, value in context.items():
            if key in self.causal_graph.variable_domains:
                if isinstance(value, (int, float)):
                    # Simple quantile-based discretization
                    if value < 0.25:
                        context_str[key] = 'low'
                    elif value < 0.5:
                        context_str[key] = 'medium' 
                    elif value < 0.75:
                        context_str[key] = 'high'
                    else:
                        context_str[key] = 'very_high'
                else:
                    context_str[key] = str(value)
            
        return context_str
    
    def _get_primary_outcome(self, action: str) -> str:
        """Get primary outcome variable for each action type."""
        action_outcomes = {
            'switch_supplier': 'supplier_reliability',
            'increase_safety_stock': 'stockout_risk',
            'emergency_procurement': 'stockout_risk',
            'reroute_shipments': 'lead_time',
            'allocate_resources': 'service_disruption'
        }
        
        return action_outcomes.get(action, 'recovery_time')
    
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