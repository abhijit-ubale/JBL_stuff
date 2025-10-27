# Healthcare CRL Framework - New Package Structure

## 📁 Project Structure

The Healthcare CRL Framework has been reorganized following Python PEP8 best practices:

```
healthcare_crl/
├── src/
│   └── healthcare_crl/           # Main package
│       ├── __init__.py
│       ├── cli.py               # Command line interface
│       ├── agents/              # RL/CRL agents
│       │   ├── __init__.py
│       │   └── crl_agent.py     # Causal RL agent implementations
│       ├── baselines/           # Baseline models
│       │   ├── __init__.py
│       │   └── baselines.py     # Traditional baseline agents
│       ├── data/                # Data processing
│       │   ├── __init__.py
│       │   └── pipeline.py      # Real data pipeline
│       ├── models/              # ML models
│       │   ├── __init__.py
│       │   └── causal_graph.py  # Causal graph models
│       └── utils/               # Utilities
│           ├── __init__.py
│           └── metrics.py       # Performance metrics
├── tests/                       # Test files
│   ├── __init__.py
│   ├── test_simple_run.py
│   ├── test_real_data_integration.py
│   └── ...
├── configs/                     # Configuration files
├── data/                        # Data files
│   ├── DATA_SPLITS/            # Dataset splits
│   ├── TRADITIONAL_RULES/      # Traditional baseline rules
│   └── TRAD_RULES/            # Additional rules
├── docs/                        # Documentation
│   ├── check_links.md
│   └── copilot-instructions.md
├── scripts/                     # Utility scripts
│   ├── get_real_metrics.py
│   ├── final_validation.py
│   ├── run_comprehensive_comparison.py
│   └── verify_stats.py
├── results/                     # Output results
├── main.py                      # Main entry point
├── setup.py                     # Legacy setup script
├── pyproject.toml              # Modern Python packaging
├── requirements.txt            # Dependencies
├── README.md                   # Project documentation
└── LICENSE.md                  # License
```

## 🔧 Package Installation

Install in development mode:
```bash
pip install -e .
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

## 📦 Import Usage

### New Import Structure

```python
# Main package components
from healthcare_crl import (
    CausalRLAgent, 
    MultiAgentCRL, 
    BaselineAgents,
    RealDataPipeline,
    create_healthcare_causal_model,
    CausalOracle,
    ResilienceMetrics,
    EpisodeData
)

# Specific module imports
from healthcare_crl.agents.crl_agent import CausalRLAgent
from healthcare_crl.data.pipeline import RealDataPipeline
from healthcare_crl.models.causal_graph import create_healthcare_causal_model
from healthcare_crl.baselines.baselines import BaselineAgents
from healthcare_crl.utils.metrics import ResilienceMetrics
```

### Old vs New Imports

| **Old Import** | **New Import** |
|----------------|----------------|
| `from data_pipeline import RealDataPipeline` | `from healthcare_crl.data.pipeline import RealDataPipeline` |
| `from crl_agent import CausalRLAgent` | `from healthcare_crl.agents.crl_agent import CausalRLAgent` |
| `from baselines import BaselineAgents` | `from healthcare_crl.baselines.baselines import BaselineAgents` |
| `from causal_graph import CausalOracle` | `from healthcare_crl.models.causal_graph import CausalOracle` |
| `from metrics import ResilienceMetrics` | `from healthcare_crl.utils.metrics import ResilienceMetrics` |

## 🚀 Usage Examples

### Quick Start
```bash
# Train CRL agent
python main.py --mode train

# Evaluate all models
python main.py --mode evaluate

# Launch dashboard
python main.py --mode dashboard

# Use custom config
python main.py --config configs/default_config.yaml --mode train
```

### Development Workflow
```bash
# Install in dev mode
pip install -e .

# Run tests
pytest tests/

# Format code
black src/

# Type checking
mypy src/

# Run validation
python test_package_structure.py
```

## 🔍 Benefits of New Structure

### 1. **PEP8 Compliance**
- Follows Python packaging best practices
- Clear separation of concerns
- Proper module organization

### 2. **Maintainability**
- Logical file organization
- Easy to navigate and understand
- Scalable architecture

### 3. **Reusability**
- Modular design
- Clean import structure
- Pluggable components

### 4. **Development Experience**
- Better IDE support
- Improved auto-completion
- Clear dependency management

### 5. **Deployment Ready**
- Modern `pyproject.toml` configuration
- Proper package metadata
- Distribution ready

## 📋 Migration Checklist

✅ **Completed Tasks:**
- [x] Created proper package structure (`src/healthcare_crl/`)
- [x] Organized modules into logical subdirectories
- [x] Added comprehensive `__init__.py` files
- [x] Updated all import statements
- [x] Created modern `pyproject.toml`
- [x] Updated configuration paths
- [x] Fixed relative imports
- [x] Validated package structure
- [x] Tested main functionality

## 🧪 Testing

Run the package structure validation:
```bash
python test_package_structure.py
```

Expected output:
```
🎉 ALL TESTS PASSED! Package structure is correct.
```

## 📝 Configuration

Configuration files are now in the `configs/` directory:
- `configs/default_config.yaml` - Default settings
- Update main.py default: `--config configs/default_config.yaml`

## 🗂️ File Organization Guide

| **Directory** | **Purpose** | **Contents** |
|---------------|-------------|--------------|
| `src/healthcare_crl/` | Core package | Main framework modules |
| `src/healthcare_crl/agents/` | RL Agents | CRL agents, multi-agent systems |
| `src/healthcare_crl/baselines/` | Baseline Models | Traditional comparison models |
| `src/healthcare_crl/data/` | Data Processing | Pipelines, loaders, preprocessors |
| `src/healthcare_crl/models/` | ML Models | Causal graphs, neural networks |
| `src/healthcare_crl/utils/` | Utilities | Metrics, helpers, common functions |
| `tests/` | Test Suite | Unit tests, integration tests |
| `configs/` | Configuration | YAML configs, hyperparameters |
| `data/` | Data Files | Datasets, rules, processed data |
| `docs/` | Documentation | Guides, API docs, tutorials |
| `scripts/` | Utility Scripts | Analysis, validation, comparison |
| `results/` | Output | Models, figures, logs, reports |

This new structure provides a solid foundation for the Healthcare CRL Framework while maintaining all existing functionality and improving code organization, maintainability, and development experience.