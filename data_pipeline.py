"""
Synthetic data pipeline for healthcare supply chain simulation.
Generates realistic datasets for hospitals, suppliers, products, and disruptions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class NetworkNode:
    """Base class for supply chain network nodes."""
    id: str
    name: str
    latitude: float
    longitude: float
    capacity: int
    node_type: str


@dataclass
class Hospital(NetworkNode):
    """Healthcare facility node."""
    bed_count: int
    specialty_services: List[str]
    trauma_level: Optional[int]
    teaching_hospital: bool
    system_affiliation: Optional[str]


@dataclass
class Supplier(NetworkNode):
    """Medical supplier/manufacturer node."""
    product_categories: List[str]
    manufacturing_capacity: Dict[str, int]
    quality_rating: float
    financial_stability: float
    regulatory_compliance: Dict[str, bool]


@dataclass
class Distributor(NetworkNode):
    """Distribution center node."""
    warehouse_capacity: int
    service_regions: List[str]
    transportation_modes: List[str]
    cold_chain_capable: bool


class HealthcareDataPipeline:
    """Generates synthetic healthcare supply chain data."""
    
    def __init__(self, random_seed: int = 42):
        """Initialize data pipeline with random seed for reproducibility."""
        np.random.seed(random_seed)
        self.random_seed = random_seed
        
        # US hospital data based on real statistics
        self.us_states = [
            'CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI',
            'NJ', 'VA', 'WA', 'AZ', 'MA', 'TN', 'IN', 'MO', 'MD', 'WI'
        ]
        
        # Medical product categories
        self.product_categories = {
            'pharmaceuticals': ['antibiotics', 'vaccines', 'oncology_drugs', 'cardiac_meds', 'insulin'],
            'medical_devices': ['ventilators', 'iv_pumps', 'monitors', 'defibrillators', 'surgical_tools'],
            'supplies': ['ppe', 'syringes', 'catheters', 'blood_bags', 'surgical_supplies'],
            'diagnostics': ['test_kits', 'reagents', 'imaging_contrast', 'lab_supplies']
        }
        
        # Disruption event templates based on historical events
        self.historical_disruptions = {
            'pandemic': {
                'covid_2020': {'severity': 0.9, 'duration_days': 730, 'affected_regions': 'all'},
                'h1n1_2009': {'severity': 0.6, 'duration_days': 180, 'affected_regions': 'all'}
            },
            'hurricane': {
                'katrina_2005': {'severity': 0.8, 'duration_days': 30, 'affected_regions': ['LA', 'MS', 'AL']},
                'harvey_2017': {'severity': 0.7, 'duration_days': 14, 'affected_regions': ['TX']},
                'sandy_2012': {'severity': 0.6, 'duration_days': 10, 'affected_regions': ['NY', 'NJ']}
            },
            'cyber_attack': {
                'colonial_pipeline_2021': {'severity': 0.7, 'duration_days': 6, 'affected_regions': ['southeast']},
                'hospital_ransomware_2020': {'severity': 0.8, 'duration_days': 21, 'affected_regions': 'random'}
            },
            'port_closure': {
                'suez_canal_2021': {'severity': 0.5, 'duration_days': 6, 'affected_regions': 'global'},
                'la_port_congestion_2021': {'severity': 0.6, 'duration_days': 120, 'affected_regions': ['west_coast']}
            }
        }
    
    def generate_hospitals(self, num_hospitals: int = 5000) -> pd.DataFrame:
        """Generate synthetic US hospital network."""
        logger.info(f"Generating {num_hospitals} hospital records...")
        
        hospitals = []
        
        # Hospital size distribution (based on AHA data)
        size_distribution = {
            'critical_access': 0.25,  # <25 beds
            'small': 0.35,           # 25-99 beds
            'medium': 0.25,          # 100-299 beds
            'large': 0.12,           # 300-499 beds
            'major': 0.03            # 500+ beds
        }
        
        bed_ranges = {
            'critical_access': (6, 24),
            'small': (25, 99),
            'medium': (100, 299),
            'large': (300, 499),
            'major': (500, 1200)
        }
        
        specialty_services = [
            'emergency', 'surgery', 'cardiology', 'oncology', 'neurology',
            'pediatrics', 'obstetrics', 'orthopedics', 'radiology', 'pathology'
        ]
        
        for i in range(num_hospitals):
            # Determine hospital size category
            size_category = np.random.choice(
                list(size_distribution.keys()),
                p=list(size_distribution.values())
            )
            
            bed_count = np.random.randint(*bed_ranges[size_category])
            
            # Geographic distribution (population-weighted by state)
            state_weights = {
                'CA': 0.12, 'TX': 0.09, 'FL': 0.065, 'NY': 0.058, 'PA': 0.039,
                'IL': 0.038, 'OH': 0.035, 'GA': 0.032, 'NC': 0.032, 'MI': 0.030
            }
            
            state = np.random.choice(
                list(state_weights.keys()),
                p=list(state_weights.values())
            )
            
            # Generate coordinates within state bounds (simplified)
            state_coords = {
                'CA': (36.7783, -119.4179), 'TX': (31.9686, -99.9018),
                'FL': (27.7663, -81.6868), 'NY': (40.7589, -73.7004),
                'PA': (40.5908, -77.2098)
            }
            
            base_lat, base_lon = state_coords.get(state, (39.8283, -98.5795))
            latitude = base_lat + np.random.normal(0, 1.5)
            longitude = base_lon + np.random.normal(0, 1.5)
            
            # Specialty services based on hospital size
            num_specialties = min(len(specialty_services), 
                                max(3, int(np.random.normal(bed_count/50, 2))))
            specialties = np.random.choice(
                specialty_services, size=num_specialties, replace=False
            ).tolist()
            
            hospital = Hospital(
                id=f"H{i:04d}",
                name=f"Hospital_{state}_{i:04d}",
                latitude=latitude,
                longitude=longitude,
                capacity=bed_count,
                node_type="hospital",
                bed_count=bed_count,
                specialty_services=specialties,
                trauma_level=np.random.choice([None, 1, 2, 3, 4], p=[0.4, 0.05, 0.1, 0.25, 0.2]),
                teaching_hospital=np.random.choice([True, False], p=[0.15, 0.85]),
                system_affiliation=f"System_{np.random.randint(1, 50)}" if np.random.rand() < 0.6 else None
            )
            hospitals.append(hospital)
        
        return pd.DataFrame([hospital.__dict__ for hospital in hospitals])
    
    def generate_suppliers(self, num_suppliers: int = 500) -> pd.DataFrame:
        """Generate synthetic supplier network."""
        logger.info(f"Generating {num_suppliers} supplier records...")
        
        suppliers = []
        
        # Supplier types and their product focus
        supplier_types = {
            'pharmaceutical_manufacturer': ['pharmaceuticals'],
            'medical_device_manufacturer': ['medical_devices'],
            'supply_distributor': ['supplies'],
            'diagnostics_company': ['diagnostics'],
            'multi_category_supplier': ['pharmaceuticals', 'supplies']
        }
        
        for i in range(num_suppliers):
            supplier_type = np.random.choice(list(supplier_types.keys()))
            product_cats = supplier_types[supplier_type]
            
            # Generate manufacturing capacity
            manufacturing_capacity = {}
            for category in product_cats:
                for product in self.product_categories[category]:
                    if np.random.rand() < 0.7:  # Not all suppliers make all products
                        capacity = np.random.lognormal(8, 1.5)  # Log-normal distribution
                        manufacturing_capacity[product] = int(capacity)
            
            # Geographic clustering (suppliers often near major cities/ports)
            major_cities = [
                (40.7128, -74.0060),  # NYC
                (34.0522, -118.2437), # LA
                (41.8781, -87.6298),  # Chicago
                (29.7604, -95.3698),  # Houston
                (39.9526, -75.1652)   # Philadelphia
            ]
            
            base_lat, base_lon = major_cities[np.random.randint(0, len(major_cities))]
            latitude = base_lat + np.random.normal(0, 0.5)
            longitude = base_lon + np.random.normal(0, 0.5)
            
            supplier = Supplier(
                id=f"S{i:04d}",
                name=f"Supplier_{supplier_type}_{i:04d}",
                latitude=latitude,
                longitude=longitude,
                capacity=sum(manufacturing_capacity.values()),
                node_type="supplier",
                product_categories=product_cats,
                manufacturing_capacity=manufacturing_capacity,
                quality_rating=np.random.beta(8, 2),  # Skewed towards higher quality
                financial_stability=np.random.beta(5, 2),
                regulatory_compliance={
                    'fda_approved': np.random.choice([True, False], p=[0.85, 0.15]),
                    'iso_certified': np.random.choice([True, False], p=[0.70, 0.30]),
                    'gmp_compliant': np.random.choice([True, False], p=[0.80, 0.20])
                }
            )
            suppliers.append(supplier)
        
        return pd.DataFrame([supplier.__dict__ for supplier in suppliers])
    
    def generate_distributors(self, num_distributors: int = 200) -> pd.DataFrame:
        """Generate synthetic distributor network."""
        logger.info(f"Generating {num_distributors} distributor records...")
        
        distributors = []
        
        for i in range(num_distributors):
            # Regional service patterns
            service_regions = np.random.choice(
                self.us_states, 
                size=np.random.randint(1, 8), 
                replace=False
            ).tolist()
            
            # Transportation capabilities
            transport_modes = []
            if np.random.rand() < 0.9:
                transport_modes.append('ground')
            if np.random.rand() < 0.4:
                transport_modes.append('air')
            if np.random.rand() < 0.2:
                transport_modes.append('sea')
            
            # Warehouse capacity based on service area
            base_capacity = len(service_regions) * np.random.lognormal(10, 1)
            
            distributor = Distributor(
                id=f"D{i:04d}",
                name=f"Distributor_{i:04d}",
                latitude=np.random.uniform(25.0, 49.0),  # Continental US
                longitude=np.random.uniform(-125.0, -66.0),
                capacity=int(base_capacity),
                node_type="distributor",
                warehouse_capacity=int(base_capacity),
                service_regions=service_regions,
                transportation_modes=transport_modes,
                cold_chain_capable=np.random.choice([True, False], p=[0.6, 0.4])
            )
            distributors.append(distributor)
        
        return pd.DataFrame([distributor.__dict__ for distributor in distributors])
    
    def generate_products(self) -> pd.DataFrame:
        """Generate product catalog with characteristics."""
        logger.info("Generating product catalog...")
        
        products = []
        product_id = 0
        
        for category, items in self.product_categories.items():
            for item in items:
                product = {
                    'product_id': f"P{product_id:04d}",
                    'name': item,
                    'category': category,
                    'unit_cost': np.random.lognormal(3, 1.5),  # Varies widely
                    'shelf_life_days': self._get_shelf_life(category, item),
                    'temperature_controlled': self._requires_cold_chain(category, item),
                    'criticality_score': np.random.beta(2, 5),  # Most products not critical
                    'demand_volatility': np.random.beta(2, 8),  # Most have stable demand
                    'regulatory_class': self._get_regulatory_class(category),
                    'supply_complexity': np.random.choice(['low', 'medium', 'high'], p=[0.4, 0.4, 0.2])
                }
                products.append(product)
                product_id += 1
        
        return pd.DataFrame(products)
    
    def _get_shelf_life(self, category: str, item: str) -> int:
        """Get realistic shelf life based on product type."""
        if category == 'pharmaceuticals':
            if 'vaccine' in item:
                return np.random.randint(180, 730)  # 6 months to 2 years
            else:
                return np.random.randint(365, 1825)  # 1-5 years
        elif category == 'medical_devices':
            return np.random.randint(1825, 3650)  # 5-10 years
        elif category == 'supplies':
            if 'blood' in item:
                return np.random.randint(35, 42)  # Blood products expire quickly
            else:
                return np.random.randint(730, 1825)  # 2-5 years
        else:
            return np.random.randint(365, 1095)  # 1-3 years
    
    def _requires_cold_chain(self, category: str, item: str) -> bool:
        """Determine if product requires temperature control."""
        if category == 'pharmaceuticals':
            return 'vaccine' in item or 'insulin' in item or np.random.rand() < 0.3
        elif 'blood' in item:
            return True
        else:
            return np.random.rand() < 0.1
    
    def _get_regulatory_class(self, category: str) -> str:
        """Assign regulatory classification."""
        if category == 'pharmaceuticals':
            return np.random.choice(['prescription', 'otc', 'controlled'], p=[0.6, 0.3, 0.1])
        elif category == 'medical_devices':
            return np.random.choice(['class_i', 'class_ii', 'class_iii'], p=[0.5, 0.4, 0.1])
        else:
            return 'unregulated'
    
    def generate_disruption_scenarios(self, num_scenarios: int = 100) -> pd.DataFrame:
        """Generate disruption event scenarios based on historical patterns."""
        logger.info(f"Generating {num_scenarios} disruption scenarios...")
        
        scenarios = []
        
        for i in range(num_scenarios):
            # Select disruption type and template
            disruption_type = np.random.choice(list(self.historical_disruptions.keys()))
            templates = self.historical_disruptions[disruption_type]
            template_name = np.random.choice(list(templates.keys()))
            template = templates[template_name]
            
            # Add variability to template
            severity = template['severity'] * np.random.uniform(0.7, 1.3)
            severity = max(0.1, min(1.0, severity))  # Clamp to [0.1, 1.0]
            
            duration = template['duration_days'] * np.random.uniform(0.5, 2.0)
            duration = max(1, int(duration))
            
            # Generate start date (within last 5 years or future scenarios)
            start_date = datetime.now() - timedelta(days=np.random.randint(0, 1825))
            
            scenario = {
                'scenario_id': f"DS{i:04d}",
                'disruption_type': disruption_type,
                'template': template_name,
                'severity': severity,
                'duration_days': duration,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'affected_regions': template['affected_regions'],
                'compound_events': self._generate_compound_events(disruption_type),
                'propagation_delay_days': np.random.randint(1, 7),
                'recovery_pattern': np.random.choice(['linear', 'exponential', 'stepwise'])
            }
            scenarios.append(scenario)
        
        return pd.DataFrame(scenarios)
    
    def _generate_compound_events(self, primary_type: str) -> List[Dict]:
        """Generate compound disruption events that often co-occur."""
        compound_events = []
        
        # Probability of compound events based on primary disruption
        compound_probabilities = {
            'pandemic': {'cyber_attack': 0.3, 'port_closure': 0.4},
            'hurricane': {'port_closure': 0.7, 'cyber_attack': 0.2},
            'cyber_attack': {'pandemic': 0.1, 'port_closure': 0.2},
            'port_closure': {'hurricane': 0.3, 'cyber_attack': 0.2}
        }
        
        if primary_type in compound_probabilities:
            for event_type, probability in compound_probabilities[primary_type].items():
                if np.random.rand() < probability:
                    compound_events.append({
                        'type': event_type,
                        'delay_days': np.random.randint(1, 30),
                        'severity_multiplier': np.random.uniform(0.3, 0.8)
                    })
        
        return compound_events
    
    def generate_baseline_demand(self, hospitals_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
        """Generate baseline demand patterns for hospitals and products."""
        logger.info("Generating baseline demand patterns...")
        
        demand_data = []
        
        for _, hospital in hospitals_df.iterrows():
            for _, product in products_df.iterrows():
                # Base demand proportional to hospital size and product criticality
                base_demand = hospital['bed_count'] * product['criticality_score'] * np.random.lognormal(2, 1)
                
                # Seasonal patterns (some products have seasonal variation)
                seasonal_factor = 1.0
                if 'vaccine' in product['name']:
                    seasonal_factor = np.random.uniform(0.5, 2.0)  # Flu season variation
                
                # Weekly pattern (higher demand during weekdays for elective procedures)
                weekly_pattern = np.random.beta(2, 2) * 0.4 + 0.8  # 0.8 to 1.2 multiplier
                
                demand_record = {
                    'hospital_id': hospital['id'],
                    'product_id': product['product_id'],
                    'base_daily_demand': base_demand,
                    'seasonal_factor': seasonal_factor,
                    'weekly_pattern': weekly_pattern,
                    'demand_volatility': product['demand_volatility'],
                    'lead_time_days': np.random.randint(1, 14),
                    'safety_stock_days': np.random.randint(3, 30)
                }
                demand_data.append(demand_record)
        
        return pd.DataFrame(demand_data)
    
    def save_datasets(self, output_dir: str = "data/") -> Dict[str, pd.DataFrame]:
        """Generate and save all datasets."""
        logger.info("Generating complete healthcare supply chain dataset...")
        
        # Generate all components
        hospitals_df = self.generate_hospitals()
        suppliers_df = self.generate_suppliers()
        distributors_df = self.generate_distributors()
        products_df = self.generate_products()
        disruptions_df = self.generate_disruption_scenarios()
        demand_df = self.generate_baseline_demand(hospitals_df, products_df)
        
        # Create comprehensive dataset dictionary
        datasets = {
            'hospitals': hospitals_df,
            'suppliers': suppliers_df,
            'distributors': distributors_df,
            'products': products_df,
            'disruptions': disruptions_df,
            'baseline_demand': demand_df
        }
        
        # Save to files
        from pathlib import Path
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for name, df in datasets.items():
            filepath = Path(output_dir) / f"{name}.parquet"
            df.to_parquet(filepath, index=False)
            logger.info(f"Saved {name}: {len(df)} records to {filepath}")
        
        # Save metadata
        metadata = {
            'generation_timestamp': datetime.now().isoformat(),
            'random_seed': self.random_seed,
            'dataset_sizes': {name: len(df) for name, df in datasets.items()},
            'data_schema': {
                name: list(df.columns) for name, df in datasets.items()
            }
        }
        
        with open(Path(output_dir) / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Dataset generation completed. Files saved to {output_dir}")
        return datasets


if __name__ == "__main__":
    # Generate sample datasets
    pipeline = HealthcareDataPipeline(random_seed=42)
    datasets = pipeline.save_datasets()
    
    # Print summary statistics
    for name, df in datasets.items():
        print(f"\n{name.upper()}: {len(df)} records")
        print(df.head())