import os

class Config:
    
    # Application log dirs
    APP_LOG_DIRS = [
        './storage/logs',        # Laravel logs
        './logs',               # Custom app logs
        './chemin'              # current sample directory
    ]
    
    # Nginx log dirs
    NGINX_LOG_DIRS = [
        '/var/log/nginx',       # Standard nginx location
        '/var/log'              # System logs (includes nginx)
    ]
    
    @classmethod
    def get_app_log_directory(cls) -> str:
        """
        Get the directory to search for application logs.
        Priority: ENV variable > common app dirs > current dir
        """
        # 1. Environment variable (priority plus haute)
        env_log_dir = os.getenv('APP_LOG_DIR')
        if env_log_dir and os.path.exists(env_log_dir):
            return env_log_dir
        
        # 2. Check common app log directories
        for log_dir in cls.APP_LOG_DIRS:
            if os.path.exists(log_dir):
                return log_dir
        
        # 3. Fallback to current directory
        return "."
    
    @classmethod
    def get_nginx_log_directory(cls) -> str:
        """
        Get the directory to search for nginx logs.
        Priority: ENV variable > common nginx dirs > current dir
        """
        # 1. Environment variable (highest priority)
        env_log_dir = os.getenv('NGINX_LOG_DIR')
        if env_log_dir and os.path.exists(env_log_dir):
            return env_log_dir
        
        # 2. Check common nginx log directories
        for log_dir in cls.NGINX_LOG_DIRS:
            if os.path.exists(log_dir):
                return log_dir
        
        # 3. Fallback to current directory
        return "."
