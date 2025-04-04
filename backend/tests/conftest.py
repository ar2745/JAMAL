import os
import sys
from pathlib import Path

import pytest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def setup_test_directories():
    """Create test directories if they don't exist"""
    directories = ['documents', 'links', 'chats', 'uploads']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    yield
    # Cleanup after tests
    for directory in directories:
        for file in Path(directory).glob('*'):
            file.unlink() 
