#!/usr/bin/env python3
"""
Project Health Check Script

Bu script projedeki tüm dosyaları kontrol eder ve sorunları raporlar.

Usage:
    python3 check_project.py
"""
import os
import sys
from pathlib import Path
import json

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text:^80}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def check_python_files():
    """Check Python files for syntax errors."""
    print_header("BACKEND - Python Files")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print_error("Backend directory not found!")
        return False
    
    errors = []
    success_count = 0
    
    # Check main Python files
    important_files = [
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/run_server.py",
        "backend/app/api/chat.py",
        "backend/app/api/documents.py",
        "backend/app/llm/response_generator.py",
        "backend/app/rag/vector_store.py",
    ]
    
    for file_path in important_files:
        if Path(file_path).exists():
            # Try to compile
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print_success(f"{file_path}")
                success_count += 1
            except SyntaxError as e:
                print_error(f"{file_path}: {e}")
                errors.append((file_path, str(e)))
        else:
            print_warning(f"{file_path} - File not found")
    
    print(f"\n{success_count}/{len(important_files)} Python files OK")
    return len(errors) == 0

def check_requirements():
    """Check if requirements.txt exists and is valid."""
    print_header("BACKEND - Dependencies")
    
    req_file = Path("backend/requirements.txt")
    if not req_file.exists():
        print_error("requirements.txt not found!")
        return False
    
    with open(req_file, 'r') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    
    print_info(f"Found {len(lines)} dependencies")
    
    # Check for important packages
    important_packages = [
        'fastapi', 'langchain', 'openai', 'chromadb', 
        'pydantic-settings', 'sqlalchemy', 'selenium'
    ]
    
    all_found = True
    for pkg in important_packages:
        found = any(pkg in line.lower() for line in lines)
        if found:
            print_success(f"{pkg}")
        else:
            print_error(f"{pkg} - Missing!")
            all_found = False
    
    return all_found

def check_env_file():
    """Check .env file."""
    print_header("BACKEND - Environment")
    
    env_example = Path("backend/.env.example")
    env_file = Path("backend/.env")
    
    if not env_example.exists():
        print_error(".env.example not found!")
        return False
    else:
        print_success(".env.example exists")
    
    if not env_file.exists():
        print_warning(".env not found! Copy from .env.example")
        print_info("Run: cp backend/.env.example backend/.env")
        return False
    else:
        print_success(".env exists")
        
        # Check for required keys
        with open(env_file, 'r') as f:
            content = f.read()
        
        required_keys = ['DATABASE_URL', 'OPENAI_API_KEY']
        for key in required_keys:
            if key in content:
                print_success(f"{key} defined")
            else:
                print_error(f"{key} missing!")
    
    return True

def check_frontend():
    """Check frontend files."""
    print_header("FRONTEND - React/TypeScript")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print_error("Frontend directory not found!")
        return False
    
    # Check package.json
    package_json = frontend_dir / "package.json"
    if package_json.exists():
        print_success("package.json exists")
        
        with open(package_json, 'r') as f:
            data = json.load(f)
            print_info(f"Project: {data.get('name', 'N/A')}")
            print_info(f"Version: {data.get('version', 'N/A')}")
    else:
        print_error("package.json not found!")
        return False
    
    # Check node_modules
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists():
        print_success("node_modules installed")
    else:
        print_warning("node_modules not found!")
        print_info("Run: cd frontend && npm install")
    
    # Check important source files
    important_files = [
        "frontend/src/App.tsx",
        "frontend/src/components/ChatInterface.tsx",
        "frontend/src/components/ChatMessage.tsx",
        "frontend/src/components/Sidebar.tsx",
    ]
    
    all_exist = True
    for file_path in important_files:
        if Path(file_path).exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} - Missing!")
            all_exist = False
    
    return all_exist

def check_data_directories():
    """Check data directories."""
    print_header("DATA - Directories & Files")
    
    dirs = [
        "backend/data/raw_pdfs",
        "backend/data/processed_json",
        "backend/data/chroma_db",
        "backend/data/archive",
        "backend/logs",
    ]
    
    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists():
            if dir_path.startswith("backend/data"):
                files = list(path.glob("*"))
                print_success(f"{dir_path} ({len(files)} files)")
            else:
                print_success(f"{dir_path}")
        else:
            print_warning(f"{dir_path} - Not found")
            print_info(f"Run: mkdir -p {dir_path}")
    
    return True

def check_documentation():
    """Check documentation files."""
    print_header("DOCUMENTATION")
    
    docs = [
        "README.md",
        "START.md",
        "DEPLOYMENT_WINDOWS.md",
        "DEVELOPMENT.md",
        "frontend/README.md",
        "REACT_SETUP.md",
    ]
    
    for doc in docs:
        if Path(doc).exists():
            print_success(f"{doc}")
        else:
            print_warning(f"{doc} - Missing")
    
    return True

def main():
    """Main check function."""
    print_header("SUBU MEVZUAT CHATBOT - PROJECT HEALTH CHECK")
    
    results = {
        "Python Files": check_python_files(),
        "Dependencies": check_requirements(),
        "Environment": check_env_file(),
        "Frontend": check_frontend(),
        "Data Directories": check_data_directories(),
        "Documentation": check_documentation(),
    }
    
    # Summary
    print_header("SUMMARY")
    
    all_ok = True
    for check, passed in results.items():
        if passed:
            print_success(f"{check}: OK")
        else:
            print_error(f"{check}: FAILED")
            all_ok = False
    
    if all_ok:
        print(f"\n{GREEN}{'🎉 ' * 20}{RESET}")
        print(f"{GREEN}ALL CHECKS PASSED! Project is ready to run!{RESET}")
        print(f"{GREEN}{'🎉 ' * 20}{RESET}\n")
        
        print_info("Next steps:")
        print("  1. cd backend && source venv/bin/activate")
        print("  2. python run_server.py")
        print("  3. Open new terminal: cd frontend && npm start")
    else:
        print(f"\n{RED}Some checks failed. Please fix the issues above.{RESET}\n")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
