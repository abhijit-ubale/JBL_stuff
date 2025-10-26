"""
Real data pipeline for healthcare supply chain analysis.
Loads and processes actual datasets from DATA_SPLITS folder.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)


@dataclass
class SupplyChainRecord:
    """Supply chain transaction record from GHSC dataset."""
    country: str
    commodity_type: str
    order_volume: int
    lead_time_days: int
    on_time_delivery_pct: float
    delivery_delay_days: float
    disruption_type: str
    supplier_reliability_score: float
    resupply_time_days: float
    stockout_frequency: float
    transport_mode: str
    freight_cost_usd: float
    co2_emissions_tons: float
    warehouse_type: str
    data_year: int
    disruption_severity: int
    outcome_metric: float


@dataclass
class LogisticsPerformance:
    """Logistics Performance Index record."""
    economy: str
    lpi_score: float
    customs_score: float
    infrastructure_score: float
    international_shipments_score: float
    logistics_competence_score: float
    timeliness_score: float
    tracking_tracing_score: float


@dataclass
class DisasterRecord:
    """Natural disaster record from EM-DAT dataset."""
    disaster_no: str
    disaster_type: str
    disaster_subtype: str
    country: str
    region: str
    start_year: int
    start_month: float
    end_year: int
    end_month: float
    total_deaths: float
    total_affected: float
    total_damage_usd: float
    latitude: float
    longitude: float


class RealDataPipeline:
    """Loads and processes real healthcare supply chain datasets."""
    
    def __init__(self, data_splits_path: str = "DATA_SPLITS"):
        """Initialize data pipeline with path to data splits."""
        self.data_splits_path = Path(data_splits_path)
        self.datasets = {}
        logger.info(f"Initialized RealDataPipeline with data path: {data_splits_path}")
        
        # Dataset file mapping
        self.dataset_files = {
            'supply_chain_train': 'GHSC_PSM_Synthetic_Resilience_Dataset_v2_consistent_traindata.csv',
            'supply_chain_test': 'GHSC_PSM_Synthetic_Resilience_Dataset_v2_consistent_testdata.csv',
            'logistics_performance_train': 'International_LPI_from_2007_to_2023_traindata.csv', 
            'logistics_performance_test': 'International_LPI_from_2007_to_2023_testdata.csv',
            'natural_disasters_train': 'NaturalDisaster_public_emdat_custom_request_traindata.csv',
            'natural_disasters_test': 'NaturalDisaster_public_emdat_custom_request_testdata.csv',
            'public_emergencies_train': 'Public_emdat_custom_request_2025-10-23_traindata.csv',
            'public_emergencies_test': 'Public_emdat_custom_request_2025-10-23_testdata.csv'
        }
        
        # Load datasets on initialization
        self._load_all_datasets()
    
    def _load_all_datasets(self) -> None:
        """Load all datasets from CSV files."""
        logger.info("Loading all datasets from CSV files...")
        
        try:
            # Load supply chain data
            self.datasets['supply_chain_train'] = self._load_supply_chain_data('supply_chain_train')
            self.datasets['supply_chain_test'] = self._load_supply_chain_data('supply_chain_test')
            
            # Load logistics performance data
            self.datasets['logistics_performance_train'] = self._load_logistics_data('logistics_performance_train')
            self.datasets['logistics_performance_test'] = self._load_logistics_data('logistics_performance_test')
            
            # Load disaster data
            self.datasets['natural_disasters_train'] = self._load_disaster_data('natural_disasters_train')
            self.datasets['natural_disasters_test'] = self._load_disaster_data('natural_disasters_test')
            
            # Load public emergency data
            self.datasets['public_emergencies_train'] = self._load_disaster_data('public_emergencies_train')
            self.datasets['public_emergencies_test'] = self._load_disaster_data('public_emergencies_test')
            
            logger.info(f"Successfully loaded {len(self.datasets)} datasets")
            
        except Exception as e:
            logger.error(f"Error loading datasets: {e}")
            raise
    
    def _load_supply_chain_data(self, dataset_key: str) -> pd.DataFrame:
        """Load GHSC supply chain dataset."""
        filepath = self.data_splits_path / self.dataset_files[dataset_key]
        
        if not filepath.exists():
            raise FileNotFoundError(f"Dataset file not found: {filepath}")
        
        logger.info(f"Loading supply chain data from: {filepath}")
        df = pd.read_csv(filepath)
        
        # Clean and preprocess the data
        df = self._preprocess_supply_chain_data(df)
        
        logger.info(f"Loaded {len(df)} supply chain records from {dataset_key}")
        return df
    
    def _preprocess_supply_chain_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess GHSC supply chain data."""
        # Handle missing values
        df['Disruption_Type'] = df['Disruption_Type'].fillna('None')
        df['Delivery_Delay_Days'] = df['Delivery_Delay_Days'].fillna(0)
        
        # Normalize percentage columns
        df['On_Time_Delivery_Normalized'] = df['On_Time_Delivery_%'] / 100.0
        
        # Create derived features
        df['Lead_Time_Category'] = pd.cut(df['Lead_Time_Days'], 
                                         bins=[0, 30, 60, 90, float('inf')],
                                         labels=['Short', 'Medium', 'Long', 'Very_Long'])
        
        df['Cost_Per_Unit'] = df['Freight_Cost_USD'] / df['Order_Volume_Units']
        
        # Encode categorical variables
        df['Transport_Mode_Encoded'] = pd.Categorical(df['Transport_Mode']).codes
        df['Warehouse_Type_Encoded'] = pd.Categorical(df['Warehouse_Type']).codes
        
        return df
    
    def _load_logistics_data(self, dataset_key: str) -> pd.DataFrame:
        """Load International LPI dataset."""
        filepath = self.data_splits_path / self.dataset_files[dataset_key]
        
        if not filepath.exists():
            raise FileNotFoundError(f"Dataset file not found: {filepath}")
        
        logger.info(f"Loading logistics data from: {filepath}")
        df = pd.read_csv(filepath)
        
        # Clean and preprocess
        df = self._preprocess_logistics_data(df)
        
        logger.info(f"Loaded {len(df)} logistics performance records from {dataset_key}")
        return df
    
    def _preprocess_logistics_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess LPI data."""
        # Normalize all score columns to [0, 1] range
        score_columns = [col for col in df.columns if 'Score' in col]
        for col in score_columns:
            if df[col].max() > 1:
                df[f"{col}_Normalized"] = df[col] / 5.0  # LPI scores are typically 1-5
        
        # Create overall logistics efficiency score
        df['Overall_Logistics_Efficiency'] = (
            df['LPI Score'] + df['Customs Score'] + df['Infrastructure Score'] + 
            df['Timeliness Score'] + df['Tracking and Tracing Score']
        ) / 5.0
        
        return df
    
    def _load_disaster_data(self, dataset_key: str) -> pd.DataFrame:
        """Load disaster/emergency data."""
        filepath = self.data_splits_path / self.dataset_files[dataset_key]
        
        if not filepath.exists():
            raise FileNotFoundError(f"Dataset file not found: {filepath}")
        
        logger.info(f"Loading disaster data from: {filepath}")
        df = pd.read_csv(filepath)
        
        # Clean and preprocess
        df = self._preprocess_disaster_data(df)
        
        logger.info(f"Loaded {len(df)} disaster records from {dataset_key}")
        return df
    
    def _preprocess_disaster_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess disaster data."""
        # Handle missing values in damage columns
        damage_cols = ['Total Deaths', 'No. Affected', 'Total Damage (\'000 US$)']
        for col in damage_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Create disaster severity categories
        if 'Total Deaths' in df.columns and 'No. Affected' in df.columns:
            df['Disaster_Severity_Score'] = (
                np.log1p(df['Total Deaths']) * 0.4 + 
                np.log1p(df['No. Affected']) * 0.6
            )
            
            df['Disaster_Severity_Category'] = pd.cut(df['Disaster_Severity_Score'],
                                                     bins=[-np.inf, 2, 5, 8, np.inf],
                                                     labels=['Low', 'Medium', 'High', 'Extreme'])
        
        # Extract year for time-based analysis
        if 'Start Year' in df.columns:
            df['Start_Year'] = pd.to_numeric(df['Start Year'], errors='coerce')
        
        return df
    
    def get_supply_chain_records(self, mode: str = 'train') -> pd.DataFrame:
        """Get supply chain records."""
        dataset_key = f'supply_chain_{mode}'
        if dataset_key not in self.datasets:
            raise ValueError(f"Dataset {dataset_key} not loaded")
        
        return self.datasets[dataset_key].copy()
    
    def get_logistics_performance(self, mode: str = 'train') -> pd.DataFrame:
        """Get logistics performance data."""
        dataset_key = f'logistics_performance_{mode}'
        if dataset_key not in self.datasets:
            raise ValueError(f"Dataset {dataset_key} not loaded")
        
        return self.datasets[dataset_key].copy()
    
    def get_disaster_records(self, mode: str = 'train', disaster_type: str = 'natural') -> pd.DataFrame:
        """Get disaster records."""
        if disaster_type == 'natural':
            dataset_key = f'natural_disasters_{mode}'
        elif disaster_type == 'public':
            dataset_key = f'public_emergencies_{mode}'
        else:
            raise ValueError(f"Unknown disaster type: {disaster_type}")
        
        if dataset_key not in self.datasets:
            raise ValueError(f"Dataset {dataset_key} not loaded")
        
        return self.datasets[dataset_key].copy()
    
    def create_integrated_features(self, mode: str = 'train') -> pd.DataFrame:
        """Create integrated feature set combining all datasets."""
        logger.info(f"Creating integrated features for {mode} mode...")
        
        # Get primary supply chain data
        supply_chain_df = self.get_supply_chain_records(mode)
        
        # Get logistics performance by country
        logistics_df = self.get_logistics_performance(mode)
        
        # Get disaster data
        natural_disasters_df = self.get_disaster_records(mode, 'natural')
        public_emergencies_df = self.get_disaster_records(mode, 'public')
        
        # Merge logistics performance with supply chain data
        integrated_df = supply_chain_df.merge(
            logistics_df[['Economy', 'LPI Score', 'Overall_Logistics_Efficiency']], 
            left_on='Country', 
            right_on='Economy', 
            how='left'
        )
        
        # Add disaster risk by country and year
        disaster_risk = self._calculate_disaster_risk_by_country_year(
            natural_disasters_df, public_emergencies_df
        )
        
        integrated_df = integrated_df.merge(
            disaster_risk,
            on=['Country', 'Data_Year'],
            how='left'
        )
        
        # Fill missing values
        integrated_df['LPI Score'] = integrated_df['LPI Score'].fillna(2.5)  # Global median
        integrated_df['Overall_Logistics_Efficiency'] = integrated_df['Overall_Logistics_Efficiency'].fillna(0.5)
        integrated_df['Disaster_Risk_Score'] = integrated_df['Disaster_Risk_Score'].fillna(0.1)
        integrated_df['Annual_Disaster_Count'] = integrated_df['Annual_Disaster_Count'].fillna(0)
        
        logger.info(f"Created integrated dataset with {len(integrated_df)} records and {len(integrated_df.columns)} features")
        
        return integrated_df
    
    def _calculate_disaster_risk_by_country_year(self, natural_df: pd.DataFrame, 
                                               public_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate annual disaster risk by country and year."""
        
        # Combine both disaster datasets
        all_disasters = []
        
        # Process natural disasters
        if 'Start_Year' in natural_df.columns and 'Country' in natural_df.columns:
            natural_risk = natural_df.groupby(['Country', 'Start_Year']).agg({
                'DisNo.': 'count',
                'Disaster_Severity_Score': 'mean'
            }).reset_index()
            natural_risk.columns = ['Country', 'Year', 'Natural_Disaster_Count', 'Natural_Disaster_Severity']
            all_disasters.append(natural_risk)
        
        # Process public emergencies  
        if 'Start Year' in public_df.columns and 'Country' in public_df.columns:
            public_risk = public_df.groupby(['Country', 'Start Year']).agg({
                'DisNo.': 'count',
                'Disaster_Severity_Score': 'mean'
            }).reset_index()
            public_risk.columns = ['Country', 'Year', 'Public_Emergency_Count', 'Public_Emergency_Severity']
            all_disasters.append(public_risk)
        
        # Combine risk data
        if all_disasters:
            if len(all_disasters) == 2:
                disaster_risk = all_disasters[0].merge(all_disasters[1], on=['Country', 'Year'], how='outer')
            else:
                disaster_risk = all_disasters[0]
                
            disaster_risk = disaster_risk.fillna(0)
            
            # Calculate combined disaster risk score
            disaster_risk['Annual_Disaster_Count'] = (
                disaster_risk.get('Natural_Disaster_Count', 0) + 
                disaster_risk.get('Public_Emergency_Count', 0)
            )
            
            disaster_risk['Disaster_Risk_Score'] = (
                disaster_risk['Annual_Disaster_Count'] * 0.6 +
                disaster_risk.get('Natural_Disaster_Severity', 0) * 0.2 +
                disaster_risk.get('Public_Emergency_Severity', 0) * 0.2
            )
            
            # Normalize risk score
            if disaster_risk['Disaster_Risk_Score'].max() > 0:
                disaster_risk['Disaster_Risk_Score'] = (
                    disaster_risk['Disaster_Risk_Score'] / disaster_risk['Disaster_Risk_Score'].max()
                )
            
            disaster_risk.rename(columns={'Year': 'Data_Year'}, inplace=True)
            
            return disaster_risk[['Country', 'Data_Year', 'Disaster_Risk_Score', 'Annual_Disaster_Count']]
        
        else:
            # Return empty dataframe with correct structure
            return pd.DataFrame(columns=['Country', 'Data_Year', 'Disaster_Risk_Score', 'Annual_Disaster_Count'])
    
    def get_feature_vector_for_state(self, record: Dict[str, Any]) -> np.ndarray:
        """Convert a supply chain record to feature vector for ML models."""
        
        # Define feature extraction based on available data
        features = []
        
        # Supply chain features
        features.append(record.get('Lead_Time_Days', 0) / 100.0)  # Normalized
        features.append(record.get('On_Time_Delivery_Normalized', 0.5))
        features.append(record.get('Supplier_Reliability_Score', 0.5))
        features.append(record.get('Stockout_Frequency_per_Year', 0.0))
        features.append(record.get('Cost_Per_Unit', 0) / 1000.0)  # Normalized
        
        # Logistics features
        features.append(record.get('LPI Score', 2.5) / 5.0)  # Normalized to [0,1]
        features.append(record.get('Overall_Logistics_Efficiency', 0.5))
        
        # Disruption features  
        disruption_severity = record.get('Disruption_Severity', 0)
        features.append(disruption_severity / 5.0)  # Normalized
        
        # Transport mode (one-hot encoded)
        transport_mode = record.get('Transport_Mode', 'Air')
        for mode in ['Air', 'Ocean', 'Land']:
            features.append(1.0 if transport_mode == mode else 0.0)
        
        # Disaster risk
        features.append(record.get('Disaster_Risk_Score', 0.1))
        features.append(record.get('Annual_Disaster_Count', 0) / 10.0)  # Normalized
        
        # Warehouse type
        warehouse_encoded = record.get('Warehouse_Type_Encoded', 0)
        features.append(warehouse_encoded / 3.0)  # Assuming 4 types (0-3)
        
        # Commodity type diversity (simple encoding)
        commodity = record.get('Commodity_Type', 'Other')
        for comm_type in ['Malaria_RDT', 'Contraceptive', 'HIV_ARV', 'LLIN', 'Maternal_Health']:
            features.append(1.0 if commodity == comm_type else 0.0)
        
        # Outcome metric (target variable in some contexts)
        features.append(record.get('Outcome_Metric', 0.5))
        
        return np.array(features, dtype=np.float32)
    
    def get_state_dimension(self) -> int:
        """Get the dimensionality of state vectors."""
        # Based on feature vector extraction method
        return 20  # Updated to match real feature vector size
    
    def get_action_space_size(self) -> int:
        """Get the size of action space."""
        return 6  # Same as before: 5 actions + no-action
    
    def sample_episode_data(self, mode: str = 'train', episode_length: int = 50) -> List[Dict[str, Any]]:
        """Sample episode data for RL training."""
        integrated_df = self.create_integrated_features(mode)
        
        if len(integrated_df) == 0:
            raise ValueError(f"No integrated data available for mode: {mode}")
        
        # Sample random records for episode simulation
        episode_records = []
        
        for step in range(episode_length):
            # Sample a random record from the integrated dataset
            record_idx = np.random.randint(0, len(integrated_df))
            record = integrated_df.iloc[record_idx].to_dict()
            
            # Add step information
            record['step'] = step
            record['episode_progress'] = step / episode_length
            
            episode_records.append(record)
        
        return episode_records
    
    def get_dataset_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about loaded datasets."""
        stats = {}
        
        for name, df in self.datasets.items():
            if df is not None and len(df) > 0:
                stats[name] = {
                    'num_records': len(df),
                    'num_features': len(df.columns),
                    'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024*1024),
                    'missing_values': df.isnull().sum().sum(),
                    'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
                    'categorical_columns': len(df.select_dtypes(include=['object']).columns)
                }
        
        return stats
    
    def export_processed_data(self, output_dir: str = "data/processed/") -> None:
        """Export processed datasets for external use."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting processed data to {output_path}")
        
        # Export integrated training and test datasets
        for mode in ['train', 'test']:
            try:
                integrated_df = self.create_integrated_features(mode)
                
                # Save as both CSV and Parquet for compatibility
                integrated_df.to_csv(output_path / f"integrated_features_{mode}.csv", index=False)
                integrated_df.to_parquet(output_path / f"integrated_features_{mode}.parquet", index=False)
                
                logger.info(f"Exported integrated {mode} dataset: {len(integrated_df)} records")
                
            except Exception as e:
                logger.warning(f"Could not export integrated {mode} dataset: {e}")
        
        # Export individual processed datasets
        for name, df in self.datasets.items():
            try:
                df.to_csv(output_path / f"{name}.csv", index=False)
                df.to_parquet(output_path / f"{name}.parquet", index=False)
            except Exception as e:
                logger.warning(f"Could not export {name}: {e}")
        
        # Export metadata
        stats = self.get_dataset_statistics()
        with open(output_path / "dataset_statistics.json", 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        logger.info(f"Data export completed to {output_path}")


if __name__ == "__main__":
    # Test real data pipeline
    pipeline = RealDataPipeline()
    
    # Print dataset statistics
    stats = pipeline.get_dataset_statistics()
    print("Dataset Statistics:")
    for name, stat in stats.items():
        print(f"\n{name.upper()}:")
        for key, value in stat.items():
            print(f"  {key}: {value}")
    
    # Test integrated feature creation
    try:
        train_features = pipeline.create_integrated_features('train')
        print(f"\nIntegrated training features: {train_features.shape}")
        print("Columns:", list(train_features.columns))
        
        # Test feature vector extraction
        sample_record = train_features.iloc[0].to_dict()
        feature_vector = pipeline.get_feature_vector_for_state(sample_record)
        print(f"Feature vector shape: {feature_vector.shape}")
        print(f"Sample feature vector: {feature_vector}")
        
    except Exception as e:
        print(f"Error creating integrated features: {e}")
    
    # Export processed data
    try:
        pipeline.export_processed_data()
        print("\nProcessed data exported successfully")
    except Exception as e:
        print(f"Error exporting data: {e}")