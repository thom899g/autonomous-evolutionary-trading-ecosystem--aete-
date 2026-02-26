"""
Configuration management for AETE.
Handles environment variables, Firebase initialization, and global settings.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ExchangeConfig:
    """Exchange connection configuration"""
    name: str
    api_key: str = ""
    api_secret: str = ""
    sandbox: bool = True
    
    def validate(self) -> bool:
        """Validate exchange configuration"""
        if not self.name:
            logging.error("Exchange name required")
            return False
        if not self.sandbox and (not self.api_key or not self.api_secret):
            logging.warning(f"Live trading requires API keys for {self.name}")
        return True

@dataclass
class GAParams:
    """Genetic Algorithm parameters"""
    population_size: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elitism_count: int = 5
    max_generations: int = 100
    tournament_size: int = 3

@dataclass
class RLParams:
    """Reinforcement Learning parameters"""
    learning_rate: float = 0.001
    gamma: float = 0.99
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    memory_size: int = 10000
    batch_size: int = 64

class AETEConfig:
    """Main configuration manager"""
    
    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase_credentials.json")
        
        # Trading parameters
        self.exchange = ExchangeConfig(
            name=os.getenv("EXCHANGE_NAME", "binance"),
            api_key=os.getenv("EXCHANGE_API_KEY", ""),
            api_secret=os.getenv("EXCHANGE_API_SECRET", ""),
            sandbox=os.getenv("EXCHANGE_SANDBOX", "true").lower() == "true"
        )
        
        # Algorithm parameters
        self.ga_params = GAParams()
        self.rl_params = RLParams()
        
        # Risk management
        self.max_position_size = float(os.getenv("MAX_POSITION_SIZE", "0.1"))
        self.max_drawdown = float(os.getenv("MAX_DRAWDOWN", "0.2"))
        
        # Initialize logging
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Configure logging system"""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('aete.log')
            ]
        )
        logging.info("AETE logging initialized")
        
    def validate(self) -> bool:
        """Validate all configurations"""
        validations = [
            ("Exchange config", self.exchange.validate()),
            ("Firebase credentials", os.path.exists(self.firebase_credentials_path)),
        ]
        
        all_valid = True
        for name, result in validations:
            if not result:
                logging.error(f"Validation failed: {name}")
                all_valid = False
                
        return all_valid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for persistence"""
        return {
            "exchange": asdict(self.exchange),
            "ga_params": asdict(self.ga_params),
            "rl_params": asdict(self.rl_params),
            "risk_limits": {
                "max_position_size": self.max_position_size,
                "max_drawdown": self.max_drawdown
            }
        }

# Global configuration instance
config = AETEConfig()