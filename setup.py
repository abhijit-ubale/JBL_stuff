"""
Healthcare Supply Chain CRL Framework Setup Script
Installation, validation, and environment setup utility.

This script handles:
- Dependency installation and verification
- Directory structure creation
- Framework component validation  
- Sample data generation
- Configuration file setup
- System health checks

Usage:
    python setup.py                    # Full setup
    python setup.py --validate-only    # Validation only
    python setup.py --install-deps     # Dependencies only
    python setup.py --create-sample    # Sample data only
"""

import os
import sys
import subprocess
import pkg_resources
import shutil
from pathlib import Path
import json
import yaml
import logging
from typing import Dict, List, Optional, Tuple
import importlib.util
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SetupManager:
    """Manages framework installation and validation."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize setup manager."""
        self.project_root = project_root or Path(__file__).parent
        self.requirements_file = self.project_root / 'requirements.txt'
        
        # Expected directory structure
        self.directories = [
            'src',
            'src/healthcare_crl',
            'src/healthcare_crl/agents',
            'src/healthcare_crl/baselines',
            'src/healthcare_crl/data', 
            'src/healthcare_crl/models',
            'src/healthcare_crl/utils',
            'configs',
            'data',
            'data/DATA_SPLITS',
            'data/TRADITIONAL_RULES',
            'docs',
            'results',
            'results/models',
            'results/figures',
            'results/logs',
            'scripts',
            'tests'
        ]
        
        # Expected Python modules
        self.required_modules = [
            'src/healthcare_crl/data/pipeline.py',
            'src/healthcare_crl/models/causal_graph.py',
            'src/healthcare_crl/agents/crl_agent.py',
            'src/healthcare_crl/baselines/baselines.py',
            'src/healthcare_crl/utils/metrics.py'
        ]
        
        logger.info(f"Setup manager initialized for project: {self.project_root}")
    
    def run_full_setup(self) -> bool:
        """Run complete setup process."""
        logger.info("Starting full framework setup...")
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating directory structure", self.create_directories),
            ("Installing dependencies", self.install_dependencies),
            ("Validating framework components", self.validate_components),
            ("Creating configuration files", self.create_config_files),
            ("Generating sample data", self.generate_sample_data),
            ("Running system health check", self.health_check)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            try:
                success = step_func()
                if not success:
                    logger.error(f"Setup failed at step: {step_name}")
                    return False
                logger.info(f"✓ {step_name} completed")
            except Exception as e:
                logger.error(f"✗ {step_name} failed: {e}")
                return False
        
        logger.info("✓ Full setup completed successfully!")
        self.print_setup_summary()
        return True
    
    def check_python_version(self) -> bool:
        """Check if Python version meets requirements."""
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            logger.error(f"Python 3.8+ required. Current version: {version.major}.{version.minor}.{version.micro}")
            return False
        
        logger.info(f"✓ Python version {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    
    def create_directories(self) -> bool:
        """Create required directory structure."""
        created = []
        
        for directory in self.directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created.append(str(dir_path))
        
        if created:
            logger.info(f"Created directories: {', '.join(created)}")
        else:
            logger.info("All required directories already exist")
        
        return True
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies from requirements.txt."""
        if not self.requirements_file.exists():
            logger.warning("requirements.txt not found. Creating it...")
            self.create_requirements_file()
        
        # Read requirements
        with open(self.requirements_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        logger.info(f"Installing {len(requirements)} packages...")
        
        # Check which packages are missing
        missing_packages = []
        for req in requirements:
            package_name = req.split('>=')[0].split('==')[0].split('[')[0]
            try:
                pkg_resources.get_distribution(package_name)
                logger.debug(f"✓ {package_name} already installed")
            except pkg_resources.DistributionNotFound:
                missing_packages.append(req)
        
        if not missing_packages:
            logger.info("All required packages already installed")
            return True
        
        # Install missing packages
        logger.info(f"Installing {len(missing_packages)} missing packages...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--upgrade'
            ] + missing_packages)
            logger.info("✓ Package installation completed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Package installation failed: {e}")
            return False
    
    def validate_components(self) -> bool:
        """Validate that all framework components are present and importable."""
        logger.info("Validating framework components...")
        
        # Check file existence
        missing_files = []
        for module_path in self.required_modules:
            file_path = self.project_root / module_path
            if not file_path.exists():
                missing_files.append(str(file_path))
        
        if missing_files:
            logger.error(f"Missing required files: {missing_files}")
            return False
        
        # Add src to path for import testing
        src_path = str(self.project_root / 'src')
        if src_path not in sys.path:
        
        # Test imports using new structure
        import_tests = [
            ('healthcare_crl.data.pipeline', ['RealDataPipeline']),
            ('healthcare_crl.models.causal_graph', ['create_healthcare_causal_model', 'CausalOracle']),
            ('healthcare_crl.agents.crl_agent', ['CausalRLAgent']),
            ('healthcare_crl.baselines.baselines', ['BaselineAgents']),
            ('healthcare_crl.utils.metrics', ['PerformanceMetrics'])
        ]
        
        for module_name, expected_classes in import_tests:
            try:
                module = importlib.import_module(module_name)
                for class_name in expected_classes:
                    if not hasattr(module, class_name):
                        logger.error(f"Class {class_name} not found in {module_name}")
                        return False
                logger.debug(f"✓ {module_name} imports successfully")
            except ImportError as e:
                logger.error(f"Failed to import {module_name}: {e}")
                return False
        
        logger.info("✓ All framework components validated")
        return True
    
    def create_config_files(self) -> bool:
        """Create default configuration files."""
        config_dir = self.project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # Default experiment configuration
        default_config = {
            'environment': {
                'num_hospitals': 20,
                'num_suppliers': 10,
                'num_distributors': 5,
                'episode_length': 50,
                'disruption_types': ['pandemic', 'hurricane', 'cyber_attack'],
                'geographic_scope': 'US',
                'data_source': 'synthetic'
            },
            'agents': {
                'crl_agent': {
                    'learning_rate': 1e-4,
                    'batch_size': 32,
                    'memory_size': 10000,
                    'causal_lambda': 0.3,
                    'use_action_masking': True,
                    'use_reward_shaping': True,
                    'exploration_strategy': 'epsilon_greedy',
                    'epsilon_start': 1.0,
                    'epsilon_end': 0.01,
                    'epsilon_decay': 0.995
                }
            },
            'experiment': {
                'num_episodes': 1000,
                'evaluation_frequency': 100,
                'save_frequency': 500,
                'results_dir': 'results/',
                'random_seed': 42
            },
            'causal_model': {
                'graph_type': 'bayesian_network',
                'learning_method': 'constraint_based',
                'significance_level': 0.05,
                'enable_oracle': True
            },
            'data_generation': {
                'hospital_count': 5000,
                'supplier_count': 500,
                'distributor_count': 200,
                'historical_years': 5,
                'disruption_frequency': 0.15,
                'seasonality_effects': True
            }
        }
        
        # Save default config
        config_path = config_dir / 'default_config.yaml'
        if not config_path.exists():
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            logger.info(f"Created default configuration: {config_path}")
        
        # Quick test config (smaller scale)
        quick_config = default_config.copy()
        quick_config['environment']['num_hospitals'] = 5
        quick_config['environment']['num_suppliers'] = 3
        quick_config['experiment']['num_episodes'] = 50
        
        quick_path = config_dir / 'quick_test_config.yaml'
        if not quick_path.exists():
            with open(quick_path, 'w') as f:
                yaml.dump(quick_config, f, default_flow_style=False, indent=2)
            logger.info(f"Created quick test configuration: {quick_path}")
        
        return True
    
    def generate_sample_data(self) -> bool:
        """Generate sample synthetic data for testing."""
        try:
            # Add src to path for imports
            src_path = str(self.project_root / 'src')
            if src_path not in sys.path:
            
            from src.healthcare_crl.data.pipeline import RealDataPipeline
            
            # Create data pipeline
            pipeline = RealDataPipeline('data/DATA_SPLITS')
            
            # Generate small sample dataset
            logger.info("Generating sample healthcare supply chain data...")
            
            # Use actual data loading instead of generation
            logger.info("Data pipeline initialized successfully")
            return True
            
            # Save sample data
            data_dir = self.project_root / 'data' / 'synthetic'
            for entity_type, data in sample_data.items():
                file_path = data_dir / f'sample_{entity_type}.json'
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                logger.info(f"Saved {len(data)} {entity_type} to {file_path}")
            
            logger.info("✓ Sample data generation completed")
            return True
            
        except Exception as e:
            logger.error(f"Sample data generation failed: {e}")
            return False
    
    def health_check(self) -> bool:
        """Run comprehensive system health check."""
        logger.info("Running system health check...")
        
        checks = [
            ("Directory structure", self._check_directories),
            ("Python modules", self._check_modules),
            ("Required packages", self._check_packages),
            ("Configuration files", self._check_configs),
            ("Sample data", self._check_sample_data)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                if result:
                    logger.info(f"  ✓ {check_name}")
                else:
                    logger.warning(f"  ✗ {check_name}")
                    all_passed = False
            except Exception as e:
                logger.error(f"  ✗ {check_name}: {e}")
                all_passed = False
        
        if all_passed:
            logger.info("✓ All health checks passed")
        else:
            logger.warning("Some health checks failed")
        
        return all_passed
    
    def _check_directories(self) -> bool:
        """Check if all required directories exist."""
        return all((self.project_root / d).exists() for d in self.directories)
    
    def _check_modules(self) -> bool:
        """Check if all required modules exist."""
        return all((self.project_root / m).exists() for m in self.required_modules)
    
    def _check_packages(self) -> bool:
        """Check if required packages are installed."""
        if not self.requirements_file.exists():
            return False
        
        with open(self.requirements_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        for req in requirements:
            package_name = req.split('>=')[0].split('==')[0].split('[')[0]
            try:
                pkg_resources.get_distribution(package_name)
            except pkg_resources.DistributionNotFound:
                return False
        
        return True
    
    def _check_configs(self) -> bool:
        """Check if configuration files exist."""
        config_dir = self.project_root / 'config'
        return (config_dir / 'default_config.yaml').exists()
    
    def _check_sample_data(self) -> bool:
        """Check if sample data exists."""
        data_dir = self.project_root / 'data' / 'synthetic'
        required_files = ['sample_hospitals.json', 'sample_suppliers.json', 'sample_distributors.json']
        return all((data_dir / f).exists() for f in required_files)
    
    def create_requirements_file(self):
        """Create requirements.txt file with all necessary dependencies."""
        requirements = [
            "# Core ML/RL Framework",
            "torch>=2.0.0",
            "gymnasium>=0.29.0", 
            "stable-baselines3>=2.0.0",
            "tensorboard>=2.13.0",
            "",
            "# Causal Inference",
            "pgmpy>=0.1.23",
            "dowhy>=0.11",
            "causalnex>=0.12.0",
            "econml>=0.14.0",
            "",
            "# Data Processing",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "scipy>=1.10.0",
            "scikit-learn>=1.3.0",
            "",
            "# Visualization",
            "matplotlib>=3.6.0",
            "plotly>=5.15.0",
            "dash>=2.14.0",
            "seaborn>=0.12.0",
            "networkx>=3.1.0",
            "",
            "# Explainability", 
            "shap>=0.42.0",
            "lime>=0.2.0",
            "",
            "# Utilities",
            "pyyaml>=6.0",
            "tqdm>=4.65.0",
            "python-dotenv>=1.0.0",
            "jsonschema>=4.17.0",
            "",
            "# Development & Testing",
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0"
        ]
        
        with open(self.requirements_file, 'w') as f:
            f.write('\n'.join(requirements))
        
        logger.info(f"Created requirements.txt with {len([r for r in requirements if r and not r.startswith('#')])} packages")
    
    def print_setup_summary(self):
        """Print setup completion summary."""
        print("\n" + "="*70)
        print("🏥 HEALTHCARE CRL FRAMEWORK SETUP COMPLETE 🏥")
        print("="*70)
        print("Framework Components:")
        print("  ✓ Causal-Reinforcement Learning Agents")
        print("  ✓ Healthcare Supply Chain Simulation")
        print("  ✓ Bayesian Causal Graph Models")
        print("  ✓ Multi-Agent Environment")
        print("  ✓ Resilience Metrics Calculator")
        print("  ✓ Baseline Agent Comparison")
        print("")
        print("Quick Start Commands:")
        print("  python main.py --mode train          # Train CRL agent")
        print("  python main.py --mode evaluate       # Compare all agents")
        print("  python main.py --mode dashboard      # Launch monitoring")
        print("")
        print("Configuration Files:")
        print(f"  {self.project_root}/config/default_config.yaml")
        print(f"  {self.project_root}/config/quick_test_config.yaml")
        print("")
        print("Data Locations:")
        print(f"  {self.project_root}/data/synthetic/")
        print(f"  {self.project_root}/results/")
        print("")
        print("Next Steps:")
        print("  1. Review configuration in config/default_config.yaml")
        print("  2. Run: python main.py --config config/quick_test_config.yaml")
        print("  3. Check results in results/ directory")
        print("="*70)


def main():
    """Main setup script entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Healthcare CRL Framework Setup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                     # Full setup
  python setup.py --validate-only     # Validation only
  python setup.py --install-deps      # Install dependencies only  
  python setup.py --create-sample     # Generate sample data only
  python setup.py --health-check      # System health check
        """
    )
    
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate existing setup')
    parser.add_argument('--install-deps', action='store_true', 
                       help='Only install dependencies')
    parser.add_argument('--create-sample', action='store_true',
                       help='Only generate sample data')
    parser.add_argument('--health-check', action='store_true',
                       help='Only run health check')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize setup manager
    setup_manager = SetupManager()
    
    try:
        # Execute based on arguments
        if args.validate_only:
            success = setup_manager.validate_components()
        elif args.install_deps:
            success = setup_manager.install_dependencies()
        elif args.create_sample:
            success = setup_manager.generate_sample_data()
        elif args.health_check:
            success = setup_manager.health_check()
        else:
            # Full setup
            success = setup_manager.run_full_setup()
        
        if success:
            print("\n✓ Setup completed successfully!")
            sys.exit(0)
        else:
            print("\n✗ Setup failed. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()