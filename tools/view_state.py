import json
from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
import time
from typing import Dict, Any

class StateViewer:
    def __init__(self, log_file: str = "debug_logs/state_log.jsonl"):
        self.log_file = Path(log_file)
        self.console = Console()
        
    def read_latest_states(self, n: int = 5) -> list:
        """Read the last n states from the log file"""
        if not self.log_file.exists():
            return []
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
            states = [json.loads(line) for line in lines[-n:]]
            return states
    
    def create_state_table(self, states: list) -> Table:
        """Create a rich table from states"""
        table = Table(title="Data State History")
        
        # Add columns
        table.add_column("Timestamp", style="cyan")
        table.add_column("Operation", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Shape", style="yellow")
        table.add_column("Memory (MB)", style="blue")
        
        # Add rows
        for state in states:
            table.add_row(
                state["timestamp"].split('T')[1],  # Just time
                state["operation"],
                state["status"],
                str(state.get("shape", "N/A")),
                f"{state.get('memory_mb', 0):.2f}" if state.get('memory_mb') else "N/A"
            )
        
        return table
    
    def create_column_info(self, state: Dict[str, Any]) -> Panel:
        """Create a panel with column information"""
        if "column_info" not in state:
            return Panel("No column information available")
        
        info_table = Table(title="Column Information")
        info_table.add_column("Column")
        info_table.add_column("Type")
        info_table.add_column("Null Count")
        info_table.add_column("Unique Count")
        
        for col, info in state["column_info"].items():
            info_table.add_row(
                col,
                info["dtype"],
                str(info["null_count"]),
                str(info["unique_count"])
            )
        
        return Panel(info_table)
    
    def create_numeric_stats(self, state: Dict[str, Any]) -> Panel:
        """Create a panel with numeric statistics"""
        if "numeric_stats" not in state:
            return Panel("No numeric statistics available")
        
        stats_table = Table(title="Numeric Statistics")
        stats_table.add_column("Column")
        stats_table.add_column("Mean")
        stats_table.add_column("Std")
        stats_table.add_column("Min")
        stats_table.add_column("Max")
        
        for col, stats in state["numeric_stats"].items():
            stats_table.add_row(
                col,
                f"{stats['mean']:.2f}",
                f"{stats['std']:.2f}",
                f"{stats['min']:.2f}",
                f"{stats['max']:.2f}"
            )
        
        return Panel(stats_table)
    
    def watch_state(self, refresh_rate: float = 2.0):
        """Watch the state in real-time"""
        try:
            with Live(auto_refresh=False) as live:
                while True:
                    states = self.read_latest_states()
                    if states:
                        latest_state = states[-1]
                        
                        # Create layout
                        state_table = self.create_state_table(states)
                        if latest_state["status"] == "active":
                            column_info = self.create_column_info(latest_state)
                            numeric_stats = self.create_numeric_stats(latest_state)
                            
                            # Update display
                            live.update(Panel.fit(
                                f"{state_table}\n\n{column_info}\n\n{numeric_stats}",
                                title="Data State Monitor",
                                border_style="blue"
                            ))
                        else:
                            live.update(state_table)
                    
                    live.refresh()
                    time.sleep(refresh_rate)
                    
        except KeyboardInterrupt:
            self.console.print("\nStopped state monitoring")

if __name__ == "__main__":
    viewer = StateViewer()
    viewer.watch_state() 