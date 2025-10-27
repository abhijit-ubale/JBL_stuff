"""
Healthcare Supply Chain Causal-Reinforcement Learning Framework
Main entry point for running CRL experiments and simulations.

Usage:
    python main.py --config experiments/default_config.yaml --mode train
    python main.py --config experiments/quick_test_config.yaml --mode evaluate  
    python main.py --mode dashboard
"""

import logging
import argparse
import sys
import os
import time
from pathlib import Path
import yaml
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add src directory to path for imports

# Import framework components
import src.healthcare_crl
from src.healthcare_crl.data.pipeline import RealDataPipeline
from src.healthcare_crl.models.causal_graph import create_healthcare_causal_model, CausalOracle
from src.healthcare_crl.agents.crl_agent import CausalRLAgent, MultiAgentCRL
from src.healthcare_crl.baselines.baselines import BaselineAgents
from src.healthcare_crl.utils.metrics import ResilienceMetrics, EpisodeData

# Import traditional baseline from data directory
from data.TRADITIONAL_RULES.traditional_baseline_system import TraditionalBaselineSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crl_experiment.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


class HealthcareCRLEnvironment:
    """
    Real data healthcare supply chain environment for CRL experiments.
    Uses actual supply chain, logistics, and disaster data from CSV files.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize environment from configuration."""
        self.config = config
        env_config = config.get('environment', {})
        self.episode_length = env_config.get('episode_length', 50)
        self.disruption_types = env_config.get('disruption_types', ['pandemic'])
        
        # Initialize real data pipeline
        data_splits_path = env_config.get('data_splits_path', 'data/DATA_SPLITS')
        self.data_pipeline = RealDataPipeline(data_splits_path)
        
        # State and action space dimensions from real data
        self.state_size = self.data_pipeline.get_state_dimension()  # Real feature vector size
        self.action_size = self.data_pipeline.get_action_space_size()  # 6 actions
        
        # Environment state
        self.current_step = 0
        self.current_state = None
        self.disruption_active = False
        self.disruption_severity = 0.0
        
        # Real data for episode simulation
        self.episode_records = []
        self.current_record_index = 0
        
        # Performance tracking
        self.episode_data = None
        
        # Get dataset statistics
        stats = self.data_pipeline.get_dataset_statistics()
        total_records = sum(stat.get('num_records', 0) for stat in stats.values())
        
        logger.info(f"Initialized environment with real data pipeline")
        logger.info(f"Total records across all datasets: {total_records}")
        logger.info(f"State dimension: {self.state_size}, Action dimension: {self.action_size}")
    
    def reset(self) -> np.ndarray:
        """Reset environment for new episode using real data."""
        self.current_step = 0
        self.disruption_active = False
        self.disruption_severity = 0.0
        self.current_record_index = 0
        
        # Sample episode data from real datasets
        try:
            self.episode_records = self.data_pipeline.sample_episode_data(
                mode='train', 
                episode_length=self.episode_length
            )
        except Exception as e:
            logger.error(f"Error sampling episode data: {e}")
            # Fallback to default state
            self.episode_records = [{'step': i, 'episode_progress': i/self.episode_length} 
                                  for i in range(self.episode_length)]
        
        # Get initial state from first record
        if self.episode_records:
            initial_record = self.episode_records[0]
            self.current_state = self.data_pipeline.get_feature_vector_for_state(initial_record)
        else:
            # Fallback state
            self.current_state = np.zeros(self.state_size)
        
        # Initialize episode data collection
        self.episode_data = {
            'states': [self.current_state.copy()],
            'actions': [],
            'rewards': [],
            'costs': [100.0],  # baseline cost
            'service_levels': [self.current_state[1] if len(self.current_state) > 1 else 0.95],
            'inventory_levels': [self.current_state[0] if len(self.current_state) > 0 else 0.8],
            'supplier_performances': [{
                'on_time_delivery': self.current_state[2] if len(self.current_state) > 2 else 0.9,
                'quality_compliance': 0.95,
                'response_time_score': 0.8
            }],
            'disruption_events': []
        }
        
        return self.current_state.copy()
    
    def step(self, action: int) -> tuple:
        """Execute action and return next state, reward, done, info."""
        self.current_step += 1
        self.current_record_index = min(self.current_record_index + 1, len(self.episode_records) - 1)
        
        # Get next state from real data record
        if self.current_record_index < len(self.episode_records):
            current_record = self.episode_records[self.current_record_index]
            
            # Check for disruptions in the data
            disruption_type = current_record.get('Disruption_Type', 'None')
            if disruption_type and disruption_type != 'None':
                self.disruption_active = True
                self.disruption_severity = current_record.get('Disruption_Severity', 0) / 5.0  # Normalize
            else:
                self.disruption_active = False
                self.disruption_severity = 0.0
            
            # Get state from real data
            next_state = self.data_pipeline.get_feature_vector_for_state(current_record)
        else:
            # Use last available state if we run out of records
            next_state = self.current_state.copy()
        
        # Apply action effects to the state
        next_state, reward, cost = self._apply_action_to_real_state(action, next_state, current_record)
        
        # Update state
        self.current_state = next_state
        
        # Check if episode is done
        done = self.current_step >= self.episode_length
        
        # Create context for causal oracle
        context = self._get_context_from_real_data(current_record)
        
        # Store step data
        self.episode_data['states'].append(next_state.copy())
        self.episode_data['actions'].append({
            'action_type': self._action_to_name(action),
            'timestamp': self.current_step
        })
        self.episode_data['rewards'].append(reward)
        self.episode_data['costs'].append(cost)
        self.episode_data['service_levels'].append(next_state[1] if len(next_state) > 1 else 0.5)
        self.episode_data['inventory_levels'].append(next_state[0] if len(next_state) > 0 else 0.5)
        
        info = {
            'context': context,
            'disruption_active': self.disruption_active,
            'step': self.current_step,
            'real_data_record': current_record
        }
        
        return next_state.copy(), reward, done, info
    
    def _apply_action_to_real_state(self, action: int, state: np.ndarray, record: Dict[str, Any]) -> tuple:
        """Apply action effects to real data-based state."""
        next_state = state.copy()
        base_reward = 1.0
        
        # Extract base cost from real data
        base_cost = record.get('Freight_Cost_USD', 100.0) / 1000.0  # Normalize
        
        # Action effects based on real supply chain principles
        if action == 0:  # switch_supplier
            # Improve supplier reliability but increase cost
            if len(next_state) > 2:
                next_state[2] = min(1.0, next_state[2] + 0.1)  # supplier_reliability
            base_cost *= 1.2
            
        elif action == 1:  # increase_safety_stock
            # Improve inventory position, reduce stockout risk
            if len(next_state) > 0:
                next_state[0] = min(1.0, next_state[0] + 0.15)  # inventory proxy
            base_cost *= 1.3
            
        elif action == 2:  # emergency_procurement
            # Significant inventory improvement at high cost
            if len(next_state) > 0:
                next_state[0] = min(1.0, next_state[0] + 0.2)
            base_cost *= 1.5
            
        elif action == 3:  # reroute_shipments
            # Reduce lead time indicator
            if len(next_state) > 0:
                next_state[0] = min(1.0, next_state[0] + 0.1)  # Improve lead time proxy
            base_cost *= 1.1
            
        elif action == 4:  # allocate_resources
            # Improve overall service level
            if len(next_state) > 1:
                next_state[1] = min(1.0, next_state[1] + 0.05)  # service level proxy
        
        # Apply disruption effects if present
        disruption_severity = record.get('Disruption_Severity', 0) / 5.0
        if disruption_severity > 0:
            # Degrade performance during disruptions
            next_state = next_state * (1 - disruption_severity * 0.1)
        
        # Calculate reward based on real performance indicators
        on_time_delivery = record.get('On_Time_Delivery_%', 90) / 100.0
        outcome_metric = record.get('Outcome_Metric', 0.5)
        
        # Reward components
        delivery_reward = (on_time_delivery - 0.9) * 2.0  # Reward for above 90% OTD
        outcome_reward = (outcome_metric - 0.5) * 2.0  # Reward for above median outcome
        cost_penalty = -min((base_cost - 100.0) / 100.0, 1.0)  # Cost penalty
        disruption_penalty = -disruption_severity * 0.5  # Disruption penalty
        
        reward = base_reward + delivery_reward + outcome_reward + cost_penalty + disruption_penalty
        
        return next_state, reward, base_cost
    
    def _get_context_from_real_data(self, record: Dict[str, Any]) -> Dict[str, float]:
        """Extract context from real data record for causal oracle."""
        context = {}
        
        # Map real data fields to context variables
        context['supplier_reliability'] = record.get('Supplier_Reliability_Score', 0.5)
        context['lead_time'] = min(record.get('Lead_Time_Days', 30) / 100.0, 1.0)  # Normalize
        context['on_time_delivery'] = record.get('On_Time_Delivery_%', 90) / 100.0
        context['freight_cost'] = min(record.get('Freight_Cost_USD', 50000) / 100000.0, 1.0)  # Normalize
        context['stockout_frequency'] = record.get('Stockout_Frequency_per_Year', 0.1)
        
        # Disruption context
        disruption_type = record.get('Disruption_Type', 'None')
        context['pandemic_severity'] = 0.8 if 'COVID' in str(disruption_type) else 0.0
        context['hurricane_severity'] = 0.7 if 'Flood' in str(disruption_type) else 0.0
        context['cyber_attack_severity'] = 0.6 if 'Cyber' in str(disruption_type) else 0.0
        context['port_closure_severity'] = 0.5 if 'Port' in str(disruption_type) else 0.0
        
        # Logistics context
        context['transport_mode'] = record.get('Transport_Mode', 'Air')
        context['warehouse_type'] = record.get('Warehouse_Type', 'RDC')
        
        return context
    
    def _action_to_name(self, action: int) -> str:
        """Convert action index to name."""
        action_names = {
            0: 'switch_supplier',
            1: 'increase_safety_stock',
            2: 'emergency_procurement', 
            3: 'reroute_shipments',
            4: 'allocate_resources',
            5: 'no_action'
        }
        return action_names.get(action, 'unknown')
    
    def _get_context(self) -> Dict[str, float]:
        """Get context dictionary for causal oracle from current state."""
        context = {}
        
        # Map state vector indices to context variables
        if len(self.current_state) >= 20:
            context['lead_time'] = self.current_state[0]
            context['service_level'] = self.current_state[1] 
            context['supplier_reliability'] = self.current_state[2]
            context['stockout_frequency'] = self.current_state[3]
            context['inventory_level'] = self.current_state[5]  # LPI-related
            context['pandemic_severity'] = self.current_state[7]  # Disruption severity
            context['disaster_risk'] = self.current_state[10] if len(self.current_state) > 10 else 0.0
        else:
            # Fallback for shorter state vectors
            context = {
                'lead_time': self.current_state[0] if len(self.current_state) > 0 else 0.5,
                'service_level': self.current_state[1] if len(self.current_state) > 1 else 0.5,
                'supplier_reliability': self.current_state[2] if len(self.current_state) > 2 else 0.5,
                'inventory_level': 0.5,
                'pandemic_severity': 0.0,
                'hurricane_severity': 0.0,
                'cyber_attack_severity': 0.0,
                'stockout_risk': 0.1
            }
        
        return context
    
    def get_episode_data(self) -> EpisodeData:
        """Convert collected data to EpisodeData format."""
        return EpisodeData(
            episode_id=1,  # Would be managed by experiment runner
            agent_type='unknown',  # Set by experiment runner
            disruption_type=self.episode_data['disruption_events'][0]['type'] if self.episode_data['disruption_events'] else 'none',
            start_time=datetime.now(),
            end_time=datetime.now(),
            actions_taken=self.episode_data['actions'],
            state_trajectory=[{'service_level': s[0], 'inventory_level': s[1], 'lead_time': s[2]} 
                            for s in self.episode_data['states']],
            rewards=self.episode_data['rewards'],
            costs=self.episode_data['costs'],
            service_levels=self.episode_data['service_levels'],
            inventory_levels=self.episode_data['inventory_levels'],
            supplier_performances=self.episode_data['supplier_performances']
        )


class ExperimentRunner:
    """Manages CRL experiments and comparative evaluation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize experiment runner."""
        self.config = config
        self.results_dir = Path(config['experiment']['results_dir'])
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics calculator
        self.metrics_calculator = ResilienceMetrics()
        
        logger.info(f"Experiment runner initialized. Results will be saved to {self.results_dir}")
    
    def run_training_experiment(self) -> Dict[str, Any]:
        """Run CRL agent training experiment."""
        logger.info("Starting CRL training experiment...")
        
        # Create environment
        env_config = self.config['environment']
        env = HealthcareCRLEnvironment(env_config)
        
        # Create causal model
        causal_graph, causal_oracle = create_healthcare_causal_model()
        
        # Create CRL agent
        agent_config = self.config['agents']['crl_agent']
        agent = CausalRLAgent(
            state_size=env.state_size,
            action_size=env.action_size,
            causal_oracle=causal_oracle,
            learning_rate=agent_config.get('learning_rate', 1e-4),
            causal_lambda=agent_config.get('causal_lambda', 0.3),
            use_action_masking=agent_config.get('use_action_masking', True),
            use_reward_shaping=agent_config.get('use_reward_shaping', True)
        )
        
        # Training loop
        num_episodes = self.config['experiment']['num_episodes']
        episode_data_list = []
        
        for episode in range(num_episodes):
            state = env.reset()
            total_reward = 0
            done = False
            
            while not done:
                # Get context for causal reasoning
                context = env._get_context()
                
                # Select action
                action = agent.act(state, context)
                
                # Execute action
                next_state, reward, done, info = env.step(action)
                
                # Learn from experience
                agent.learn(state, action, reward, next_state, done, context)
                
                state = next_state
                total_reward += reward
            
            # Episode completed
            agent.episode_ended(total_reward)
            
            # Collect episode data
            episode_data = env.get_episode_data()
            episode_data.episode_id = episode
            episode_data.agent_type = 'crl_agent'
            episode_data_list.append(episode_data)
            
            # Log progress
            if episode % 100 == 0:
                logger.info(f"Episode {episode}/{num_episodes}, Total Reward: {total_reward:.2f}")
        
        # Save results
        results = {
            'agent_type': 'crl_agent',
            'episodes': episode_data_list,
            'training_metrics': agent.get_metrics(),
            'config': self.config
        }
        
        self._save_results(results, 'crl_training_results.json')
        
        logger.info(f"Training completed. {num_episodes} episodes finished.")
        return results
    
    def run_comparative_evaluation(self) -> Dict[str, Any]:
        """Run comparative evaluation across all agents."""
        logger.info("Starting comparative evaluation...")
        
        # Create environment
        env_config = self.config['environment']
        
        # Create causal model  
        causal_graph, causal_oracle = create_healthcare_causal_model()
        
        # Create all agents
        agents = {
            'crl_agent': CausalRLAgent(
                state_size=20, action_size=6, causal_oracle=causal_oracle,
                **self.config['agents']['crl_agent']
            ),
            'deterministic': BaselineAgents.create_deterministic_agent(20, 6),
            'pure_rl': BaselineAgents.create_pure_rl_agent(20, 6),
            'causal_heuristic': BaselineAgents.create_causal_heuristic_agent(20, 6, causal_oracle)
        }
        
        # Run experiments for each agent
        all_results = {}
        num_episodes = self.config['experiment']['num_episodes']
        
        for agent_name, agent in agents.items():
            logger.info(f"Evaluating {agent_name}...")
            
            env = HealthcareCRLEnvironment(env_config)
            episode_data_list = []
            
            for episode in range(num_episodes):
                state = env.reset()
                total_reward = 0
                done = False
                
                while not done:
                    context = env._get_context()
                    action = agent.act(state, context)
                    next_state, reward, done, info = env.step(action)
                    
                    if hasattr(agent, 'learn'):
                        agent.learn(state, action, reward, next_state, done, context)
                    
                    state = next_state
                    total_reward += reward
                
                agent.episode_ended(total_reward)
                
                # Collect episode data
                episode_data = env.get_episode_data()
                episode_data.episode_id = episode
                episode_data.agent_type = agent_name
                episode_data_list.append(episode_data)
            
            all_results[agent_name] = episode_data_list
        
        # Compute comparative metrics
        comparison_df, summary_stats = self.metrics_calculator.compare_agents(all_results)
        
        # Save results
        results = {
            'comparison_data': comparison_df.to_dict(),
            'summary_statistics': summary_stats.to_dict() if hasattr(summary_stats, 'to_dict') else str(summary_stats),
            'agent_results': {name: len(episodes) for name, episodes in all_results.items()},
            'config': self.config
        }
        
        self._save_results(results, 'comparative_evaluation_results.json')
        comparison_df.to_csv(self.results_dir / 'agent_comparison.csv', index=False)
        
        logger.info("Comparative evaluation completed.")
        return results
    
    def _save_results(self, results: Dict[str, Any], filename: str):
        """Save results to JSON file."""
        filepath = self.results_dir / filename
        
        # Convert non-serializable objects for JSON
        def convert_for_json(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, EpisodeData):
                return obj.__dict__
            elif hasattr(obj, '__dict__'):
                return {k: convert_for_json(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_for_json(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            else:
                return obj
        
        converted_results = convert_for_json(results)
        
        with open(filepath, 'w') as f:
            json.dump(converted_results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filepath}")


def load_config(config_path: str) -> Dict[str, Any]:
    """Load experiment configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Using default configuration...")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Get default configuration if config file not found."""
    return {
        'environment': {
            'data_splits_path': 'data/DATA_SPLITS',
            'episode_length': 50,
            'disruption_types': ['pandemic', 'flood', 'cyber_attack'],
            'use_real_data': True
        },
        'agents': {
            'crl_agent': {
                'learning_rate': 1e-4,
                'causal_lambda': 0.3,
                'use_action_masking': True,
                'use_reward_shaping': True
            }
        },
        'experiment': {
            'num_episodes': 100,
            'results_dir': 'results/'
        }
    }


def launch_dashboard(config: Dict[str, Any]):
    """Launch real-time monitoring dashboard (placeholder)."""
    logger.info("Dashboard functionality not yet implemented.")
    logger.info("In full implementation, this would launch a Dash/Plotly dashboard")
    logger.info("showing real-time metrics, causal graphs, and agent performance.")
    
    print("\n" + "="*60)
    print("HEALTHCARE CRL FRAMEWORK - DASHBOARD MODE")
    print("="*60)
    print("🏥 Real-time Supply Chain Monitoring")
    print("📊 Resilience Metrics Dashboard") 
    print("🧠 Causal Analysis Visualization")
    print("🤖 Agent Performance Comparison")
    print("="*60)
    print("\nDashboard would be available at: http://localhost:8050")
    print("Press Ctrl+C to exit dashboard mode")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDashboard shutdown.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Healthcare Supply Chain CRL Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode train
  python main.py --config default_config.yaml --mode train  
  python main.py --mode evaluate
  python main.py --mode dashboard
        """
    )
    
    parser.add_argument('--config', type=str, default='configs/default_config.yaml',
                       help='Path to experiment configuration file')
    parser.add_argument('--mode', type=str, choices=['train', 'evaluate', 'dashboard'],
                       default='train', help='Execution mode')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--episodes', type=int, default=None,
                       help='Override number of episodes')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Print framework banner
    print("\n" + "="*60)
    print("HEALTHCARE SUPPLY CHAIN CRL FRAMEWORK")
    print("Causal-Reinforcement Learning for Resilience")
    print("="*60)
    print(f"Mode: {args.mode}")
    print(f"Config: {args.config}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # Load configuration
    config = load_config(args.config)
    
    # Override episodes if specified
    if args.episodes:
        config['experiment']['num_episodes'] = args.episodes
    
    try:
        # Execute based on mode
        if args.mode == 'train':
            runner = ExperimentRunner(config)
            results = runner.run_training_experiment()
            print(f"\n✓ Training completed successfully!")
            print(f"Results saved to: {runner.results_dir}")
            
        elif args.mode == 'evaluate':
            runner = ExperimentRunner(config)  
            results = runner.run_comparative_evaluation()
            print(f"\n✓ Evaluation completed successfully!")
            print(f"Results saved to: {runner.results_dir}")
            
        elif args.mode == 'dashboard':
            launch_dashboard(config)
            
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user.")
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()