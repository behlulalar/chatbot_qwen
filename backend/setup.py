"""
Setup script - Creates necessary directories and checks dependencies.
"""
import sys
from pathlib import Path


def create_directories():
    """Create all necessary directories for the project."""
    directories = [
        "./data/raw_pdfs",
        "./data/processed_json",
        "./data/archive",
        "./data/chroma_db",
        "./logs",
    ]
    
    print("Creating directories...")
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ {dir_path}")


def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        print("\n⚠️ .env file not found!")
        if env_example.exists():
            print("📝 Please copy .env.example to .env and fill in your settings:")
            print("   cp .env.example .env")
        return False
    else:
        print("\n✅ .env file found")
        return True


def check_chromedriver():
    """Check if ChromeDriver is available."""
    import shutil
    
    chrome_path = shutil.which("chromedriver")
    if chrome_path:
        print(f"✅ ChromeDriver found: {chrome_path}")
        return True
    else:
        print("\n⚠️ ChromeDriver not found in PATH!")
        print("📥 Download ChromeDriver:")
        print("   https://chromedriver.chromium.org/downloads")
        print("   Or install via: brew install chromedriver (Mac)")
        return False


def check_postgresql():
    """Check if PostgreSQL is accessible."""
    try:
        import psycopg2
        print("✅ psycopg2 (PostgreSQL driver) installed")
        return True
    except ImportError:
        print("⚠️ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False


def main():
    print("=" * 60)
    print("SUBU CHATBOT - SETUP")
    print("=" * 60)
    
    # Create directories
    create_directories()
    
    # Check environment
    print("\n" + "=" * 60)
    print("Checking environment...")
    print("=" * 60)
    
    env_ok = check_env_file()
    chrome_ok = check_chromedriver()
    pg_ok = check_postgresql()
    
    # Summary
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    
    if env_ok and chrome_ok and pg_ok:
        print("✅ All checks passed! You're ready to go.")
        print("\nNext steps:")
        print("1. Edit .env file with your settings")
        print("2. Create PostgreSQL database: createdb subu_chatbot")
        print("3. Run test: python test_scraper.py")
    else:
        print("⚠️ Some checks failed. Please fix the issues above.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
