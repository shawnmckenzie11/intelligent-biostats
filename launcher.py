import sys
import os
import time
import logging
import webbrowser
import threading
import requests
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt
import subprocess
import signal

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class IntelligentBiostatsApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Initialize variables
        self.server_process = None
        self.port = None
        self.browser_opened = False
        
        # Create system tray icon
        self.setup_tray()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def setup_tray(self):
        """Set up the system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon()
        # Use a default icon for now
        self.tray_icon.setIcon(self.app.style().standardIcon(self.app.style().SP_ComputerIcon))
        
        # Create tray menu
        menu = QMenu()
        
        # Add menu items
        open_action = menu.addAction("Open Application")
        open_action.triggered.connect(self.open_browser)
        
        menu.addSeparator()
        
        restart_action = menu.addAction("Restart Server")
        restart_action.triggered.connect(self.restart_server)
        
        menu.addSeparator()
        
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip("Intelligent Biostats")
        self.tray_icon.show()
        
        # Show notification
        self.tray_icon.showMessage(
            "Intelligent Biostats",
            "Application is starting...",
            QSystemTrayIcon.Information,
            2000
        )
    
    def find_free_port(self, start_port=5000, max_attempts=100):
        """Find an available port starting from start_port."""
        import socket
        from contextlib import closing
        
        for port in range(start_port, start_port + max_attempts):
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                try:
                    sock.bind(('0.0.0.0', port))
                    logger.info(f"Found available port: {port}")
                    return port
                except socket.error as e:
                    logger.debug(f"Port {port} is in use: {str(e)}")
                    continue
        raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")
    
    def start_server(self):
        """Start the Flask server in a separate process."""
        try:
            # Find available port
            self.port = self.find_free_port()
            os.environ['FLASK_RUN_PORT'] = str(self.port)
            
            # Start the server process
            self.server_process = subprocess.Popen(
                [sys.executable, 'run.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Start monitoring the server
            self.monitor_server()
            
        except Exception as e:
            logger.error(f"Error starting server: {str(e)}")
            self.show_error("Failed to start server", str(e))
    
    def monitor_server(self):
        """Monitor the server process and wait for it to be ready."""
        def check_server():
            max_attempts = 30
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    response = requests.get(f'http://localhost:{self.port}/')
                    if response.status_code == 200:
                        logger.info("Server is ready")
                        self.tray_icon.showMessage(
                            "Intelligent Biostats",
                            f"Server is running on port {self.port}",
                            QSystemTrayIcon.Information,
                            2000
                        )
                        if not self.browser_opened:
                            self.open_browser()
                        return
                except requests.exceptions.ConnectionError:
                    pass
                
                attempt += 1
                logger.debug(f"Waiting for server to start... (attempt {attempt}/{max_attempts})")
                time.sleep(1)
            
            self.show_error("Server Timeout", "Could not connect to the server")
        
        # Start monitoring in a separate thread
        threading.Thread(target=check_server, daemon=True).start()
    
    def open_browser(self):
        """Open the default web browser to the application URL."""
        if self.port:
            url = f'http://localhost:{self.port}'
            webbrowser.open(url)
            self.browser_opened = True
    
    def restart_server(self):
        """Restart the Flask server."""
        self.stop_server()
        time.sleep(1)  # Wait for port to be released
        self.start_server()
    
    def stop_server(self):
        """Stop the Flask server."""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
    
    def show_error(self, title, message):
        """Show an error message to the user."""
        QMessageBox.critical(None, title, message)
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutting down...")
        self.quit_application()
    
    def quit_application(self):
        """Clean up and quit the application."""
        self.stop_server()
        self.tray_icon.hide()
        self.app.quit()
    
    def run(self):
        """Run the application."""
        try:
            # Start the server
            self.start_server()
            
            # Run the Qt event loop
            return self.app.exec_()
            
        except Exception as e:
            logger.error(f"Error running application: {str(e)}")
            self.show_error("Application Error", str(e))
            return 1

if __name__ == '__main__':
    app = IntelligentBiostatsApp()
    sys.exit(app.run()) 