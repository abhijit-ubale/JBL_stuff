"""
Causal Reinforcement Learning Agent for Healthcare Supply Chain.
Implements Deep Q-Network with causal action masking and reward shaping.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from collections import deque, namedtuple
import random
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Experience replay memory
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done', 'causal_effect'])


class DQNetwork(nn.Module):
    """Deep Q-Network for supply chain decision making."""
    
    def __init__(self, state_size: int, action_size: int, hidden_sizes: List[int] = [256, 128, 64]):
        """
        Initialize DQN.
        
        Args:
            state_size: Dimension of state space
            action_size: Number of possible actions
            hidden_sizes: List of hidden layer sizes
        """
        super(DQNetwork, self).__init__()
        
        # Build network layers
        layers = []
        input_size = state_size
        
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(input_size, hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            input_size = hidden_size
        
        # Output layer
        layers.append(nn.Linear(input_size, action_size))
        
        self.network = nn.Sequential(*layers)
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        """Initialize network weights."""
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
    
    def forward(self, state):
        """Forward pass through network."""
        return self.network(state)


class ReplayBuffer:
    """Experience replay buffer with causal effect storage."""
    
    def __init__(self, capacity: int = 10000):
        """Initialize replay buffer."""
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done, causal_effect=0.0):
        """Add experience to buffer."""
        experience = Experience(state, action, reward, next_state, done, causal_effect)
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[Experience]:
        """Sample batch of experiences."""
        return random.sample(self.buffer, batch_size)
    
    def __len__(self):
        """Get buffer size."""
        return len(self.buffer)


class CausalRLAgent:
    """
    Causal Reinforcement Learning Agent for Healthcare Supply Chain.
    Implements the CRL framework from the paper with action masking and reward shaping.
    """
    
    def __init__(self, 
                 state_size: int,
                 action_size: int,
                 causal_oracle=None,
                 learning_rate: float = 1e-4,
                 gamma: float = 0.99,
                 epsilon_start: float = 1.0,
                 epsilon_end: float = 0.01,
                 epsilon_decay: float = 0.995,
                 causal_lambda: float = 0.3,
                 use_action_masking: bool = True,
                 use_reward_shaping: bool = True,
                 buffer_size: int = 10000,
                 batch_size: int = 32,
                 target_update_freq: int = 100):
        """
        Initialize CRL Agent.
        
        Args:
            state_size: Dimension of state space
            action_size: Number of possible actions
            causal_oracle: Causal inference oracle for effect estimation
            learning_rate: Learning rate for neural network
            gamma: Discount factor for future rewards
            epsilon_start: Initial exploration rate
            epsilon_end: Final exploration rate
            epsilon_decay: Exploration decay rate
            causal_lambda: Weight for causal reward shaping
            use_action_masking: Whether to use causal action masking
            use_reward_shaping: Whether to use causal reward shaping
            buffer_size: Size of experience replay buffer
            batch_size: Batch size for training
            target_update_freq: Frequency of target network updates
        """
        
        self.state_size = state_size
        self.action_size = action_size
        self.causal_oracle = causal_oracle
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.causal_lambda = causal_lambda
        self.use_action_masking = use_action_masking
        self.use_reward_shaping = use_reward_shaping
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
            'causal_effects': [],
            'epsilon_values': []
        }
        
        # Action mapping
        self.action_mapping = {
            0: 'switch_supplier',
            1: 'increase_safety_stock', 
            2: 'emergency_procurement',
            3: 'reroute_shipments',
            4: 'allocate_resources',
            5: 'no_action'  # Do nothing action
        }
        
        logger.info(f"Initialized CRL Agent with causal_lambda={causal_lambda}, "
                   f"action_masking={use_action_masking}, reward_shaping={use_reward_shaping}")
    
    def act(self, state: np.ndarray, context: Dict[str, Any] = None, mask: np.ndarray = None) -> int:
        """
        Select action using epsilon-greedy policy with optional causal action masking.
        
        Args:
            state: Current environment state
            context: Contextual information for causal oracle
            mask: Pre-computed action mask (if None, will compute from causal oracle)
            
        Returns:
            Selected action index
        """
        
        # Convert state to tensor
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # Get action mask using causal oracle
        if self.use_action_masking and self.causal_oracle and mask is None:
            mask = self._get_causal_action_mask(context or {})
        elif mask is None:
            mask = np.ones(self.action_size)  # No masking
        
        # Epsilon-greedy action selection
        if random.random() > self.epsilon:
            # Greedy action with masking
            with torch.no_grad():
                q_values = self.q_network(state_tensor).cpu().numpy()[0]
                
                # Apply action mask (set invalid actions to -inf)
                masked_q_values = q_values.copy()
                masked_q_values[mask == 0] = -np.inf
                
                action = np.argmax(masked_q_values)
        else:
            # Random action from valid actions only
            valid_actions = np.where(mask == 1)[0]
            if len(valid_actions) > 0:
                action = np.random.choice(valid_actions)
            else:
                action = np.random.randint(0, self.action_size)  # Fallback
        
        return action
    
    def _get_causal_action_mask(self, context: Dict[str, Any]) -> np.ndarray:
        """Get action mask based on causal feasibility constraints."""
        mask = np.zeros(self.action_size)
        
        if self.causal_oracle:
            # Check feasibility of each action
            for i, action_name in self.action_mapping.items():
                if action_name == 'no_action':
                    mask[i] = 1  # No-action is always feasible
                else:
                    mask[i] = 1 if self.causal_oracle.is_feasible(action_name, context) else 0
        else:
            # No causal oracle - all actions feasible
            mask.fill(1)
        
        # Ensure at least one action is feasible
        if mask.sum() == 0:
            mask[-1] = 1  # Enable no-action as fallback
        
        return mask
    
    def learn(self, state: np.ndarray, action: int, reward: float, 
              next_state: np.ndarray, done: bool, context: Dict[str, Any] = None) -> None:
        """
        Learn from experience with causal reward shaping.
        
        Args:
            state: Current state
            action: Action taken
            reward: Environment reward
            next_state: Next state
            done: Episode termination flag
            context: Contextual information for causal oracle
        """
        
        # Calculate causal effect for reward shaping
        causal_effect = 0.0
        if self.use_reward_shaping and self.causal_oracle and context:
            action_name = self.action_mapping.get(action, 'no_action')
            if action_name != 'no_action':
                causal_effect = self.causal_oracle.effect(action_name, context)
        
        # Causal reward shaping
        shaped_reward = reward + self.causal_lambda * causal_effect
        
        # Store experience
        self.replay_buffer.push(state, action, shaped_reward, next_state, done, causal_effect)
        
        # Update step count
        self.step_count += 1
        
        # Train if enough experiences and at regular intervals
        if len(self.replay_buffer) >= self.batch_size and self.step_count % 4 == 0:
            self._train_step()
        
        # Update target network
        if self.step_count % self.target_update_freq == 0:
            self._update_target_network()
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        # Store metrics
        self.training_metrics['causal_effects'].append(causal_effect)
        self.training_metrics['epsilon_values'].append(self.epsilon)
    
    def _train_step(self) -> None:
        """Perform one training step on sampled batch."""
        
        # Sample batch of experiences
        batch = self.replay_buffer.sample(self.batch_size)
        
        # Convert to tensors
        states = torch.FloatTensor([e.state for e in batch]).to(self.device)
        actions = torch.LongTensor([e.action for e in batch]).to(self.device)
        rewards = torch.FloatTensor([e.reward for e in batch]).to(self.device)
        next_states = torch.FloatTensor([e.next_state for e in batch]).to(self.device)
        dones = torch.BoolTensor([e.done for e in batch]).to(self.device)
        
        # Current Q values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values from target network
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        # Compute loss
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=10.0)
        
        self.optimizer.step()
        
        # Store training metrics
        self.training_metrics['losses'].append(loss.item())
    
    def _update_target_network(self) -> None:
        """Update target network with current network weights."""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def episode_ended(self, total_reward: float) -> None:
        """Called when episode ends to update metrics."""
        self.episode_count += 1
        self.training_metrics['rewards'].append(total_reward)
        
        if self.episode_count % 100 == 0:
            avg_reward = np.mean(self.training_metrics['rewards'][-100:])
            avg_loss = np.mean(self.training_metrics['losses'][-100:]) if self.training_metrics['losses'] else 0
            logger.info(f"Episode {self.episode_count}: avg_reward={avg_reward:.2f}, "
                       f"avg_loss={avg_loss:.4f}, epsilon={self.epsilon:.3f}")
    
    def save_model(self, filepath: str) -> None:
        """Save model weights and training state."""
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'training_metrics': self.training_metrics,
            'episode_count': self.episode_count,
            'step_count': self.step_count,
            'epsilon': self.epsilon
        }, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """Load model weights and training state."""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_metrics = checkpoint['training_metrics']
        self.episode_count = checkpoint['episode_count']
        self.step_count = checkpoint['step_count']
        self.epsilon = checkpoint['epsilon']
        
        logger.info(f"Model loaded from {filepath}")
    
    def get_metrics(self) -> Dict[str, List[float]]:
        """Get training metrics."""
        return self.training_metrics.copy()
    
    def get_action_explanation(self, action: int, context: Dict[str, Any] = None) -> str:
        """Get explanation for chosen action using causal oracle."""
        action_name = self.action_mapping.get(action, 'unknown')
        
        if self.causal_oracle and action_name != 'no_action' and context:
            causal_effect = self.causal_oracle.effect(action_name, context)
            explanation = self.causal_oracle.get_causal_explanation(action_name, 'recovery_time')
            return f"Action: {action_name} | Causal Effect: {causal_effect:.3f} | {explanation}"
        else:
            return f"Action: {action_name}"


class MultiAgentCRL:
    """
    Multi-agent system with multiple CRL agents for different supply chain roles.
    """
    
    def __init__(self, observation_space, action_space, causal_oracle=None, num_agents: int = 4):
        """Initialize multi-agent CRL system."""
        
        self.num_agents = num_agents
        self.agents = {}
        self.agent_roles = ['hospital', 'supplier', 'distributor', 'logistics']
        
        # Create specialized agents for each role
        for i, role in enumerate(self.agent_roles[:num_agents]):
            self.agents[role] = CausalRLAgent(
                state_size=observation_space.shape[0] if hasattr(observation_space, 'shape') else observation_space,
                action_size=action_space.n if hasattr(action_space, 'n') else action_space,
                causal_oracle=causal_oracle,
                causal_lambda=0.2 + i * 0.1,  # Different causal weights for different agents
                learning_rate=1e-4,
                use_action_masking=True,
                use_reward_shaping=True
            )
        
        logger.info(f"Initialized multi-agent CRL system with {len(self.agents)} agents")
    
    def act(self, observations: Dict[str, np.ndarray], contexts: Dict[str, Dict] = None) -> Dict[str, int]:
        """Get actions from all agents."""
        actions = {}
        
        for role, agent in self.agents.items():
            obs = observations.get(role, observations.get('shared', np.zeros(agent.state_size)))
            context = contexts.get(role, {}) if contexts else {}
            actions[role] = agent.act(obs, context)
        
        return actions
    
    def learn(self, experiences: Dict[str, Tuple]) -> None:
        """Update all agents from their experiences."""
        for role, agent in self.agents.items():
            if role in experiences:
                state, action, reward, next_state, done, context = experiences[role]
                agent.learn(state, action, reward, next_state, done, context)
    
    def save_models(self, directory: str) -> None:
        """Save all agent models."""
        from pathlib import Path
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        for role, agent in self.agents.items():
            agent.save_model(f"{directory}/{role}_agent.pt")
    
    def load_models(self, directory: str) -> None:
        """Load all agent models."""
        for role, agent in self.agents.items():
            try:
                agent.load_model(f"{directory}/{role}_agent.pt")
            except FileNotFoundError:
                logger.warning(f"Model file not found for {role} agent")


if __name__ == "__main__":
    # Test CRL agent creation
    agent = CausalRLAgent(
        state_size=20,
        action_size=6,
        causal_oracle=None,
        use_action_masking=False,
        use_reward_shaping=False
    )
    
    # Test action selection
    test_state = np.random.randn(20)
    action = agent.act(test_state)
    print(f"Selected action: {action}")
    
    # Test learning
    next_state = np.random.randn(20)
    agent.learn(test_state, action, 1.0, next_state, False)
    print("Learning step completed")