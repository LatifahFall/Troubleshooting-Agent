# Tetra - Advanced Web Application Troubleshooting Agent

Tetra is an intelligent troubleshooting assistant developed to help identify, diagnose, and resolve errors or incidents affecting web applications. It systematically analyzes application logs and nginx server logs to provide actionable diagnosis and step-by-step troubleshooting instructions.

## 🚀 Features

- **Automated Log Analysis**: Automatically discovers and analyzes application and nginx log files
- **Intelligent Diagnosis**: Identifies specific errors, their root causes, and severity levels
- **Actionable Solutions**: Provides numbered, step-by-step troubleshooting instructions
- **Comprehensive Coverage**: Analyzes both application-level and server-level issues
- **Interactive Assistance**: Offers further help and clarification when needed
- **Dynamic Configuration**: Supports environment variables for custom log directory paths
- **JSON Response Format**: Structured output for easy parsing and integration

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Access to log files for analysis

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd troubleshooting-agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🏗️ Project Structure

```
Troubleshooting Agent/
├── main.py              # Main application entry point with OpenAI integration
├── utils.py             # Utility functions for log analysis and file operations
├── config.py            # Configuration management for log directories
├── system_prompt.j2     # Jinja2 template for dynamic system prompt generation
├── requirements.txt     # Python dependencies
├── README.md           # This documentation file
├── chemin/              # Sample log files directory
│   └── bis/
│       ├── access.log
│       ├── laravel.log
│       └── tetra.log
└── test/                # Test environment logs
    └── var/
        └── env/
            ├── app.log
            └── nginx_error.log
```

## 🚀 Usage

### Basic Usage

Run the troubleshooting agent:

```bash
python main.py
```

The agent follows a mandatory workflow:
1. **Application Log Analysis**: Searches for and analyzes application logs (database errors, code exceptions, etc.)
2. **Nginx Log Analysis**: Searches for and analyzes nginx server logs (404 errors, SSL issues, etc.)
3. **Diagnosis Generation**: Provides comprehensive diagnosis with severity levels and troubleshooting steps
4. **Further Assistance**: Offers additional help and clarification if needed
5. **Final Report**: Displays the complete diagnosis prominently with all troubleshooting instructions

### Directory Configuration

Tetra automatically searches for different types of logs in their typical locations with configurable paths:

**Application Logs** (Laravel, PHP, etc.):
1. **Environment Variable**: `APP_LOG_DIR` (if set)
2. **Common App Directories**: `./storage/logs`, `./logs`, etc. (if they exist)
3. **Current Directory**: `"."` (fallback)

**Nginx Logs** (Web server):
1. **Environment Variable**: `NGINX_LOG_DIR` (if set)
2. **Common Nginx Directories**: `/var/log/nginx`, `/var/log` (if they exist)
3. **Current Directory**: `"."` (fallback)

**Application Log Directory**:
1. **Environment Variable**: `APP_LOG_DIR` (if set)
2. **Common Log Directories**: `/var/log`, `/var/log/nginx`, etc. (if they exist)
3. **Current Directory**: `"."` (fallback)

**Examples:**
```bash
# Search in current directory (default)
python main.py

# Search app logs in specific directory
export APP_LOG_DIR="./storage/logs"
python main.py

# Search nginx logs in system directory
export NGINX_LOG_DIR="/var/log/nginx"
python main.py

# Search both types in different locations
export APP_LOG_DIR="./chemin"
export NGINX_LOG_DIR="/var/log"
python main.py

# Use custom general log directory
export TETRA_LOG_DIR="/var/log/myapp"
python main.py
```

### What the Agent Analyzes

**Application Logs**:
- Database connection errors
- Missing environment variables
- File permission issues
- Code exceptions and stack traces
- Missing controllers or classes
- Application configuration problems

**Nginx Logs**:
- 404 errors (missing files)
- SSL handshake failures
- Connection timeouts
- Server performance issues
- Access and error patterns

## 📊 Output Format

The agent provides diagnosis in a structured JSON format with severity levels and actionable steps:

```json
{
  "log_type": "diagnosis",
  "thoughts": "Internal reasoning about the analysis",
  "intent": "done_for_now",
  "args": {
    "message": "**DIAGNOSIS:**\n- [CRITICAL] Database connection timeout: MySQL connection failed after 30 seconds\n- [HIGH] Missing environment variable: APP_KEY not set\n- [MEDIUM] File permission error: Cannot write to storage/logs directory\n\n**TROUBLESHOOTING STEPS:**\n1. Check MySQL service: `sudo systemctl status mysql`\n2. Verify database credentials in .env file\n3. Generate APP_KEY: `php artisan key:generate`\n4. Fix storage permissions: `chmod -R 755 storage/`\n\n**CONTEXT:**\nThese errors prevent the application from running properly."
  }
}
```

**Severity Levels:**
- **CRITICAL**: Issues that completely prevent the application from running
- **HIGH**: Issues that cause major functionality problems
- **MEDIUM**: Issues that affect performance or cause warnings
- **WARNING**: Issues that may cause problems but don't immediately break functionality
- **LOW**: Minor issues or recommendations for improvement

## 🔧 Configuration

### System Prompt Customization

The agent's behavior is controlled by the `system_prompt.j2` template. You can modify:

- **Workflow**: Change the mandatory analysis sequence
- **Output Format**: Modify the diagnosis and troubleshooting format
- **Function Capabilities**: Add or remove available functions
- **Severity Levels**: Adjust how issues are prioritized

### Configuration Management

The `config.py` file manages log directory discovery with the following priorities:

1. **Environment Variables**: Highest priority for custom paths
2. **Common Directories**: Predefined paths for typical installations
3. **Current Directory**: Fallback option

### Log File Discovery

The agent automatically discovers log files by:
- Searching all subdirectories recursively
- Identifying files by extension (.log, .txt, .out, .err)
- Detecting log-like content patterns using regex
- Filtering by application-specific keywords
- Excluding web server logs when analyzing application logs

## 🛠️ Available Functions

### Core Functions
- `get_app_logs(root_path)`: Collects and analyzes application log files from the specified directory
- `get_nginx_logs(root_path)`: Collects and analyzes nginx log files from the specified directory
- `read_file(path)`: Reads specific file content for detailed analysis

### Directory Functions
- `get_app_working_directory()`: Gets the directory for application log analysis
- `get_nginx_working_directory()`: Gets the directory for nginx log analysis

### Interactive Functions
- `ask_for_clarification(message)`: Requests user input for clarification when needed
- `provide_further_assistance(message)`: Offers additional help after completing analysis
- `done_for_now(message)`: Completes analysis with comprehensive diagnosis and troubleshooting steps

**Function Requirements:**
- All functions require specific arguments as defined in the system prompt
- The `done_for_now` function must contain complete diagnosis and troubleshooting steps in the message field
- Functions are called in a specific sequence to ensure comprehensive analysis
- JSON response format is enforced for structured communication

## 🔍 Troubleshooting the Agent

### Common Issues

1. **No logs found**: Ensure log files are in the current directory or subdirectories
2. **API errors**: Verify your OpenAI API key is correct and has sufficient credits
3. **Permission errors**: Check file permissions for log files
4. **Memory issues**: Large log files may be skipped for performance
5. **JSON parsing errors**: Check that the system prompt generates valid JSON responses

### Debug Mode

The agent provides detailed output including:
- Internal reasoning in the `thoughts` field
- Function call results
- Complete analysis log in JSON format
- Iteration tracking to prevent infinite loops

### Error Handling

The agent includes comprehensive error handling for:
- File not found errors
- JSON parsing errors
- OpenAI API errors
- Validation errors for response models
- Memory management with message cleanup

## 📦 Dependencies

Key dependencies include:
- `openai==1.98.0`: OpenAI API client
- `pydantic==2.11.7`: Data validation and settings management
- `python-dotenv==1.1.1`: Environment variable management
- `jinja2`: Template engine for dynamic prompt generation
- `mypy==1.17.1`: Type checking support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with various log file types
5. Ensure JSON response format compliance
6. Submit a pull request

## 🙏 Acknowledgments

- Built with OpenAI GPT-4 for intelligent analysis
- Uses Jinja2 for dynamic prompt generation
- Pydantic for data validation and type safety
- Python for robust log processing and file operations
---

**Tetra** - Your intelligent web application troubleshooting companion! 🐛🔧
