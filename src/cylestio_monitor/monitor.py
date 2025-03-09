"""Cylestio Monitor core module.

This module provides a framework-agnostic monitoring solution for AI agents.
It supports dynamic patching of different frameworks and collects monitoring data
in a standardized format.
"""

import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime
from pathlib import Path

from .events_processor import events_processor, log_event
from .events_listener import EventsListener
from .auto_detect import detect_frameworks
from .patchers.base import BasePatcher

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Monitor:
    """Main monitoring class for Cylestio Monitor.
    
    This class provides monitoring capabilities for AI agents, regardless of the
    framework or implementation they use. It automatically detects and monitors
    available frameworks.
    """
    
    def __init__(self):
        """Initialize monitor."""
        self.output_file = None
        self.config = {}
        self.events_listener = EventsListener()
        self.is_running = False
        self.patchers = []
        self.logger = logging.getLogger("CylestioMonitor")
        
    def register_patcher(self, patcher: BasePatcher) -> None:
        """Register a patcher.
        
        Args:
            patcher: Patcher instance to register
        """
        if not isinstance(patcher, BasePatcher):
            raise TypeError("Patcher must be an instance of BasePatcher")
        self.patchers.append(patcher)
        
    def start(
        self,
        output_file: str = "cylestio_monitoring.json",
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Start monitoring.
        
        This method:
        1. Sets up monitoring configuration
        2. Auto-detects available frameworks
        3. Starts monitoring components
        
        Args:
            output_file: Path to JSON output file for monitoring data
            config: Optional configuration dictionary
        """
        if self.is_running:
            return
            
        self.output_file = Path(output_file)
        self.config = config or {}
        
        # Set up logging
        file_handler = logging.FileHandler(f"{self.output_file.stem}.log")
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
        
        # Auto-detect frameworks if no patchers registered
        if not self.patchers:
            self.patchers = detect_frameworks()
        
        self.is_running = True
        
        # Log start event
        log_event(
            "monitoring_start",
            {
                "timestamp": datetime.now().isoformat(),
                "output_file": str(self.output_file),
                "config": self.config,
                "detected_frameworks": [
                    p.__class__.__name__ for p in self.patchers
                ]
            },
            "SYSTEM"
        )
        
        # Apply all patchers
        for patcher in self.patchers:
            try:
                patcher.patch()
            except Exception as e:
                self.logger.error(f"Failed to apply patcher {patcher.__class__.__name__}: {e}")
                
        # Start components
        events_processor.start()
        self.events_listener.start()
        
    def stop(self) -> None:
        """Stop monitoring.
        
        This method:
        1. Stops collecting monitoring data
        2. Removes all patches
        3. Saves final monitoring data to output file
        """
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Remove all patches
        for patcher in reversed(self.patchers):
            try:
                patcher.unpatch()
            except Exception as e:
                self.logger.error(f"Failed to remove patcher {patcher.__class__.__name__}: {e}")
                
        # Stop components
        events_processor.stop()
        self.events_listener.stop()
        
        # Save monitoring data
        self._save_monitoring_data()
        
        # Log stop event
        log_event(
            "monitoring_stop",
            {
                "timestamp": datetime.now().isoformat()
            },
            "SYSTEM"
        )
        
    def _save_monitoring_data(self) -> None:
        """Save monitoring data to output file."""
        if not self.output_file:
            return
            
        data = {
            "metadata": {
                "version": "0.1.0",
                "timestamp": datetime.now().isoformat(),
                "config": self.config
            },
            "monitoring": self.get_summary()
        }
        
        with open(self.output_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary."""
        return {
            "status": {
                "running": self.is_running,
                "output_file": str(self.output_file) if self.output_file else None,
                "patchers": [p.__class__.__name__ for p in self.patchers]
            },
            "events": events_processor.get_summary()
        }

def init_monitoring(
    output_file: str = "cylestio_monitoring.json",
    config: Optional[Dict[str, Any]] = None,
    patchers: Optional[List[BasePatcher]] = None
) -> Monitor:
    """Initialize and start monitoring.
    
    This is the main entry point for using Cylestio Monitor.
    
    Args:
        output_file: Path to JSON output file for monitoring data
        config: Optional configuration dictionary
        patchers: Optional list of patchers to register
        
    Returns:
        Monitor instance
        
    Example:
        ```python
        from cylestio_monitor import init_monitoring
        from cylestio_monitor.patchers import MCPPatcher, AnthropicPatcher
        
        # Initialize monitoring with specific patchers
        monitor = init_monitoring(
            output_file="agent_monitoring.json",
            patchers=[
                MCPPatcher(),
                AnthropicPatcher(client=anthropic_client)
            ]
        )
        
        # Your agent code here...
        
        # Stop monitoring when done
        monitor.stop()
        ```
    """
    monitor = Monitor()
    
    # Register patchers if provided
    if patchers:
        for patcher in patchers:
            monitor.register_patcher(patcher)
            
    # Start monitoring
    monitor.start(output_file=output_file, config=config)
    
    return monitor