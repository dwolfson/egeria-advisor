"""
MLflow tracking integration for Egeria Advisor.

This module provides utilities for tracking experiments, metrics, and artifacts
using MLflow for observability and performance monitoring.
"""

import mlflow
from mlflow.tracking import MlflowClient
from typing import Dict, Any, Optional
from loguru import logger
from contextlib import contextmanager
import time

from advisor.config import settings


class MLflowTracker:
    """MLflow tracking wrapper for Egeria Advisor."""
    
    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: Optional[str] = None
    ):
        """
        Initialize MLflow tracker.
        
        Args:
            tracking_uri: MLflow tracking server URI
            experiment_name: Name of the experiment
        """
        self.tracking_uri = tracking_uri or settings.mlflow_tracking_uri
        self.experiment_name = experiment_name or settings.mlflow_experiment_name
        self.enabled = settings.mlflow_enable_tracking
        
        if not self.enabled:
            logger.info("MLflow tracking is disabled")
            return
        
        # Set tracking URI
        mlflow.set_tracking_uri(self.tracking_uri)
        logger.info(f"MLflow tracking URI: {self.tracking_uri}")
        
        # Set or create experiment
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(self.experiment_name)
                logger.info(f"Created MLflow experiment: {self.experiment_name} (ID: {experiment_id})")
            else:
                experiment_id = experiment.experiment_id
                logger.info(f"Using existing MLflow experiment: {self.experiment_name} (ID: {experiment_id})")
            
            mlflow.set_experiment(self.experiment_name)
            
        except Exception as e:
            logger.warning(f"Failed to set up MLflow experiment: {e}")
            self.enabled = False
    
    @contextmanager
    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        """
        Context manager for MLflow runs.
        
        Args:
            run_name: Name for the run
            tags: Tags to add to the run
            
        Yields:
            MLflow run object
        """
        if not self.enabled:
            yield None
            return
        
        try:
            with mlflow.start_run(run_name=run_name, tags=tags) as run:
                logger.info(f"Started MLflow run: {run.info.run_id}")
                yield run
        except Exception as e:
            logger.error(f"MLflow run failed: {e}")
            yield None
    
    def log_params(self, params: Dict[str, Any]):
        """Log parameters to MLflow."""
        if not self.enabled:
            return
        
        try:
            mlflow.log_params(params)
            logger.debug(f"Logged {len(params)} parameters to MLflow")
        except Exception as e:
            logger.warning(f"Failed to log parameters: {e}")
    
    @contextmanager
    def track_operation(
        self,
        operation_name: str,
        params: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Context manager for tracking an operation with MLflow.
        
        Args:
            operation_name: Name of the operation
            params: Parameters to log
            tags: Tags to add
            
        Yields:
            Tracker object with log_metrics method
        """
        if not self.enabled:
            # Return a dummy tracker that does nothing
            class DummyTracker:
                def log_metrics(self, metrics: Dict[str, float]):
                    pass
            yield DummyTracker()
            return
        
        start_time = time.time()
        
        try:
            with self.start_run(run_name=operation_name, tags=tags) as run:
                if params:
                    self.log_params(params)
                
                # Create a tracker object that can log metrics
                class OperationTracker:
                    def __init__(self, parent):
                        self.parent = parent
                    
                    def log_metrics(self, metrics: Dict[str, float]):
                        self.parent.log_metrics(metrics)
                
                yield OperationTracker(self)
                
                # Log duration
                duration = time.time() - start_time
                self.log_metrics({"operation_duration_seconds": duration})
                
        except Exception as e:
            logger.error(f"Error tracking operation {operation_name}: {e}")
            class DummyTracker:
                def log_metrics(self, metrics: Dict[str, float]):
                    pass
            yield DummyTracker()
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics to MLflow."""
        if not self.enabled:
            return
        
        try:
            mlflow.log_metrics(metrics, step=step)
            logger.debug(f"Logged {len(metrics)} metrics to MLflow")
        except Exception as e:
            logger.warning(f"Failed to log metrics: {e}")
    
    def log_metric(self, key: str, value: float, step: Optional[int] = None):
        """Log a single metric to MLflow."""
        if not self.enabled:
            return
        
        try:
            mlflow.log_metric(key, value, step=step)
        except Exception as e:
            logger.warning(f"Failed to log metric {key}: {e}")
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """Log an artifact to MLflow."""
        if not self.enabled:
            return
        
        try:
            mlflow.log_artifact(local_path, artifact_path)
            logger.debug(f"Logged artifact: {local_path}")
        except Exception as e:
            logger.warning(f"Failed to log artifact: {e}")
    
    def log_dict(self, dictionary: Dict[str, Any], artifact_file: str):
        """Log a dictionary as a JSON artifact."""
        if not self.enabled:
            return
        
        try:
            mlflow.log_dict(dictionary, artifact_file)
            logger.debug(f"Logged dictionary as {artifact_file}")
        except Exception as e:
            logger.warning(f"Failed to log dictionary: {e}")
    
    def set_tags(self, tags: Dict[str, str]):
        """Set tags for the current run."""
        if not self.enabled:
            return
        
        try:
            mlflow.set_tags(tags)
            logger.debug(f"Set {len(tags)} tags")
        except Exception as e:
            logger.warning(f"Failed to set tags: {e}")


# Global tracker instance
_mlflow_tracker: Optional[MLflowTracker] = None


def get_mlflow_tracker() -> MLflowTracker:
    """Get or create the global MLflow tracker instance."""
    global _mlflow_tracker
    
    if _mlflow_tracker is None:
        _mlflow_tracker = MLflowTracker()
    
    return _mlflow_tracker


@contextmanager
def track_operation(
    operation_name: str,
    params: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None
):
    """
    Context manager to track an operation with MLflow.
    
    Args:
        operation_name: Name of the operation
        params: Parameters to log
        tags: Tags to add
        
    Yields:
        Tracker object with log_metric method
    """
    tracker = get_mlflow_tracker()
    
    start_time = time.time()
    
    with tracker.start_run(run_name=operation_name, tags=tags) as run:
        if run and params:
            tracker.log_params(params)
        
        # Create a simple object to hold metrics during the operation
        class MetricsLogger:
            def log_metric(self, key: str, value: float):
                tracker.log_metric(key, value)
            
            def log_metrics(self, metrics: Dict[str, float]):
                tracker.log_metrics(metrics)
        
        metrics_logger = MetricsLogger()
        
        try:
            yield metrics_logger
        finally:
            # Log duration
            duration = time.time() - start_time
            tracker.log_metric("duration_seconds", duration)
            logger.info(f"Operation '{operation_name}' completed in {duration:.2f}s")