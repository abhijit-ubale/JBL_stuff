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
from pathlib import Path
import yaml
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    # Import framework components
    from data_pipeline import HealthcareDataPipeline
    from causal_graph import create_healthcare_causal_model, CausalOracle
    from crl_agent import CausalRLAgent, MultiAgentCRL
    from baselines import BaselineAgents
    from metrics import ResilienceMetrics, EpisodeData
except ImportError as e:
    print(f"Import Error: {e}")
    print("Make sure all framework components are properly installed.")
    print("Run: python setup.py")
    sys.exit(1)

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
    Simplified healthcare supply chain environment for CRL experiments.
    This is a mock environment - in full implementation, this would be
    a complete gymnasium environment.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize environment from configuration."""
        self.config = config
        self.num_hospitals = config.get('num_hospitals', 50)
        self.num_suppliers = config.get('num_suppliers', 25)
        self.episode_length = config.get('episode_length', 50)
        self.disruption_types = config.get('disruption_types', ['pandemic'])
        
        # State and action space dimensions
        self.state_size = 20  # Multi-dimensional state representation
        self.action_size = 6  # 5 actions + no-action
        
        # Environment state
        self.current_step = 0
        self.current_state = None
        self.disruption_active = False
        self.disruption_severity = 0.0
        
        # Performance tracking
        self.episode_data = None
        
        logger.info(f"Initialized environment with {self.num_hospitals} hospitals, "
                   f"{self.num_suppliers} suppliers")
    
    def reset(self) -> np.ndarray:
        """Reset environment for new episode."""
        self.current_step = 0
        self.disruption_active = False
        self.disruption_severity = 0.0
        
        # Initialize state [service_level, inventory_level, lead_time, supplier_reliability, ...]
        self.current_state = np.array([
            0.95,  # service_level
            0.8,   # inventory_level  
            0.3,   # lead_time
            0.9,   # supplier_reliability
            0.2,   # cost_pressure
            0.0,   # pandemic_severity
            0.0,   # hurricane_severity
            0.0,   # cyber_attack_severity
            0.0,   # port_closure_severity
            0.0,   # compound_disruption
            0.8,   # transportation_capacity
            0.1,   # stockout_risk
            0.1,   # demand_surge
            0.2,   # cost_increase
            0.95,  # quality_compliance
            12.0,  # inventory_turnover (normalized)
            0.0,   # service_disruption
            0.0,   # recovery_progress
            0.8,   # digital_responsiveness
            0.6    # sustainability_score
        ])
        
        # Initialize episode data collection
        self.episode_data = {
            'states': [self.current_state.copy()],
            'actions': [],
            'rewards': [],
            'costs': [100.0],  # baseline cost
            'service_levels': [0.95],
            'inventory_levels': [0.8],
            'supplier_performances': [{
                'on_time_delivery': 0.9,
                'quality_compliance': 0.95,
                'response_time_score': 0.8
            }],
            'disruption_events': []
        }
        
        return self.current_state.copy()
    
    def step(self, action: int) -> tuple:
        """Execute action and return next state, reward, done, info."""
        self.current_step += 1
        
        # Simulate disruption events (random timing)
        if not self.disruption_active and np.random.rand() < 0.1:  # 10% chance per step
            self._trigger_disruption()
        
        # Apply action effects
        next_state, reward, cost = self._apply_action(action)
        
        # Update state
        self.current_state = next_state
        
        # Check if episode is done
        done = self.current_step >= self.episode_length
        
        # Create context for causal oracle
        context = self._get_context()
        
        # Store step data
        self.episode_data['states'].append(next_state.copy())
        self.episode_data['actions'].append({
            'action_type': self._action_to_name(action),
            'timestamp': self.current_step
        })
        self.episode_data['rewards'].append(reward)
        self.episode_data['costs'].append(cost)
        self.episode_data['service_levels'].append(next_state[0])
        self.episode_data['inventory_levels'].append(next_state[1])
        
        info = {
            'context': context,
            'disruption_active': self.disruption_active,
            'step': self.current_step
        }
        
        return next_state.copy(), reward, done, info
    
    def _trigger_disruption(self):
        """Trigger a random disruption event."""
        disruption_type = np.random.choice(self.disruption_types)
        self.disruption_severity = np.random.uniform(0.3, 0.9)
        self.disruption_active = True
        
        # Update state based on disruption type
        if disruption_type == 'pandemic':
            self.current_state[5] = self.disruption_severity  # pandemic_severity
            self.current_state[12] = min(1.0, self.disruption_severity * 0.8)  # demand_surge
            self.current_state[3] *= (1 - self.disruption_severity * 0.3)  # supplier_reliability
        elif disruption_type == 'hurricane':
            self.current_state[6] = self.disruption_severity  # hurricane_severity
            self.current_state[10] *= (1 - self.disruption_severity * 0.4)  # transportation_capacity
        elif disruption_type == 'cyber_attack':
            self.current_state[7] = self.disruption_severity  # cyber_attack_severity
            self.current_state[2] *= (1 + self.disruption_severity * 0.5)  # lead_time
        
        self.episode_data['disruption_events'].append({
            'type': disruption_type,
            'severity': self.disruption_severity,
            'step': self.current_step
        })
        
        logger.info(f"Triggered {disruption_type} disruption at step {self.current_step} "
                   f"with severity {self.disruption_severity:.2f}")
    
    def _apply_action(self, action: int) -> tuple:
        """Apply action and compute next state and reward."""
        next_state = self.current_state.copy()
        base_reward = 1.0
        base_cost = 100.0
        
        # Action effects on state
        if action == 0:  # switch_supplier
            next_state[3] = min(1.0, next_state[3] + 0.1)  # improve supplier_reliability
            base_cost *= 1.2  # increased cost
            
        elif action == 1:  # increase_safety_stock
            next_state[1] = min(1.0, next_state[1] + 0.15)  # increase inventory_level
            next_state[11] = max(0.0, next_state[11] - 0.1)  # reduce stockout_risk
            base_cost *= 1.3  # inventory holding cost
            
        elif action == 2:  # emergency_procurement
            next_state[1] = min(1.0, next_state[1] + 0.2)  # increase inventory_level
            next_state[11] = max(0.0, next_state[11] - 0.15)  # reduce stockout_risk
            base_cost *= 1.5  # premium procurement cost
            
        elif action == 3:  # reroute_shipments
            next_state[2] = max(0.1, next_state[2] - 0.1)  # reduce lead_time
            base_cost *= 1.1  # routing cost
            
        elif action == 4:  # allocate_resources
            next_state[0] = min(1.0, next_state[0] + 0.05)  # improve service_level
            next_state[16] = max(0.0, next_state[16] - 0.1)  # reduce service_disruption
            
        # No action (action == 5) has no direct effects
        
        # Natural state evolution and disruption effects
        if self.disruption_active:
            # Degradation during disruption
            next_state[0] *= 0.98  # service_level degradation
            next_state[1] *= 0.95  # inventory depletion
            next_state[11] = min(1.0, next_state[11] + 0.05)  # increasing stockout_risk
            
            # Recovery progress
            if np.random.rand() < 0.3:  # 30% chance to start recovery
                self.disruption_active = False
                next_state[17] = min(1.0, next_state[17] + 0.2)  # recovery_progress
        
        # Compute reward based on performance
        service_reward = next_state[0] - 0.95  # penalty for service below baseline
        cost_penalty = -abs(base_cost - 100.0) / 100.0  # cost increase penalty
        stockout_penalty = -next_state[11] * 2.0  # stockout risk penalty
        
        reward = base_reward + service_reward + cost_penalty + stockout_penalty
        
        return next_state, reward, base_cost
    
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
        """Get context dictionary for causal oracle."""
        return {
            'pandemic_severity': self.current_state[5],
            'hurricane_severity': self.current_state[6],
            'cyber_attack_severity': self.current_state[7],
            'supplier_reliability': self.current_state[3],
            'inventory_level': self.current_state[1],
            'service_level': self.current_state[0],
            'stockout_risk': self.current_state[11],
            'lead_time': self.current_state[2],
            'transportation_capacity': self.current_state[10]
        }
    
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
            'num_hospitals': 20,
            'num_suppliers': 10,
            'num_distributors': 5,
            'episode_length': 50,
            'disruption_types': ['pandemic']
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
        import time
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
    
    parser.add_argument('--config', type=str, default='default_config.yaml',
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