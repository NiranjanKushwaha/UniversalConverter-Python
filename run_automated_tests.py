#!/usr/bin/env python3
"""
Automated Test Runner
Sets up test files and runs comprehensive conversion tests
"""

import os
import sys
import asyncio
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'python-multipart', 'requests', 
        'pandas', 'Pillow', 'python-docx', 'openpyxl', 'reportlab',
        'PyMuPDF', 'python-pptx', 'beautifulsoup4'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_api_server():
    """Check if the API server is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print("❌ API server is not responding correctly")
            return False
    except Exception as e:
        print("❌ API server is not running")
        print(f"   Error: {e}")
        print("\nStart the API server with:")
        print("uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False

def setup_test_files():
    """Set up test files for testing"""
    print("\n📁 Setting up test files...")
    
    try:
        from test_files_setup import TestFilesGenerator
        generator = TestFilesGenerator()
        files = generator.generate_all_test_files()
        print(f"✅ Created {len(files)} test files")
        return True
    except Exception as e:
        print(f"❌ Failed to create test files: {e}")
        return False

def run_automated_tests():
    """Run the automated test suite"""
    print("\n🧪 Running automated test suite...")
    
    try:
        from automated_test_suite import ConversionTestSuite
        
        # Create test suite
        test_suite = ConversionTestSuite()
        
        # Run tests
        start_time = time.time()
        report = asyncio.run(test_suite.run_full_test_suite())
        end_time = time.time()
        
        if report:
            print(f"\n✅ Test suite completed in {end_time - start_time:.2f} seconds")
            return True
        else:
            print("❌ Test suite failed")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run test suite: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Universal File Converter - Automated Test Suite")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check API server
    if not check_api_server():
        sys.exit(1)
    
    # Setup test files
    if not setup_test_files():
        sys.exit(1)
    
    # Run tests
    if not run_automated_tests():
        sys.exit(1)
    
    print("\n🎉 All tests completed successfully!")
    print("\n📊 Check the following files for results:")
    print("   - test_outputs/test_report_*.json (Detailed results)")
    print("   - test_outputs/test_summary_*.csv (CSV summary)")
    print("   - test_outputs/test_report_*.html (HTML report)")
    
    print("\n📁 Test files are in: test_files/")
    print("📁 Output files are in: test_outputs/")

if __name__ == "__main__":
    main() 