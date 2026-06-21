import psutil
import time
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    LOGGER_WARNING("GPUtil not available. GPU monitoring will be disabled. Install with: pip install GPUtil", "YELLOW")

class ProcessHandler:
    def __init__(self):
        pass

    def get_pid_by_name(self, process_name= "CiscoCollabHost.exe"):
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] == process_name:
                        return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return None
        
    def get_all_pids_by_name(self, process_name="CiscoCollabHost.exe"):
        """
        Return a list of all PIDs for the given process name.
        """
        pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == process_name:
                    pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return pids

    def get_cisco_collab_pid_info(self):
        """
        Returns a dict with main process pid (Hosted=True), media process pid (media), and all pids for CiscoCollabHost.exe.
        """
        pids = self.get_all_pids_by_name("CiscoCollabHost.exe")
        main_pid = None
        media_pid = None

        for pid in pids:
            try:
                proc = psutil.Process(pid)
                cmdline = " ".join(proc.cmdline())
                if "Hosted" in cmdline:
                    main_pid = pid
                if "media" in cmdline.lower():
                    media_pid = pid
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return {
            "main_pid": main_pid,
            "media_pid": media_pid,
            "all_pids": pids
        }

    def get_pid_cpu_memory(self, pid):
        """
        Returns a dict with cpu_percent (like Task Manager) and memory_info (in MB) for the given PID.
        """
        try:
            proc = psutil.Process(pid)
            proc.cpu_percent(interval=None)  
            cpu_raw = proc.cpu_percent(interval=1.0)
            # Normalize CPU percentage to match Task Manager display
            # This accounts for multi-core systems where psutil returns total across all cores
            cpu_count = psutil.cpu_count(logical=True)
            if cpu_count and cpu_count > 0:
                cpu_normalized = cpu_raw / cpu_count
            else:
                cpu_normalized = cpu_raw  # Fallback if cpu_count is None or 0
            mem = proc.memory_info().rss / (1024 * 1024)  
            return {
                "pid": pid,
                "cpu": round(cpu_normalized, 2),  # Use normalized CPU value
                "mem": round(mem, 2)  
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
    
    def get_gpu_usage(self):
        """
        Get GPU usage information. Returns the highest GPU usage percentage.
        """
        if not GPU_AVAILABLE:
            return 0.0
            
        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                return 0.0
                
            # Get the maximum GPU usage across all GPUs
            max_gpu_usage = 0.0
            for gpu in gpus:
                if gpu.load is not None:
                    gpu_usage_percent = gpu.load * 100  # GPUtil returns load as 0-1, convert to percentage
                    max_gpu_usage = max(max_gpu_usage, gpu_usage_percent)
                    
            return round(max_gpu_usage, 2)
            
        except Exception as e:
            LOGGER_DEBUG(f"Error getting GPU usage: {e}", "YELLOW")
            return 0.0
    
    def get_pid_cpu_memory_gpu(self, pid):
        """
        Returns a dict with cpu_percent, memory_info (in MB), and GPU usage for the given PID.
        """
        if pid is None:
            return None
            
        try:
            proc = psutil.Process(pid)
            proc.cpu_percent(interval=None)  
            cpu_raw = proc.cpu_percent(interval=1.0)
            # Normalize CPU percentage to match Task Manager display
            # This accounts for multi-core systems where psutil returns total across all cores
            cpu_count = psutil.cpu_count(logical=True)
            if cpu_count and cpu_count > 0:
                cpu_normalized = cpu_raw / cpu_count
            else:
                cpu_normalized = cpu_raw  # Fallback if cpu_count is None or 0
                
            mem = proc.memory_info().rss / (1024 * 1024)
            gpu_usage = self.get_gpu_usage()  # Get system-wide GPU usage
            
            return {
                "pid": pid,
                "cpu": round(cpu_normalized, 2),  # Use normalized CPU value
                "mem": round(mem, 2),
                "gpu": gpu_usage  # GPU usage as percentage
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        
    def extract_pid_performance_meta(self, main_meta, media_meta):
        def get_val(meta, key):
            return meta.get(key, None) if meta is not None else None
        return (
            get_val(main_meta, 'cpu'),
            get_val(main_meta, 'mem'),
            get_val(media_meta, 'cpu'),
            get_val(media_meta, 'mem'),
            get_val(main_meta, 'gpu')  # Add GPU from main process
        )
    
    def get_performance_cisco_collab_pid_meta(self):
        pid_info = self.get_cisco_collab_pid_info()
        main_pid = pid_info.get('main_pid', None)
        media_pid = pid_info.get('media_pid', None)
        main_meta = self.get_pid_cpu_memory_gpu(main_pid)  # Use GPU-enabled method
        media_meta = self.get_pid_cpu_memory_gpu(media_pid)  # Use GPU-enabled method
        return self.extract_pid_performance_meta(main_meta, media_meta)
    
    def wait_for_main_pid(self, max_wait_time=30):
        """
        Wait for getting Webex main process PID, retry every 1 second if empty
        Args:
            max_wait_time: Maximum wait time in seconds
        Returns:
            int: Main process PID, or None if timeout
        """
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            pid_info = self.get_cisco_collab_pid_info()
            main_pid = pid_info.get('main_pid')
            
            if main_pid is not None:
                LOGGER_INFO(f"Successfully obtained Webex main process PID: {main_pid}", "GREEN")
                return main_pid
            
            LOGGER_INFO("Waiting for Webex main process PID...", "YELLOW")
            time.sleep(1)
        
        LOGGER_INFO(f"Timeout ({max_wait_time}s) failed to obtain Webex main process PID", "RED")
        return None