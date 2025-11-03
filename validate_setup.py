#!/usr/bin/env python3
"""
Setup Validation Script for IxOS Port Utilization Plotter

This script validates your Docker Compose setup before deployment.
"""

import os
import sys
import json
import subprocess

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠{Colors.END}  {text}")

def print_error(text):
    print(f"{Colors.RED}✗{Colors.END} {text}")

def check_docker():
    """Check if Docker is installed and running"""
    print_header("Checking Docker Installation")
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success(f"Docker installed: {result.stdout.strip()}")
        else:
            print_error("Docker is not installed!")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_error("Docker is not installed!")
        return False
    
    # Check Docker Compose
    try:
        result = subprocess.run(['docker', 'compose', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success(f"Docker Compose installed: {result.stdout.strip()}")
        else:
            # Try old docker-compose
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print_success(f"Docker Compose installed: {result.stdout.strip()}")
            else:
                print_error("Docker Compose is not installed!")
                return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_error("Docker Compose is not installed!")
        return False
    
    # Check Docker daemon
    try:
        result = subprocess.run(['docker', 'info'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success("Docker daemon is running")
        else:
            print_error("Docker daemon is not running!")
            return False
    except subprocess.TimeoutExpired:
        print_error("Docker daemon is not responding!")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and is properly configured"""
    print_header("Checking Environment Configuration")
    
    if not os.path.exists('.env'):
        print_error(".env file not found!")
        print_warning("Copy env.example to .env and configure it:")
        print(f"         cp env.example .env")
        return False
    
    print_success(".env file exists")
    
    # Read and validate .env
    issues = []
    with open('.env', 'r') as f:
        env_content = f.read()
        
        # Check for InfluxDB token
        if 'INFLUXDB_TOKEN=' in env_content:
            for line in env_content.split('\n'):
                if line.startswith('INFLUXDB_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    if token == 'your-super-secret-token-change-me':
                        issues.append("INFLUXDB_TOKEN still using default value - should be changed for security!")
                    else:
                        print_success("INFLUXDB_TOKEN configured")
                    break
        else:
            issues.append("INFLUXDB_TOKEN not defined")
    
    if issues:
        print_warning("Configuration issues found:")
        for issue in issues:
            print(f"         - {issue}")
        return False
    
    return True

def check_config_py():
    """Check if config.py is properly configured"""
    print_header("Checking IxOS Poller Configuration")
    
    if not os.path.exists('config.py'):
        print_error("config.py not found!")
        return False
    
    print_success("config.py exists")
    
    # Try to import and check configuration
    try:
        import config
        
        if not hasattr(config, 'CHASSIS_LIST'):
            print_error("CHASSIS_LIST not defined in config.py")
            return False
        
        chassis_list = config.CHASSIS_LIST
        if len(chassis_list) == 0:
            print_warning("CHASSIS_LIST is empty - no chassis configured!")
            return False
        else:
            print_success(f"Found {len(chassis_list)} chassis configured")
            for i, chassis in enumerate(chassis_list, 1):
                if 'ip' in chassis:
                    print(f"         {i}. {chassis['ip']}")
                else:
                    print_error(f"Chassis {i} missing 'ip' field")
                    return False
        
        # Check InfluxDB connection settings
        if hasattr(config, 'INFLUXDB_URL'):
            print_success(f"InfluxDB URL: {config.INFLUXDB_URL}")
        else:
            print_warning("INFLUXDB_URL not defined in config.py")
        
        return True
    except Exception as e:
        print_error(f"Error loading config.py: {e}")
        return False

def check_files():
    """Check if required files exist"""
    print_header("Checking Required Files")
    
    required_files = [
        'docker-compose.yml',
        'config.py',
        'portInfoPoller.py',
        'influxDBclient.py',
        'IxOSRestAPICaller.py',
        'prometheus.yml',
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print_success(f"{file} exists")
        else:
            print_error(f"{file} missing!")
            all_exist = False
    
    return all_exist

def check_ports():
    """Check if required ports are available"""
    print_header("Checking Port Availability")
    
    # Load ports from .env or use defaults
    influxdb_port = 8086
    grafana_port = 3000
    prometheus_port = 9090
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('INFLUXDB_PORT='):
                    influxdb_port = int(line.split('=')[1].strip())
                elif line.startswith('GRAFANA_PORT='):
                    grafana_port = int(line.split('=')[1].strip())
                elif line.startswith('PROMETHEUS_PORT='):
                    prometheus_port = int(line.split('=')[1].strip())
    
    ports = {
        influxdb_port: 'InfluxDB',
        grafana_port: 'Grafana',
        prometheus_port: 'Prometheus'
    }
    
    all_available = True
    for port, service in ports.items():
        try:
            # Try to get what's using the port
            result = subprocess.run(['lsof', '-i', f':{port}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.stdout and 'LISTEN' in result.stdout:
                print_warning(f"Port {port} ({service}) is already in use")
                print(f"         {result.stdout.strip()}")
                all_available = False
            else:
                print_success(f"Port {port} ({service}) is available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # lsof not available, skip check
            print_warning(f"Could not check port {port} ({service}) - lsof not available")
    
    return all_available

def main():
    """Main validation function"""
    print(f"\n{Colors.BLUE}╔{'═'*78}╗{Colors.END}")
    print(f"{Colors.BLUE}║{' '*20}IxOS Port Utilization Plotter{' '*29}║{Colors.END}")
    print(f"{Colors.BLUE}║{' '*25}Setup Validation{' '*36}║{Colors.END}")
    print(f"{Colors.BLUE}╚{'═'*78}╝{Colors.END}")
    
    checks = [
        ("Docker Installation", check_docker),
        ("Environment Configuration (.env)", check_env_file),
        ("IxOS Poller Configuration (config.py)", check_config_py),
        ("Required Files", check_files),
        ("Port Availability", check_ports),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_error(f"Error during {check_name}: {e}")
            results[check_name] = False
    
    # Summary
    print_header("Validation Summary")
    
    all_passed = all(results.values())
    
    for check_name, passed in results.items():
        if passed:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")
    
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    
    if all_passed:
        print(f"\n{Colors.GREEN}✓ All checks passed! You're ready to deploy.{Colors.END}")
        print(f"\n{Colors.BLUE}Next steps:{Colors.END}")
        print(f"  1. Start Docker services: {Colors.BLUE}./start.sh{Colors.END}")
        print(f"  2. Run IxOS poller:       {Colors.BLUE}python3 portInfoPoller.py{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠  Some checks failed. Please fix the issues above.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

