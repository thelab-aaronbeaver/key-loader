# LightBurn UDP Communication Controller
# Based on: https://github.com/bunkford/lightburn_automation.git

import socket
import time
import json

class LightBurnController:
    """
    Controller for LightBurn automation via UDP.
    
    LightBurn uses UDP ports:
    - 19840 (outgoing from this app)
    - 19841 (incoming to this app)
    
    Supported commands:
    - START: Start the current job
    - STATUS: Get current status
    - PING: Test connection
    - CLOSE: Close LightBurn gracefully
    """
    
    def __init__(self, target_ip="127.0.0.1", out_port=19840, in_port=19841, timeout=2.0):
        """
        Initialize LightBurn controller.
        
        Args:
            target_ip: IP address of machine running LightBurn
            out_port: Port to send commands to (default 19840)
            in_port: Port to receive responses on (default 19841)
            timeout: Timeout for responses in seconds
        """
        self.target_ip = target_ip
        self.out_port = out_port
        self.in_port = in_port
        self.timeout = timeout
        self.sock = None
        
    def _create_socket(self):
        """Create UDP socket for communication."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(self.timeout)
            # Bind to incoming port to receive responses
            self.sock.bind(('', self.in_port))
            return True
        except Exception as e:
            print(f"❌ Failed to create socket: {e}")
            return False
    
    def _send_command(self, command):
        """
        Send a command to LightBurn and wait for response.
        
        Args:
            command: Command string to send
            
        Returns:
            Response string or None if failed
        """
        try:
            # Create fresh socket for each command
            if not self._create_socket():
                return None
            
            # Send command
            self.sock.sendto(command.encode('utf-8'), (self.target_ip, self.out_port))
            print(f"📡 Sent to LightBurn ({self.target_ip}:{self.out_port}): {command}")
            
            # Wait for response
            try:
                data, addr = self.sock.recvfrom(1024)
                response = data.decode('utf-8')
                print(f"📥 Response from LightBurn: {response}")
                return response
            except socket.timeout:
                print(f"⏱️  No response from LightBurn (timeout: {self.timeout}s)")
                return None
                
        except Exception as e:
            print(f"❌ Error sending command to LightBurn: {e}")
            return None
        finally:
            if self.sock:
                self.sock.close()
                self.sock = None
    
    def ping(self):
        """
        Test connection to LightBurn.
        
        Returns:
            True if LightBurn responds, False otherwise
        """
        response = self._send_command("PING")
        return response is not None
    
    def start_job(self):
        """
        Start the current job in LightBurn.
        
        Returns:
            True if command sent successfully, False otherwise
        """
        response = self._send_command("START")
        return response is not None
    
    def get_status(self):
        """
        Get current status from LightBurn.
        
        Returns:
            Dictionary with status information or None if failed
            Example: {"status": "idle"} or {"status": "running"}
        """
        response = self._send_command("STATUS")
        if response:
            try:
                # Try to parse as JSON if LightBurn returns structured data
                return json.loads(response)
            except (json.JSONDecodeError, ValueError):
                # If not JSON, return raw response
                return {"raw_response": response, "status": response.lower()}
        return None
    
    def is_busy(self):
        """
        Check if LightBurn is currently running a job.
        
        Returns:
            True if busy, False if idle, None if unable to determine
        """
        status = self.get_status()
        if status is None:
            return None
        
        # Check various status indicators
        status_str = str(status).lower()
        
        # LightBurn is busy if status contains these keywords
        busy_keywords = ['running', 'busy', 'active', 'working', 'processing']
        idle_keywords = ['idle', 'ready', 'waiting', 'stopped', 'finished', 'complete']
        
        for keyword in busy_keywords:
            if keyword in status_str:
                return True
        
        for keyword in idle_keywords:
            if keyword in status_str:
                return False
        
        # Unable to determine
        return None
    
    def wait_for_completion(self, poll_interval=0.5, max_wait=300):
        """
        Wait for LightBurn to complete the current job.
        
        Args:
            poll_interval: How often to check status (seconds)
            max_wait: Maximum time to wait (seconds)
            
        Returns:
            True if job completed, False if timeout or error
        """
        start_time = time.time()
        
        print(f"⏳ Waiting for LightBurn job completion (max {max_wait}s)...")
        
        while True:
            elapsed = time.time() - start_time
            
            # Check timeout
            if elapsed > max_wait:
                print(f"⏱️  Timeout waiting for LightBurn job completion ({max_wait}s)")
                return False
            
            # Check status
            is_busy = self.is_busy()
            
            if is_busy is None:
                # Unable to get status - LightBurn might be offline
                print(f"⚠️  Unable to get LightBurn status (elapsed: {elapsed:.1f}s)")
                time.sleep(poll_interval)
                continue
            
            if not is_busy:
                # Job complete
                print(f"✅ LightBurn job completed (elapsed: {elapsed:.1f}s)")
                return True
            
            # Still busy, wait and check again
            print(f"⏳ LightBurn busy... (elapsed: {elapsed:.1f}s)")
            time.sleep(poll_interval)
    
    def close(self):
        """
        Close LightBurn gracefully.
        
        Returns:
            True if command sent successfully, False otherwise
        """
        response = self._send_command("CLOSE")
        return response is not None
    
    def force_close(self):
        """
        Force close LightBurn.
        
        Returns:
            True if command sent successfully, False otherwise
        """
        response = self._send_command("FORCECLOSE")
        return response is not None


# Example usage
if __name__ == "__main__":
    # Test LightBurn connection
    lb = LightBurnController(target_ip="127.0.0.1")
    
    print("\n=== Testing LightBurn Connection ===")
    if lb.ping():
        print("✅ LightBurn is responding")
    else:
        print("❌ LightBurn is not responding")
    
    print("\n=== Getting Status ===")
    status = lb.get_status()
    print(f"Status: {status}")
    
    print("\n=== Checking if Busy ===")
    is_busy = lb.is_busy()
    print(f"Busy: {is_busy}")

