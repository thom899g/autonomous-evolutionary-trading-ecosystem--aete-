"""
Firebase Firestore client for AETE state persistence.
Handles strategy storage, performance metrics, and ecosystem state.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud.firestore_v1.base_query import FieldFilter

from config import config

class FirebaseClient:
    """Firebase Firestore client for AETE"""
    
    def __init__(self):
        """Initialize Firebase connection"""
        self.db: Optional[FirestoreClient] = None
        self._initialized = False
        self._initialize_firebase()
        
    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(config.firebase_credentials_path)
                firebase_admin.initialize_app(cred)
                logging.info("Firebase Admin SDK initialized")
            
            self.db = firestore.client()
            self._initialized = True
            logging.info("Firestore client connected")
            
        except Exception as e:
            logging.error(f"Firebase initialization failed: {e}")
            self._initialized = False
            raise
    
    def is_connected(self) -> bool:
        """Check if Firebase is connected"""
        return self._initialized and self.db is not None
    
    # --- Strategy Management ---
    
    def save_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]) -> bool:
        """Save strategy to Firestore"""
        if not self.is_connected():
            logging.error("Firebase not connected")
            return False
            
        try:
            strategy_ref = self.db.collection("strategies").document(strategy_id)
            strategy_data["updated_at"] = firestore.SERVER_TIMESTAMP
            strategy_data["version"] = strategy_data.get("version", 1)
            
            strategy_ref.set(strategy_data, merge=True)
            logging.info(f"Strategy {strategy_id} saved to Firestore")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save strategy {strategy_id}: {e}")
            return False
    
    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve strategy from Firestore"""
        if not self.is_connected():
            return None
            
        try:
            doc_ref = self.db.collection("strategies").document(strategy_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                logging.warning(f"Strategy {strategy_id} not found")
                return None
                
        except Exception as e:
            logging.error(f"Failed to retrieve strategy {strategy_id}: {e}")
            return None
    
    # --- Performance Metrics ---
    
    def log_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Log trade execution to Firestore"""
        if not self.is_connected():
            return False
            
        try:
            # Add metadata
            trade_data["logged_at"] = firestore.SERVER_TIMESTAMP
            trade_data["ecosystem_version"] = "aete_v1"
            
            # Store in trades collection
            trades_ref = self.db.collection("trades")
            trades_ref.add(trade_data)
            
            # Update strategy performance
            strategy_id = trade_data.get("strategy_id")
            if strategy_id:
                self._update_strategy_performance(strategy_id, trade_data)
            
            logging.debug(f