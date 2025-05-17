"""
Security patterns for Cylestio Monitor.

This module provides centralized patterns for security detection.
"""

from typing import List, Dict, Pattern
import re


# Compiled patterns cache
_COMPILED_PATTERNS: Dict[str, List[Pattern]] = {}


def get_suspicious_shell_patterns() -> List[str]:
    """
    Get regex patterns for suspicious shell usage.

    Returns:
        List of regex patterns for suspicious shell activities
    """
    return [
        # Command chaining
        r'(;|\|\||&&|\|)\s*\w+',
        # Input/output redirection
        r'(>\s*[\w\/\.]+|>>\s*[\w\/\.]+|<\s*[\w\/\.]+)',
        # Command substitution
        r'`.*`|\$\(.*\)',
        # Suspicious commands in shell context
        r'\b(curl|wget|nc|ncat|netcat)\b.*\b(download|http|ftp|tcp)\b',
        # File operations in sensitive locations
        r'\b(touch|cat|echo)\b.*\b(/etc/|/tmp/|/var/|C:\\Windows\\|%TEMP%)\b',
        # Suspicious network activities
        r'\b(curl|wget|nc)\b.*\b([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|http://|https://)\b',
        # Obfuscation attempts
        r'(\$[A-Za-z0-9_]+\s*=.*;\s*\$[A-Za-z0-9_]+)',
        r'(base64|hex|eval|exec)\b'
    ]


def get_shell_access_network_patterns() -> List[Dict[str, str]]:
    """
    Get patterns for detecting shell access in network traffic.
    
    These patterns are designed to identify shell access characteristics in 
    network traffic without relying on hardcoded indicators like specific URLs or ports.
    
    Returns:
        List of dictionaries containing pattern information with 'regex' and 'description' keys
    """
    return [
        # Shell prompt patterns
        {
            "regex": r"(\$|#|>)\s+(ls|pwd|whoami|id|echo|cat|ps|mkdir|cd)\s",
            "description": "Shell command prompt detected in traffic"
        },
        # Shell response patterns
        {
            "regex": r"uid=\d+\(\w+\)\s+gid=\d+\(\w+\)",
            "description": "Shell id/whoami command response detected"
        },
        {
            "regex": r"(total\s+\d+\s*\n[-d][-rwx]{9}\s+\d+\s+\w+\s+\w+)",
            "description": "Directory listing response detected"
        },
        # TTY control sequences
        {
            "regex": r"\x1b\[\d+[mABCDHJKhu]",
            "description": "Terminal control sequences detected in traffic"
        },
        # Interactive shell upgrade attempts
        {
            "regex": r"(python\s+-c\s+['\"](import pty; pty\.spawn\(|import tty|exec pty\.spawn)|stty raw -echo|script -q|socat)",
            "description": "Interactive shell/TTY upgrade attempt detected"
        },
        # Command sequences indicative of post-exploitation
        {
            "regex": r"(uname -a|cat /etc/(passwd|shadow|issue|os-release)|cat /proc/version|hostnamectl|systeminfo|ver\b)",
            "description": "System information gathering commands detected"
        },
        # Binary data transfer indicators
        {
            "regex": r"(base64 [-d]|xxd|hexdump|openssl|dd if=)",
            "description": "Binary data transfer/encoding detected"
        },
        # Reverse shell connection patterns
        {
            "regex": r"(sh|bash|cmd|powershell|python|perl|ruby|php)\s+(-[ec]|--exec|-i)\s",
            "description": "Reverse shell execution pattern detected"
        },
        # Linux command history pattern
        {
            "regex": r"(\d+\s+\w+.*\n\d+\s+\w+.*\n\d+\s+\w+)",
            "description": "Command history output detected"
        },
        # Interactive shell session identifiers
        {
            "regex": r"(sh-\d+\.\d+[$#>]|bash-\d+\.\d+[$#>]|Microsoft Windows \[.*\]|Copyright \(c\) \d+ Microsoft Corporation)",
            "description": "Shell session banner detected"
        },
        # MCP to shell transition indicators
        {
            "regex": r"(Special username trigger detected|Switching to Shell Command mode|ATTACK MODE ACTIVATED|FORMAT: \"[^\"]+\"\?)",
            "description": "MCP to shell transition pattern detected"
        },
        # Command execution in shell after transition
        {
            "regex": r"(All queries are now being executed as shell commands|/bin/sh: [^:]+: command not found)",
            "description": "Shell command execution after MCP transition detected"
        },
        # HTTP-based command injection patterns
        {
            "regex": r"what is the email of ([a-zA-Z0-9_\-\.]+)\?",
            "description": "Potential HTTP-based command injection pattern detected"
        }
    ]


def get_mcp_shell_transition_patterns() -> List[Dict[str, str]]:
    """
    Get patterns for detecting transitions from MCP (Model-Code-Protocol) to shell execution.
    
    These patterns are designed to identify when legitimate interfaces like database
    connectors are exploited to gain shell access.
    
    Returns:
        List of dictionaries containing pattern information with 'regex' and 'description' keys
    """
    return [
        # MCP shell activation trigger phrases
        {
            "regex": r"SWITCH_TO_SHELL_MODE|enable-shell|SHELL_ACCESS_REQUEST",
            "description": "MCP shell mode activation trigger detected"
        },
        # Mode transition messaging
        {
            "regex": r"(Switching|Switched) to [Ss]hell [Cc]ommand mode",
            "description": "Shell command mode transition detected"
        },
        # Attack success indicators
        {
            "regex": r"ATTACK MODE ACTIVATED|VICTIM HAS BEEN COMPROMISED",
            "description": "Successful attack mode activation detected"
        },
        # Shell instruction patterns (custom command format instructions)
        {
            "regex": r"Format: \"[^\"]+\"\?|All queries are now being executed as|executed as shell commands",
            "description": "Shell command execution instructions detected"
        },
        # Command disguise patterns
        {
            "regex": r"what is the (email|password|username|account) of ([^?]+)\?",
            "description": "Disguised shell command pattern detected"
        },
        # Command responses in HTTP traffic
        {
            "regex": r"/bin/sh: [^:]+: command not found",
            "description": "Shell command error response detected"
        },
        # Common command outputs
        {
            "regex": r"README\.md\s+__pycache__\s+\w+\.py",
            "description": "Directory listing command output detected"
        }
    ]


def get_context_switching_patterns() -> List[str]:
    """
    Get regex patterns for context switching attempts between
    database/application contexts and execution environments.

    Returns:
        List of regex patterns for context switching attempts
    """
    return [
        # Generic patterns for enabling special modes
        r'(?i)enable[_\s]*(shell|command|exec|system)',
        r'(?i)(activate|trigger|switch[_\s]*to)[_\s]*(shell|command|exec|system)',
        r'(?i)(mode|context)[_\s]*=[_\s]*(shell|command|exec|true|1)',
        # Function calls that might indicate mode changing
        r'(?i)(set|change|modify)[_\s]*(mode|context|environment|privilege)',
        # Patterns that could be used to evade simple string matching
        r'(?i)([a-z_]+_){2,}(mode|shell|command|exec|context)',
        r'(?i)(s\s*h\s*e\s*l\s*l|c\s*o\s*m\s*m\s*a\s*n\s*d|e\s*x\s*e\s*c)',
        # Database to shell transition indicators
        r'(?i)(exec|system|shell)[_\s]*(command|call|function)',
        # Generic keywords that might be used in variable names
        r'(?i)(cmd|shell|os|sys|exec)[_\s]*(access|enabled|mode)',
        # Boolean flags that might be used to control execution contexts
        r'(?i)(is|allow|enable)[_\s]*(shell|command|exec)[_\s]*(access|mode)'
    ]


def get_dangerous_commands() -> List[str]:
    """
    Get list of dangerous commands that might indicate malicious activity.

    Returns:
        List of dangerous command strings
    """
    return [
        # Network exfiltration commands
        "curl", "wget", "nc", "netcat", "ncat", "telnet", "scp", "sftp", "ftp",

        # System manipulation commands
        "chmod", "chown", "chattr", "usermod", "visudo", "mkfs", "dd",

        # Remote access commands
        "ssh", "ssh-keygen", "sshd", "rsh", "rexec", "vnc", "rdp",

        # File destructive commands
        "shred", "rm -rf", "rmdir", "srm",

        # Command execution
        "nohup", "xargs", "at", "crontab", "watch",

        # Payload downloads
        "pip install", "npm install", "gem install", "apt-get", "apt install", "yum install",

        # Dangerous scripting tools
        "perl -e", "python -c", "ruby -e", "php -r", "node -e", "bash -c",

        # Reverse shells
        "bash -i", "perl -e 'use Socket'", "/dev/tcp/", "python -c 'import socket'",

        # Memory dumping/inspection
        "memdump", "hexdump", "strings", "gcore", "ptrace", "strace", "ltrace",

        # Persistence mechanisms
        "iptables", "systemctl", "selinux", "firewall-cmd", "launchctl", "netsh",

        # Reconnaissance commands
        "nmap", "masscan", "nikto", "gobuster", "dirb", "dirbuster", "enum4linux",

        # Rootkit/malware tools
        "rootkit", "keylogger", "mimikatz", "metasploit", "msfvenom"
    ]


def get_suspicious_directories() -> List[str]:
    """
    Get list of suspicious directories commonly used in attacks.

    Returns:
        List of suspicious directory paths
    """
    return [
        # Unix temporary directories
        "/tmp", "/dev/shm", "/var/tmp", "/run/user", "/run/shm", "/var/run",
        "/proc/self/fd", "/proc/self/maps", "/proc/self/mem",

        # Web server writeable directories
        "/var/www/html/uploads", "/var/www/tmp", "/srv/www",

        # Windows temporary directories
        "\\temp", "\\tmp", "\\appdata\\local\\temp", "\\users\\public",
        "\\programdata\\temp", "\\windows\\temp", "\\windows\\system32\\config\\systemprofile\\appdata\\local\\temp",

        # Others
        "/.git", "/.svn", "/.aws", "/.ssh", "/.gnupg",
        "/mnt/c/windows/temp"  # WSL access to Windows
    ]


def get_privilege_escalation_commands() -> List[str]:
    """
    Get list of commands commonly used for privilege escalation.

    Returns:
        List of privilege escalation command strings
    """
    return [
        # Unix privilege escalation commands
        "sudo", "su ", "pkexec", "doas", "gksudo", "kdesudo", "setuid", "setgid",
        "chown root", "chmod u+s", "chmod +s", "polkit", "pkcon",

        # Windows privilege escalation
        "runas", "psexec", "nssm", "sc", "at job", "schtasks", "reg add",

        # Exploits
        "CVE-", "pwn", "exploit", "dirty_cow", "dirtycow", "linpeas", "linEnum"
    ]


def get_sql_injection_patterns() -> List[str]:
    """
    Get regex patterns for SQL injection attempts.

    Returns:
        List of regex patterns for SQL injection attempts
    """
    return [
        # Common SQLi patterns
        r"('|\")\s*(OR|AND)\s*('|\")\s*=\s*('|\")",
        r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER)",
        r"UNION\s+(ALL\s+)?SELECT",
        r"--\s+",
        r"#\s*$",
        r"/\*.*\*/",

        # More advanced SQLi
        r"SLEEP\s*\(\s*\d+\s*\)",
        r"BENCHMARK\s*\(",
        r"WAITFOR\s+DELAY",
        r"INFORMATION_SCHEMA",
        r"LOAD_FILE\s*\(",
        r"INTO\s+OUTFILE",
        r"DUMPFILE",

        # SQL to shell transition patterns
        r"(?i)(EXEC|EXECUTE|CALL|SYSTEM_EXEC|XP_CMDSHELL)(\s*\(|\s+)",
        r"(?i)(os\.|sys\.|dbms_).*\.(exec|shell|command|system)",

        # NoSQL injection
        r"\{\s*\$where\s*:\s*",
        r"\$ne\s*:",
        r"\$gt\s*:",
        r"\$or\s*:"
    ]
