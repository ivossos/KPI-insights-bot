import pandas as pd
import numpy as np
import logging
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import json

from ..config import settings, config
from ..models.schemas import ExpenseRecord, PayrollRecord, ContractRecord

logger = logging.getLogger(__name__)

class DataProcessor:
    """Handles ETL pipeline for data normalization and enrichment"""
    
    def __init__(self):
        self.processed_data_path = Path(config["data_storage"]["processed_data_path"])
        self.catmat_mapping = self._load_catmat_mapping()
        self.price_stats_cache = {}
        
    def _load_catmat_mapping(self) -> Dict[str, str]:
        """Load CATMAT/CATSER mapping from external source"""
        # In a real implementation, this would fetch from API or local database
        # For now, return a sample mapping
        return {
            "material_escritorio": "CATMAT_001",
            "combustivel": "CATMAT_002",
            "servico_limpeza": "CATSER_001",
            "consultoria": "CATSER_002"
        }
        
    async def process_all_data(self) -> None:
        """Process all pending data"""
        logger.info("Starting data processing pipeline")
        
        try:
            # Find all parquet files to process
            parquet_files = list(self.processed_data_path.glob("**/*.parquet"))
            
            for file_path in parquet_files:
                if not self._is_processed(file_path):
                    await self._process_file(file_path)
                    
            logger.info("Data processing pipeline completed")
            
        except Exception as e:
            logger.error(f"Error in data processing pipeline: {str(e)}")
            raise
            
    async def _process_file(self, file_path: Path) -> None:
        """Process a single parquet file"""
        logger.info(f"Processing file: {file_path}")
        
        try:
            # Read data
            df = pd.read_parquet(file_path)
            
            # Determine dataset type
            dataset_type = df['dataset_type'].iloc[0] if 'dataset_type' in df.columns else 'unknown'
            
            # Apply appropriate processing based on dataset type
            if dataset_type == 'despesas':
                processed_df = await self._process_expenses(df)
            elif dataset_type == 'folha':
                processed_df = await self._process_payroll(df)
            elif dataset_type == 'contratos':
                processed_df = await self._process_contracts(df)
            else:
                logger.warning(f"Unknown dataset type: {dataset_type}")
                return
                
            # Save processed data
            await self._save_processed_data(processed_df, file_path, dataset_type)
            
            # Mark as processed
            self._mark_as_processed(file_path)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
            
    async def _process_expenses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process expense data"""
        logger.info("Processing expense data")
        
        # Normalize currency values
        df['amount'] = df['amount'].apply(self._normalize_currency)
        
        # Normalize units
        df['unit'] = df['unit'].apply(self._normalize_unit)
        
        # Calculate unit price
        df['unit_price'] = df.apply(
            lambda row: row['amount'] / row['quantity'] if row['quantity'] > 0 else 0,
            axis=1
        )
        
        # Map to CATMAT/CATSER codes
        df['catmat_code'] = df['description'].apply(self._map_to_catmat)
        
        # Enrich with price statistics
        df = await self._enrich_with_price_stats(df)
        
        # Detect emergency purchases
        df['is_emergency'] = df['process_number'].apply(self._detect_emergency)
        
        return df
        
    async def _process_payroll(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process payroll data"""
        logger.info("Processing payroll data")
        
        # Normalize salary values
        df['salary'] = df['salary'].apply(self._normalize_currency)
        df['benefits'] = df['benefits'].apply(self._normalize_currency)
        df['total_payment'] = df['total_payment'].apply(self._normalize_currency)
        
        # Calculate benefits percentage
        df['benefits_percentage'] = df.apply(
            lambda row: (row['benefits'] / row['salary']) * 100 if row['salary'] > 0 else 0,
            axis=1
        )
        
        # Standardize position names
        df['position'] = df['position'].apply(self._standardize_position)
        
        return df
        
    async def _process_contracts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process contract data"""
        logger.info("Processing contract data")
        
        # Normalize contract values
        df['amount'] = df['amount'].apply(self._normalize_currency)
        
        # Parse dates
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
        
        # Calculate contract duration
        df['duration_days'] = (df['end_date'] - df['start_date']).dt.days
        
        # Detect emergency contracts
        df['is_emergency'] = df['description'].apply(self._detect_emergency)
        
        # Map to categories
        df['category'] = df['description'].apply(self._categorize_contract)
        
        return df
        
    def _normalize_currency(self, value: Any) -> float:
        """Normalize currency values"""
        if pd.isna(value):
            return 0.0
            
        if isinstance(value, (int, float)):
            return float(value)
            
        # Remove currency symbols and convert to float
        value_str = str(value).replace('R$', '').replace('$', '')
        value_str = value_str.replace('.', '').replace(',', '.')
        value_str = re.sub(r'[^\d.,]', '', value_str)
        
        try:
            return float(value_str)
        except ValueError:
            return 0.0
            
    def _normalize_unit(self, unit: Any) -> str:
        """Normalize unit values"""
        if pd.isna(unit):
            return 'unidade'
            
        unit_str = str(unit).lower().strip()
        
        # Mapping common units
        unit_mapping = {
            'un': 'unidade',
            'und': 'unidade',
            'pc': 'peça',
            'pç': 'peça',
            'kg': 'quilograma',
            'g': 'grama',
            'l': 'litro',
            'ml': 'mililitro',
            'm': 'metro',
            'cm': 'centímetro',
            'mm': 'milímetro',
            'm²': 'metro_quadrado',
            'm³': 'metro_cubico'
        }
        
        return unit_mapping.get(unit_str, unit_str)
        
    def _map_to_catmat(self, description: str) -> str:
        """Map item description to CATMAT/CATSER code"""
        if pd.isna(description):
            return 'UNKNOWN'
            
        description_lower = description.lower()
        
        # Simple keyword matching - in production, use ML or fuzzy matching
        for keyword, code in self.catmat_mapping.items():
            if keyword in description_lower:
                return code
                
        return 'UNKNOWN'
        
    async def _enrich_with_price_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich data with price statistics from external API"""
        logger.info("Enriching data with price statistics")
        
        # Group by CATMAT code and unit
        for catmat_code in df['catmat_code'].unique():
            if catmat_code != 'UNKNOWN':
                stats = await self._get_price_stats(catmat_code)
                if stats:
                    mask = df['catmat_code'] == catmat_code
                    df.loc[mask, 'price_mean'] = stats.get('mean', 0)
                    df.loc[mask, 'price_median'] = stats.get('median', 0)
                    df.loc[mask, 'price_std'] = stats.get('std', 0)
                    df.loc[mask, 'price_min'] = stats.get('min', 0)
                    df.loc[mask, 'price_max'] = stats.get('max', 0)
                    
        return df
        
    async def _get_price_stats(self, catmat_code: str) -> Optional[Dict[str, float]]:
        """Get price statistics for a CATMAT code"""
        if catmat_code in self.price_stats_cache:
            return self.price_stats_cache[catmat_code]
            
        try:
            # In production, this would query the real Preços panel API
            # For now, return mock data
            mock_stats = {
                'mean': 100.0,
                'median': 95.0,
                'std': 25.0,
                'min': 50.0,
                'max': 200.0
            }
            
            self.price_stats_cache[catmat_code] = mock_stats
            return mock_stats
            
        except Exception as e:
            logger.error(f"Error getting price stats for {catmat_code}: {str(e)}")
            return None
            
    def _detect_emergency(self, text: str) -> bool:
        """Detect emergency purchases/contracts"""
        if pd.isna(text):
            return False
            
        text_lower = text.lower()
        emergency_keywords = [
            'emergencial', 'urgente', 'emergência', 'urgencia',
            'calamidade', 'desastre', 'situação crítica'
        ]
        
        return any(keyword in text_lower for keyword in emergency_keywords)
        
    def _standardize_position(self, position: str) -> str:
        """Standardize position names"""
        if pd.isna(position):
            return 'UNKNOWN'
            
        position_lower = position.lower().strip()
        
        # Mapping common positions
        position_mapping = {
            'diretor': 'Diretor',
            'coordenador': 'Coordenador',
            'gerente': 'Gerente',
            'supervisor': 'Supervisor',
            'analista': 'Analista',
            'auxiliar': 'Auxiliar',
            'assistente': 'Assistente',
            'técnico': 'Técnico',
            'especialista': 'Especialista'
        }
        
        for key, value in position_mapping.items():
            if key in position_lower:
                return value
                
        return position.title()
        
    def _categorize_contract(self, description: str) -> str:
        """Categorize contract by description"""
        if pd.isna(description):
            return 'UNKNOWN'
            
        description_lower = description.lower()
        
        categories = {
            'consultoria': ['consultoria', 'consultor', 'assessoria'],
            'limpeza': ['limpeza', 'higienização', 'conservação'],
            'segurança': ['segurança', 'vigilância', 'monitoramento'],
            'tecnologia': ['sistema', 'software', 'tecnologia', 'informática'],
            'construção': ['obra', 'construção', 'reforma', 'manutenção'],
            'transporte': ['transporte', 'combustível', 'veículo'],
            'material': ['material', 'equipamento', 'suprimento']
        }
        
        for category, keywords in categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
                
        return 'outros'
        
    def _is_processed(self, file_path: Path) -> bool:
        """Check if file has been processed"""
        processed_marker = file_path.parent / f".processed_{file_path.stem}"
        return processed_marker.exists()
        
    def _mark_as_processed(self, file_path: Path) -> None:
        """Mark file as processed"""
        processed_marker = file_path.parent / f".processed_{file_path.stem}"
        processed_marker.touch()
        
    async def _save_processed_data(self, df: pd.DataFrame, original_path: Path, dataset_type: str) -> None:
        """Save processed data"""
        processed_file = original_path.parent / f"processed_{original_path.name}"
        df.to_parquet(processed_file, index=False)
        logger.info(f"Processed data saved to {processed_file}")
        
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = {
            'total_files': len(list(self.processed_data_path.glob("**/*.parquet"))),
            'processed_files': len(list(self.processed_data_path.glob("**/.processed_*"))),
            'cache_size': len(self.price_stats_cache),
            'last_update': datetime.now().isoformat()
        }
        return stats