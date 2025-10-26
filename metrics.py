"""
Resilience metrics implementation for healthcare supply chain evaluation.
Implements all 10 metrics from the research paper.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class EpisodeData:
    """Container for episode performance data."""
    episode_id: int
    agent_type: str
    disruption_type: str
    start_time: datetime
    end_time: datetime
    actions_taken: List[Dict[str, Any]]
    state_trajectory: List[Dict[str, float]]
    rewards: List[float]
    costs: List[float]
    service_levels: List[float]
    inventory_levels: List[float]
    supplier_performances: List[Dict[str, float]]
    
    
class ResilienceMetrics:
    """
    Implementation of 10 resilience metrics from the research paper.
    Provides comprehensive evaluation of supply chain performance.
    """
    
    def __init__(self):
        """Initialize metrics calculator."""
        self.baseline_performance = None
        self.metric_definitions = self._define_metrics()
        
    def _define_metrics(self) -> Dict[str, Dict[str, str]]:
        """Define metric formulas and descriptions."""
        return {
            'recovery_time': {
                'formula': 'RT = t(recovery) - t(disruption)',
                'description': 'Duration required for supply chain to return to pre-disruption service level',
                'unit': 'time_steps',
                'interpretation': 'lower_is_better'
            },
            'service_level_stability': {
                'formula': 'SLV = σ²(service_level)',
                'description': 'Variance in order-fulfillment rates during and after disruption',
                'unit': 'variance',
                'interpretation': 'lower_is_better'
            },
            'cost_variance': {
                'formula': 'CV = (C_actual - C_planned) / C_planned',
                'description': 'Difference between planned and actual procurement/logistics costs',
                'unit': 'percentage',
                'interpretation': 'lower_is_better'
            },
            'supplier_reliability_index': {
                'formula': 'SRI = w₁(OTD) + w₂(Quality) + w₃(ResponseTime)',
                'description': 'Composite supplier performance score',
                'unit': 'index_0_to_1',
                'interpretation': 'higher_is_better'
            },
            'inventory_turnover_ratio': {
                'formula': 'ITR = COGS / Average_Inventory',
                'description': 'Frequency of inventory replenishment',
                'unit': 'ratio',
                'interpretation': 'higher_is_better'
            },
            'disruption_impact_index': {
                'formula': 'DII = Σ(operational_losses) across throughput, lead_time, cost',
                'description': 'Overall operational loss from multi-source disruptions',
                'unit': 'normalized_loss',
                'interpretation': 'lower_is_better'
            },
            'resilience_index': {
                'formula': 'RI = Performance_post / Performance_pre',
                'description': 'Ratio of post-disruption to pre-disruption performance',
                'unit': 'ratio',
                'interpretation': 'higher_is_better'
            },
            'digital_responsiveness_score': {
                'formula': 'DRS = time_lag between disruption detection and first automated action',
                'description': 'Speed of automated system response',
                'unit': 'time_steps',
                'interpretation': 'lower_is_better'
            },
            'managerial_interpretability_score': {
                'formula': 'MIS = survey score of AI recommendation clarity and trust',
                'description': 'Trust and understanding of AI decisions',
                'unit': 'score_1_to_5',
                'interpretation': 'higher_is_better'
            },
            'carbon_resilience_metric': {
                'formula': 'CRM = alignment of recovery actions with carbon reduction',
                'description': 'Sustainability of recovery strategies',
                'unit': 'sustainability_score',
                'interpretation': 'higher_is_better'
            }
        }
    
    def calculate_recovery_time(self, episode_data: EpisodeData, 
                               baseline_service_level: float = 0.95) -> Dict[str, float]:
        """
        Calculate Recovery Time (RT) - Metric 1
        RT = t(recovery) - t(disruption)
        """
        service_levels = episode_data.service_levels
        
        if len(service_levels) == 0:
            return {'recovery_time': float('inf'), 'recovery_achieved': False}
        
        # Find disruption start (significant drop in service level)
        disruption_start = 0
        for i in range(1, len(service_levels)):
            if service_levels[i] < baseline_service_level * 0.8:  # 20% drop threshold
                disruption_start = i
                break
        
        # Find recovery point (return to baseline)
        recovery_point = None
        for i in range(disruption_start, len(service_levels)):
            if service_levels[i] >= baseline_service_level * 0.95:  # 95% of baseline
                recovery_point = i
                break
        
        if recovery_point is not None:
            recovery_time = recovery_point - disruption_start
            recovery_achieved = True
        else:
            recovery_time = len(service_levels) - disruption_start  # Didn't recover
            recovery_achieved = False
        
        return {
            'recovery_time': float(recovery_time),
            'recovery_achieved': recovery_achieved,
            'disruption_start': disruption_start,
            'recovery_point': recovery_point
        }
    
    def calculate_service_level_stability(self, episode_data: EpisodeData) -> Dict[str, float]:
        """
        Calculate Service-Level Stability (SLV) - Metric 2
        SLV = σ²(service_level)
        """
        service_levels = episode_data.service_levels
        
        if len(service_levels) < 2:
            return {'slv_variance': 0.0, 'slv_std': 0.0, 'slv_cv': 0.0}
        
        variance = np.var(service_levels)
        std_dev = np.std(service_levels)
        mean_service = np.mean(service_levels)
        coefficient_variation = std_dev / mean_service if mean_service > 0 else float('inf')
        
        return {
            'slv_variance': float(variance),
            'slv_std': float(std_dev),
            'slv_cv': float(coefficient_variation),
            'mean_service_level': float(mean_service)
        }
    
    def calculate_cost_variance(self, episode_data: EpisodeData, 
                               baseline_cost_per_step: float = 100.0) -> Dict[str, float]:
        """
        Calculate Cost Variance (CV) - Metric 3
        CV = (C_actual - C_planned) / C_planned
        """
        costs = episode_data.costs
        
        if len(costs) == 0:
            return {'cost_variance': 0.0, 'total_cost_increase': 0.0}
        
        total_actual_cost = sum(costs)
        total_planned_cost = baseline_cost_per_step * len(costs)
        
        cost_variance = (total_actual_cost - total_planned_cost) / total_planned_cost
        cost_increase = total_actual_cost - total_planned_cost
        
        # Cost volatility (additional measure)
        cost_volatility = np.std(costs) / np.mean(costs) if np.mean(costs) > 0 else 0.0
        
        return {
            'cost_variance': float(cost_variance),
            'total_cost_increase': float(cost_increase),
            'cost_volatility': float(cost_volatility),
            'total_actual_cost': float(total_actual_cost),
            'total_planned_cost': float(total_planned_cost)
        }
    
    def calculate_supplier_reliability_index(self, episode_data: EpisodeData) -> Dict[str, float]:
        """
        Calculate Supplier Reliability Index (SRI) - Metric 4
        SRI = w₁(OTD) + w₂(Quality) + w₃(ResponseTime)
        """
        supplier_performances = episode_data.supplier_performances
        
        if len(supplier_performances) == 0:
            return {'sri_score': 0.5, 'otd_score': 0.5, 'quality_score': 0.5, 'response_score': 0.5}
        
        # Weights for SRI components
        w1, w2, w3 = 0.4, 0.35, 0.25  # On-time delivery, Quality, Response time
        
        # Aggregate supplier performance metrics
        otd_scores = []
        quality_scores = []
        response_scores = []
        
        for perf in supplier_performances:
            otd_scores.append(perf.get('on_time_delivery', 0.5))
            quality_scores.append(perf.get('quality_compliance', 0.5))
            response_scores.append(perf.get('response_time_score', 0.5))
        
        avg_otd = np.mean(otd_scores)
        avg_quality = np.mean(quality_scores)  
        avg_response = np.mean(response_scores)
        
        sri_score = w1 * avg_otd + w2 * avg_quality + w3 * avg_response
        
        return {
            'sri_score': float(sri_score),
            'otd_score': float(avg_otd),
            'quality_score': float(avg_quality), 
            'response_score': float(avg_response),
            'num_suppliers_evaluated': len(supplier_performances)
        }
    
    def calculate_inventory_turnover_ratio(self, episode_data: EpisodeData) -> Dict[str, float]:
        """
        Calculate Inventory Turnover Ratio (ITR) - Metric 5
        ITR = COGS / Average_Inventory
        """
        inventory_levels = episode_data.inventory_levels
        costs = episode_data.costs
        
        if len(inventory_levels) == 0 or len(costs) == 0:
            return {'itr_ratio': 0.0, 'avg_inventory': 0.0, 'total_cogs': 0.0}
        
        # Cost of Goods Sold approximation (sum of procurement costs)
        total_cogs = sum(costs)
        
        # Average inventory level during period
        avg_inventory = np.mean(inventory_levels)
        
        # ITR calculation
        itr_ratio = total_cogs / avg_inventory if avg_inventory > 0 else 0.0
        
        # Additional inventory efficiency metrics
        inventory_variance = np.var(inventory_levels)
        stockout_periods = sum(1 for level in inventory_levels if level < 0.1)
        
        return {
            'itr_ratio': float(itr_ratio),
            'avg_inventory': float(avg_inventory),
            'total_cogs': float(total_cogs),
            'inventory_variance': float(inventory_variance),
            'stockout_periods': int(stockout_periods)
        }
    
    def calculate_disruption_impact_index(self, episode_data: EpisodeData) -> Dict[str, float]:
        """
        Calculate Disruption Impact Index (DII) - Metric 6
        DII = Σ(operational_losses) across throughput, lead_time, cost
        """
        
        # Normalized operational loss components
        service_loss = self._calculate_service_loss(episode_data)
        cost_loss = self._calculate_cost_impact(episode_data)
        time_loss = self._calculate_lead_time_impact(episode_data)
        
        # Weighted combination of losses
        w_service, w_cost, w_time = 0.5, 0.3, 0.2
        
        dii_score = w_service * service_loss + w_cost * cost_loss + w_time * time_loss
        
        return {
            'dii_score': float(dii_score),
            'service_loss_component': float(service_loss),
            'cost_loss_component': float(cost_loss),
            'time_loss_component': float(time_loss)
        }
    
    def _calculate_service_loss(self, episode_data: EpisodeData) -> float:
        """Calculate normalized service level loss based on real data."""
        service_levels = episode_data.service_levels
        if len(service_levels) == 0:
            return 0.0
        
        # Use real data baseline (average on-time delivery from GHSC data is ~88%)
        baseline_service = 0.88  # Real data baseline
        service_shortfall = max(0, baseline_service - np.mean(service_levels))
        return service_shortfall / baseline_service
    
    def _calculate_cost_impact(self, episode_data: EpisodeData) -> float:
        """Calculate normalized cost impact based on real freight cost data."""
        costs = episode_data.costs
        if len(costs) == 0:
            return 0.0
        
        # Use real data baseline (median freight cost from GHSC data ~70K USD)
        baseline_cost = 70.0  # Normalized baseline from real data
        avg_actual_cost = np.mean(costs)
        cost_increase = max(0, avg_actual_cost - baseline_cost)
        return min(1.0, cost_increase / baseline_cost)  # Cap at 100% increase
    
    def _calculate_lead_time_impact(self, episode_data: EpisodeData) -> float:
        """Calculate normalized lead time impact."""
        # Extract lead time proxy from state trajectory
        if len(episode_data.state_trajectory) == 0:
            return 0.0
        
        lead_times = [state.get('lead_time', 0.5) for state in episode_data.state_trajectory]
        baseline_lead_time = 0.3  # Expected normalized lead time
        avg_lead_time = np.mean(lead_times)
        lead_time_increase = max(0, avg_lead_time - baseline_lead_time)
        return min(1.0, lead_time_increase / (1.0 - baseline_lead_time))
    
    def calculate_resilience_index(self, episode_data: EpisodeData, 
                                  baseline_performance: Dict[str, float] = None) -> Dict[str, float]:
        """
        Calculate Resilience Index (RI) - Metric 7
        RI = Performance_post / Performance_pre
        """
        
        if baseline_performance is None:
            # Use real data baselines from GHSC dataset
            baseline_performance = {
                'service_level': 0.88,  # Average on-time delivery from real data
                'cost_efficiency': 1.0,
                'inventory_turnover': 8.0  # Adjusted for healthcare supply chains
            }
        
        # Calculate post-disruption performance
        post_performance = self._calculate_overall_performance(episode_data)
        
        # Baseline (pre-disruption) performance
        baseline_overall = (
            baseline_performance['service_level'] * 0.5 +
            baseline_performance['cost_efficiency'] * 0.3 +
            (baseline_performance['inventory_turnover'] / 20.0) * 0.2  # Normalize ITR
        )
        
        resilience_index = post_performance / baseline_overall if baseline_overall > 0 else 0.0
        
        return {
            'resilience_index': float(resilience_index),
            'post_disruption_performance': float(post_performance),
            'baseline_performance': float(baseline_overall)
        }
    
    def _calculate_overall_performance(self, episode_data: EpisodeData) -> float:
        """Calculate composite performance score."""
        
        # Service level component
        service_component = np.mean(episode_data.service_levels) if episode_data.service_levels else 0.0
        
        # Cost efficiency component (inverse of cost increase)
        costs = episode_data.costs
        if costs:
            baseline_cost = 70.0  # Real data baseline
            avg_cost = np.mean(costs)
            cost_efficiency = baseline_cost / avg_cost if avg_cost > 0 else 0.0
        else:
            cost_efficiency = 1.0
        
        # Inventory efficiency component
        inventory_levels = episode_data.inventory_levels
        if inventory_levels and costs:
            avg_inventory = np.mean(inventory_levels)
            total_cogs = sum(costs)
            itr = total_cogs / avg_inventory if avg_inventory > 0 else 0.0
            inventory_efficiency = min(1.0, itr / 12.0)  # Normalize based on healthcare norms
        else:
            inventory_efficiency = 0.5
        
        # Weighted combination
        overall_performance = (
            service_component * 0.5 +
            cost_efficiency * 0.3 +
            inventory_efficiency * 0.2
        )
        
        return overall_performance
    
    def calculate_digital_responsiveness_score(self, episode_data: EpisodeData) -> Dict[str, float]:
        """
        Calculate Digital Responsiveness Score (DRS) - Metric 8
        DRS = time_lag between disruption detection and first automated action
        """
        
        actions = episode_data.actions_taken
        states = episode_data.state_trajectory
        
        if len(actions) == 0 or len(states) == 0:
            return {'drs_lag': float('inf'), 'disruption_detected': False, 'response_time': float('inf')}
        
        # Detect disruption point (significant state change)
        disruption_point = self._detect_disruption_point(states)
        
        # Find first automated response action (non-"no_action")
        first_response = None
        for i, action in enumerate(actions):
            if action.get('action_type', 'no_action') != 'no_action':
                first_response = i
                break
        
        if disruption_point is not None and first_response is not None:
            response_lag = max(0, first_response - disruption_point)
        else:
            response_lag = float('inf')
        
        # Additional responsiveness metrics
        total_actions = len([a for a in actions if a.get('action_type', 'no_action') != 'no_action'])
        action_frequency = total_actions / len(actions) if len(actions) > 0 else 0.0
        
        return {
            'drs_lag': float(response_lag),
            'disruption_detected': disruption_point is not None,
            'response_time': float(response_lag) if response_lag != float('inf') else None,
            'total_automated_actions': total_actions,
            'action_frequency': float(action_frequency)
        }
    
    def _detect_disruption_point(self, states: List[Dict[str, float]]) -> Optional[int]:
        """Detect when disruption begins based on state changes."""
        
        if len(states) < 3:
            return None
        
        # Look for significant changes in key state variables
        for i in range(1, len(states)):
            current_state = states[i]
            prev_state = states[i-1]
            
            # Check for disruption indicators
            service_drop = (prev_state.get('service_level', 1.0) - current_state.get('service_level', 1.0)) > 0.2
            inventory_drop = (prev_state.get('inventory_level', 1.0) - current_state.get('inventory_level', 1.0)) > 0.3
            lead_time_increase = (current_state.get('lead_time', 0.0) - prev_state.get('lead_time', 0.0)) > 0.2
            
            if service_drop or inventory_drop or lead_time_increase:
                return i
        
        return None
    
    def calculate_managerial_interpretability_score(self, episode_data: EpisodeData,
                                                   explainability_features: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Calculate Managerial Interpretability Score (MIS) - Metric 9
        MIS = survey score of AI recommendation clarity and trust (1-5 scale)
        """
        
        # In practice, this would be based on user surveys
        # For simulation, we calculate based on action consistency and explainability features
        
        if explainability_features is None:
            explainability_features = {
                'causal_explanations_provided': True,
                'action_consistency': 0.8,
                'explanation_quality': 0.7
            }
        
        # Simulate MIS based on explainability features
        base_score = 3.0  # Neutral score
        
        # Adjust based on features
        if explainability_features.get('causal_explanations_provided', False):
            base_score += 0.5
        
        consistency = explainability_features.get('action_consistency', 0.5)
        base_score += (consistency - 0.5) * 2  # Scale to [-1, 1] then to score adjustment
        
        explanation_quality = explainability_features.get('explanation_quality', 0.5)
        base_score += (explanation_quality - 0.5) * 1.5
        
        # Clamp to [1, 5] scale
        mis_score = max(1.0, min(5.0, base_score))
        
        # Calculate interpretability metrics from actions
        actions = episode_data.actions_taken
        action_diversity = len(set(a.get('action_type', 'no_action') for a in actions)) / 6.0  # 6 possible actions
        
        return {
            'mis_score': float(mis_score),
            'base_interpretability': float(base_score),
            'action_diversity': float(action_diversity),
            'causal_explanations_available': explainability_features.get('causal_explanations_provided', False)
        }
    
    def calculate_carbon_resilience_metric(self, episode_data: EpisodeData) -> Dict[str, float]:
        """
        Calculate Carbon and Sustainability Resilience Metric (CRM) - Metric 10
        CRM = alignment of recovery actions with carbon reduction and ESG objectives
        """
        
        actions = episode_data.actions_taken
        
        if len(actions) == 0:
            return {'crm_score': 0.5, 'sustainable_actions_ratio': 0.0, 'carbon_impact_score': 0.5}
        
        # Define sustainability scores for each action type
        action_sustainability = {
            'switch_supplier': 0.3,  # May increase transportation
            'increase_safety_stock': 0.2,  # Increases inventory holding
            'emergency_procurement': 0.1,  # Often uses air freight (high carbon)
            'reroute_shipments': 0.4,  # Can optimize for efficiency  
            'allocate_resources': 0.8,  # Efficient resource use
            'no_action': 0.6  # Neutral impact
        }
        
        # Calculate weighted sustainability score
        total_weight = 0
        weighted_sustainability = 0
        
        for action in actions:
            action_type = action.get('action_type', 'no_action')
            weight = 1.0  # Equal weighting for now
            sustainability = action_sustainability.get(action_type, 0.5)
            
            weighted_sustainability += weight * sustainability
            total_weight += weight
        
        avg_sustainability = weighted_sustainability / total_weight if total_weight > 0 else 0.5
        
        # Calculate sustainable actions ratio
        sustainable_actions = sum(1 for action in actions 
                                if action_sustainability.get(action.get('action_type', 'no_action'), 0.5) > 0.5)
        sustainable_ratio = sustainable_actions / len(actions)
        
        # Bonus for consistency with sustainability goals
        consistency_bonus = 0.1 if sustainable_ratio > 0.6 else 0.0
        
        crm_score = avg_sustainability + consistency_bonus
        
        return {
            'crm_score': float(min(1.0, crm_score)),
            'sustainable_actions_ratio': float(sustainable_ratio),
            'carbon_impact_score': float(avg_sustainability),
            'total_actions_evaluated': len(actions)
        }
    
    def calculate_all_metrics(self, episode_data: EpisodeData, 
                            baseline_performance: Dict[str, float] = None,
                            explainability_features: Dict[str, Any] = None) -> Dict[str, Dict[str, float]]:
        """Calculate all 10 resilience metrics for an episode."""
        
        logger.info(f"Calculating all resilience metrics for episode {episode_data.episode_id}")
        
        metrics = {}
        
        try:
            metrics['recovery_time'] = self.calculate_recovery_time(episode_data)
            metrics['service_level_stability'] = self.calculate_service_level_stability(episode_data)
            metrics['cost_variance'] = self.calculate_cost_variance(episode_data)
            metrics['supplier_reliability_index'] = self.calculate_supplier_reliability_index(episode_data)
            metrics['inventory_turnover_ratio'] = self.calculate_inventory_turnover_ratio(episode_data)
            metrics['disruption_impact_index'] = self.calculate_disruption_impact_index(episode_data)
            metrics['resilience_index'] = self.calculate_resilience_index(episode_data, baseline_performance)
            metrics['digital_responsiveness_score'] = self.calculate_digital_responsiveness_score(episode_data)
            metrics['managerial_interpretability_score'] = self.calculate_managerial_interpretability_score(
                episode_data, explainability_features)
            metrics['carbon_resilience_metric'] = self.calculate_carbon_resilience_metric(episode_data)
            
            logger.info("Successfully calculated all 10 resilience metrics")
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            # Return default values on error
            for metric_name in self.metric_definitions.keys():
                if metric_name not in metrics:
                    metrics[metric_name] = {'score': 0.0, 'error': str(e)}
        
        return metrics
    
    def compare_agents(self, agent_results: Dict[str, List[EpisodeData]]) -> pd.DataFrame:
        """Compare multiple agents across all resilience metrics."""
        
        comparison_data = []
        
        for agent_name, episodes in agent_results.items():
            agent_metrics = []
            
            for episode in episodes:
                episode_metrics = self.calculate_all_metrics(episode)
                
                # Extract key metric values
                metrics_row = {
                    'agent': agent_name,
                    'episode': episode.episode_id,
                    'disruption_type': episode.disruption_type
                }
                
                # Add main metric values
                for metric_name, metric_data in episode_metrics.items():
                    if isinstance(metric_data, dict):
                        # Use the main score from each metric
                        main_keys = {
                            'recovery_time': 'recovery_time',
                            'service_level_stability': 'slv_variance', 
                            'cost_variance': 'cost_variance',
                            'supplier_reliability_index': 'sri_score',
                            'inventory_turnover_ratio': 'itr_ratio',
                            'disruption_impact_index': 'dii_score',
                            'resilience_index': 'resilience_index',
                            'digital_responsiveness_score': 'drs_lag',
                            'managerial_interpretability_score': 'mis_score',
                            'carbon_resilience_metric': 'crm_score'
                        }
                        
                        key = main_keys.get(metric_name, list(metric_data.keys())[0])
                        metrics_row[metric_name] = metric_data.get(key, 0.0)
                
                comparison_data.append(metrics_row)
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Calculate summary statistics by agent
        summary_stats = comparison_df.groupby('agent').agg({
            'recovery_time': ['mean', 'std'],
            'service_level_stability': ['mean', 'std'],
            'cost_variance': ['mean', 'std'],
            'supplier_reliability_index': ['mean', 'std'],
            'inventory_turnover_ratio': ['mean', 'std'],
            'disruption_impact_index': ['mean', 'std'],
            'resilience_index': ['mean', 'std'],
            'digital_responsiveness_score': ['mean', 'std'],
            'managerial_interpretability_score': ['mean', 'std'],
            'carbon_resilience_metric': ['mean', 'std']
        }).round(3)
        
        return comparison_df, summary_stats
    
    def get_metric_definitions(self) -> Dict[str, Dict[str, str]]:
        """Get definitions of all metrics."""
        return self.metric_definitions.copy()


if __name__ == "__main__":
    # Test resilience metrics
    from datetime import datetime
    
    # Create sample episode data
    episode = EpisodeData(
        episode_id=1,
        agent_type='crl_agent',
        disruption_type='pandemic',
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        actions_taken=[
            {'action_type': 'emergency_procurement', 'timestamp': 10},
            {'action_type': 'increase_safety_stock', 'timestamp': 20}
        ],
        state_trajectory=[
            {'service_level': 0.95, 'inventory_level': 0.8, 'lead_time': 0.3},
            {'service_level': 0.7, 'inventory_level': 0.4, 'lead_time': 0.6},
            {'service_level': 0.85, 'inventory_level': 0.6, 'lead_time': 0.4}
        ],
        rewards=[1.0, -0.5, 0.5],
        costs=[100, 150, 120],
        service_levels=[0.95, 0.7, 0.85],
        inventory_levels=[0.8, 0.4, 0.6],
        supplier_performances=[
            {'on_time_delivery': 0.9, 'quality_compliance': 0.95, 'response_time_score': 0.8},
            {'on_time_delivery': 0.6, 'quality_compliance': 0.8, 'response_time_score': 0.4}
        ]
    )
    
    # Calculate metrics
    metrics_calculator = ResilienceMetrics()
    all_metrics = metrics_calculator.calculate_all_metrics(episode)
    
    print("Resilience Metrics Results:")
    for metric_name, metric_data in all_metrics.items():
        print(f"{metric_name}: {metric_data}")