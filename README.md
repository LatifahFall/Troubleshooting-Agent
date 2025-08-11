# Tetra - Advanced Web Application Troubleshooting Agent

Tetra is an intelligent troubleshooting assistant developed to help identify, diagnose, and resolve errors or incidents affecting web applications. It systematically analyzes application logs and nginx server logs to provide actionable diagnosis and step-by-step troubleshooting instructions.

## 🚀 Features

- **Automated Log Analysis**: Automatically discovers and analyzes application and nginx log files
- **Intelligent Diagnosis**: Identifies specific errors, their root causes, and severity levels
- **Actionable Solutions**: Provides numbered, step-by-step troubleshooting instructions
- **Comprehensive Coverage**: Analyzes both application-level and server-level issues
- **Interactive Assistance**: Offers further help and clarification when needed

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
├── main.py              # Main application entry point
├── utils.py             # Utility functions for log analysis
├── system_prompt.j2     # Jinja2 template for system prompt
├── requirements.txt     # Python dependencies
└── chemin/              # Sample log files directory
    └── bis/
        ├── access.log
        ├── laravel.log
        └── tetra.log
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

The agent provides diagnosis in a structured format with severity levels and actionable steps:

```
**DIAGNOSIS:**
- [CRITICAL] Database connection timeout: MySQL connection failed after 30 seconds
- [HIGH] Missing environment variable: APP_KEY not set
- [MEDIUM] File permission error: Cannot write to storage/logs directory

**TROUBLESHOOTING STEPS:**
1. Check MySQL service: `sudo systemctl status mysql`
2. Verify database credentials in .env file
3. Generate APP_KEY: `php artisan key:generate`
4. Fix storage permissions: `chmod -R 755 storage/`

**CONTEXT:**
These errors prevent the application from running properly.
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

### Log File Discovery

The agent automatically discovers log files by:
- Searching all subdirectories recursively
- Identifying files by extension (.log, .txt, .out, .err)
- Detecting log-like content patterns
- Filtering by application-specific keywords

## 🛠️ Available Functions

- `get_app_logs(root_path)`: Collects and analyzes application log files from the specified directory
- `get_nginx_logs(root_path)`: Collects and analyzes nginx log files from the specified directory
- `read_file(path)`: Reads specific file content for detailed analysis
- `ask_for_clarification(message)`: Requests user input for clarification when needed
- `provide_further_assistance(message)`: Offers additional help after completing analysis
- `done_for_now(message)`: Completes analysis with comprehensive diagnosis and troubleshooting steps

**Function Requirements:**
- All functions require specific arguments as defined in the system prompt
- The `done_for_now` function must contain complete diagnosis and troubleshooting steps in the message field
- Functions are called in a specific sequence to ensure comprehensive analysis

## 🔍 Troubleshooting the Agent

### Common Issues

1. **No logs found**: Ensure log files are in the current directory or subdirectories
2. **API errors**: Verify your OpenAI API key is correct and has sufficient credits
3. **Permission errors**: Check file permissions for log files
4. **Memory issues**: Large log files may be skipped for performance

### Debug Mode

The agent provides detailed output including:
- Internal reasoning in the `thoughts` field
- Function call results
- Complete analysis log in JSON format

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🙏 Acknowledgments

- Built with OpenAI GPT-4 for intelligent analysis
- Uses Jinja2 for dynamic prompt generation
- Pydantic for data validation
- Python for robust log processing

## 📞 Support

For issues, questions, or contributions, please:
1. Check the troubleshooting section above
2. Review the system prompt configuration
3. Ensure your log files are accessible
4. Verify your OpenAI API key is valid

---

**Tetra** - Your intelligent web application troubleshooting companion! 🐛🔧
