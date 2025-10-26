"""
Baseline agents for comparison with CRL agent.
Implements deterministic, pure RL, and causal heuristic approaches.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Tuple, Any
import random
from collections import deque, namedtuple
import logging

from crl_agent import DQNetwork, ReplayBuffer

logger = logging.getLogger(__name__)


class DeterministicAgent:
    """
    Deterministic optimization agent using safety stock and fixed reorder rules.
    Represents traditional supply chain management approach.
    """
    
    def __init__(self, state_size: int, action_size: int):
        """Initialize deterministic agent."""
        self.state_size = state_size
        self.action_size = action_size
        
        # Fixed policy parameters
        self.safety_stock_threshold = 0.3
        self.stockout_threshold = 0.2
        self.cost_threshold = 0.7
        self.lead_time_threshold = 0.6
        
        # Action mapping same as CRL agent
        self.action_mapping = {
            0: 'switch_supplier',
            1: 'increase_safety_stock', 
            2: 'emergency_procurement',
            3: 'reroute_shipments',
            4: 'allocate_resources',
            5: 'no_action'
        }
        
        # Metrics tracking
        self.episode_rewards = []
        self.action_counts = {action: 0 for action in range(action_size)}
        
    def act(self, state: np.ndarray, context: Dict[str, Any] = None) -> int:
        """Select action using deterministic rules."""
        
        # Extract key state features (assuming structured state representation)
        inventory_level = state[0] if len(state) > 0 else 0.5
        stockout_risk = state[1] if len(state) > 1 else 0.5
        lead_time = state[2] if len(state) > 2 else 0.5
        supplier_reliability = state[3] if len(state) > 3 else 0.5
        cost_pressure = state[4] if len(state) > 4 else 0.5
        
        # Deterministic decision tree
        if stockout_risk > self.stockout_threshold:
            if inventory_level < self.safety_stock_threshold:
                action = 2  # emergency_procurement
            else:
                action = 4  # allocate_resources
        elif supplier_reliability < 0.4:
            action = 0  # switch_supplier
        elif lead_time > self.lead_time_threshold:
            action = 3  # reroute_shipments
        elif inventory_level < self.safety_stock_threshold and cost_pressure < self.cost_threshold:
            action = 1  # increase_safety_stock
        else:
            action = 5  # no_action
        
        self.action_counts[action] += 1
        return action
    
    def learn(self, state: np.ndarray, action: int, reward: float, 
              next_state: np.ndarray, done: bool, context: Dict[str, Any] = None) -> None:
        """Deterministic agent doesn't learn, but tracks rewards."""
        if done:
            # This would be called at end of episode if tracking episode rewards
            pass
    
    def episode_ended(self, total_reward: float) -> None:
        """Track episode completion."""
        self.episode_rewards.append(total_reward)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        return {
            'episode_rewards': self.episode_rewards.copy(),
            'action_distribution': self.action_counts.copy(),
            'avg_reward': np.mean(self.episode_rewards) if self.episode_rewards else 0.0
        }
    
    def save_model(self, filepath: str) -> None:
        """Save agent state (deterministic agents have no learnable parameters)."""
        import json
        with open(filepath, 'w') as f:
            json.dump({
                'type': 'deterministic',
                'metrics': self.get_metrics(),
                'parameters': {
                    'safety_stock_threshold': self.safety_stock_threshold,
                    'stockout_threshold': self.stockout_threshold,
                    'cost_threshold': self.cost_threshold,
                    'lead_time_threshold': self.lead_time_threshold
                }
            }, f, indent=2)
    
    def load_model(self, filepath: str) -> None:
        """Load agent state."""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
            if 'parameters' in data:
                params = data['parameters']
                self.safety_stock_threshold = params.get('safety_stock_threshold', self.safety_stock_threshold)
                self.stockout_threshold = params.get('stockout_threshold', self.stockout_threshold)
                self.cost_threshold = params.get('cost_threshold', self.cost_threshold)
                self.lead_time_threshold = params.get('lead_time_threshold', self.lead_time_threshold)


class PureRLAgent:
    """
    Pure reinforcement learning agent without causal inference.
    Standard DQN implementation for comparison.
    """
    
    def __init__(self, 
                 state_size: int,
                 action_size: int,
                 learning_rate: float = 1e-4,
                 gamma: float = 0.99,
                 epsilon_start: float = 1.0,
                 epsilon_end: float = 0.01,
                 epsilon_decay: float = 0.995,
                 buffer_size: int = 10000,
                 batch_size: int = 32,
                 target_update_freq: int = 100):
        """Initialize pure RL agent."""
        
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        
        # Neural networks
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.q_network = DQNetwork(state_size, action_size).to(self.device)
        self.target_network = DQNetwork(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Experience replay
        self.replay_buffer = ReplayBuffer(buffer_size)
        
        # Training metrics
        self.step_count = 0
        self.episode_count = 0
        self.training_metrics = {
            'losses': [],
            'rewards': [],
            'epsilon_values': []
        }
        
    def act(self, state: np.ndarray, context: Dict[str, Any] = None) -> int:
        """Select action using epsilon-greedy policy (no causal masking)."""
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        if random.random() > self.epsilon:
            # Greedy action
            with torch.no_grad():
                q_values = self.q_network(state_tensor)
                action = q_values.argmax().item()
        else:
            # Random action
            action = random.randint(0, self.action_size - 1)
        
        return action
    
    def learn(self, state: np.ndarray, action: int, reward: float, 
              next_state: np.ndarray, done: bool, context: Dict[str, Any] = None) -> None:
        """Learn from experience (no causal reward shaping)."""
        
        # Store experience (no causal effects)
        self.replay_buffer.push(state, action, reward, next_state, done, causal_effect=0.0)
        
        self.step_count += 1
        
        # Train if enough experiences
        if len(self.replay_buffer) >= self.batch_size and self.step_count % 4 == 0:
            self._train_step()
        
        # Update target network
        if self.step_count % self.target_update_freq == 0:
            self._update_target_network()
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        self.training_metrics['epsilon_values'].append(self.epsilon)
    
    def _train_step(self) -> None:
        """Perform training step (same as CRL agent but without causal components)."""
        
        batch = self.replay_buffer.sample(self.batch_size)
        
        states = torch.FloatTensor([e.state for e in batch]).to(self.device)
        actions = torch.LongTensor([e.action for e in batch]).to(self.device)
        rewards = torch.FloatTensor([e.reward for e in batch]).to(self.device)
        next_states = torch.FloatTensor([e.next_state for e in batch]).to(self.device)
        dones = torch.BoolTensor([e.done for e in batch]).to(self.device)
        
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=10.0)
        self.optimizer.step()
        
        self.training_metrics['losses'].append(loss.item())
    
    def _update_target_network(self) -> None:
        """Update target network."""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def episode_ended(self, total_reward: float) -> None:
        """Track episode completion."""
        self.episode_count += 1
        self.training_metrics['rewards'].append(total_reward)
    
    def get_metrics(self) -> Dict[str, List[float]]:
        """Get training metrics."""
        return self.training_metrics.copy()
    
    def save_model(self, filepath: str) -> None:
        """Save model."""
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'training_metrics': self.training_metrics,
            'episode_count': self.episode_count,
            'step_count': self.step_count,
            'epsilon': self.epsilon
        }, filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load model."""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_metrics = checkpoint['training_metrics']
        self.episode_count = checkpoint['episode_count']
        self.step_count = checkpoint['step_count']
        self.epsilon = checkpoint['epsilon']


class CausalHeuristicAgent:
    """
    Heuristic agent using causal knowledge without learning.
    Uses Bayesian Network expectations to guide decisions.
    """
    
    def __init__(self, state_size: int, action_size: int, causal_oracle=None):
        """Initialize causal heuristic agent."""
        
        self.state_size = state_size
        self.action_size = action_size
        self.causal_oracle = causal_oracle
        
        # Action mapping
        self.action_mapping = {
            0: 'switch_supplier',
            1: 'increase_safety_stock', 
            2: 'emergency_procurement',
            3: 'reroute_shipments',
            4: 'allocate_resources',
            5: 'no_action'
        }
        
        # Metrics
        self.episode_rewards = []
        self.causal_effects_used = []
        
    def act(self, state: np.ndarray, context: Dict[str, Any] = None) -> int:
        """Select action using causal heuristics."""
        
        if self.causal_oracle and context:
            # Evaluate causal effects of all feasible actions
            action_effects = {}
            
            for action_idx, action_name in self.action_mapping.items():
                if action_name == 'no_action':
                    action_effects[action_idx] = 0.0  # Baseline
                elif self.causal_oracle.is_feasible(action_name, context):
                    effect = self.causal_oracle.effect(action_name, context)
                    action_effects[action_idx] = effect
                else:
                    action_effects[action_idx] = -1.0  # Infeasible
            
            # Select action with highest positive causal effect
            if action_effects:
                best_action = max(action_effects.keys(), key=lambda k: action_effects[k])
                self.causal_effects_used.append(action_effects[best_action])
                return best_action
            else:
                return 5  # no_action fallback
        else:
            # Fallback to simple heuristic without causal oracle
            return self._simple_heuristic(state)
    
    def _simple_heuristic(self, state: np.ndarray) -> int:
        """Simple heuristic when no causal oracle available."""
        
        if len(state) >= 2:
            inventory_level = state[0]
            stockout_risk = state[1]
            
            if stockout_risk > 0.7:
                return 2  # emergency_procurement
            elif inventory_level < 0.3:
                return 1  # increase_safety_stock
            else:
                return 5  # no_action
        else:
            return 5  # no_action
    
    def learn(self, state: np.ndarray, action: int, reward: float, 
              next_state: np.ndarray, done: bool, context: Dict[str, Any] = None) -> None:
        """Heuristic agent doesn't learn from experience."""
        pass
    
    def episode_ended(self, total_reward: float) -> None:
        """Track episode completion."""
        self.episode_rewards.append(total_reward)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return {
            'episode_rewards': self.episode_rewards.copy(),
            'causal_effects_used': self.causal_effects_used.copy(),
            'avg_reward': np.mean(self.episode_rewards) if self.episode_rewards else 0.0,
            'avg_causal_effect': np.mean(self.causal_effects_used) if self.causal_effects_used else 0.0
        }
    
    def save_model(self, filepath: str) -> None:
        """Save agent metrics."""
        import json
        with open(filepath, 'w') as f:
            json.dump({
                'type': 'causal_heuristic',
                'metrics': self.get_metrics()
            }, f, indent=2)
    
    def load_model(self, filepath: str) -> None:
        """Load agent metrics."""
        import json
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if 'metrics' in data:
                    metrics = data['metrics']
                    self.episode_rewards = metrics.get('episode_rewards', [])
                    self.causal_effects_used = metrics.get('causal_effects_used', [])
        except FileNotFoundError:
            logger.warning(f"Model file not found: {filepath}")


class BaselineAgents:
    """Factory class for creating baseline agents."""
    
    @staticmethod
    def create_deterministic_agent(state_size: int, action_size: int) -> DeterministicAgent:
        """Create deterministic optimization agent."""
        return DeterministicAgent(state_size, action_size)
    
    @staticmethod
    def create_pure_rl_agent(state_size: int, action_size: int, **kwargs) -> PureRLAgent:
        """Create pure RL agent without causal inference."""
        return PureRLAgent(state_size, action_size, **kwargs)
    
    @staticmethod
    def create_causal_heuristic_agent(state_size: int, action_size: int, 
                                    causal_oracle=None) -> CausalHeuristicAgent:
        """Create causal heuristic agent."""
        return CausalHeuristicAgent(state_size, action_size, causal_oracle)
    
    @staticmethod
    def get_all_baselines(state_size: int, action_size: int, causal_oracle=None) -> Dict[str, Any]:
        """Create all baseline agents for comparison."""
        
        baselines = {
            'deterministic': BaselineAgents.create_deterministic_agent(state_size, action_size),
            'pure_rl': BaselineAgents.create_pure_rl_agent(state_size, action_size),
            'causal_heuristic': BaselineAgents.create_causal_heuristic_agent(state_size, action_size, causal_oracle)
        }
        
        logger.info(f"Created {len(baselines)} baseline agents for comparison")
        return baselines


if __name__ == "__main__":
    # Test baseline agents
    state_size = 10
    action_size = 6
    
    # Create all baselines
    baselines = BaselineAgents.get_all_baselines(state_size, action_size)
    
    # Test each agent
    test_state = np.random.randn(state_size)
    
    for name, agent in baselines.items():
        action = agent.act(test_state)
        print(f"{name} agent selected action: {action}")
        
        # Test learning interface
        agent.learn(test_state, action, 1.0, test_state, False)
        agent.episode_ended(10.0)
        
        print(f"{name} metrics: {agent.get_metrics()}")