import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app
port = int(os.environ.get('PORT', 7555))
print("=" * 50)
print(f"  Server starting on http://127.0.0.1:{port}")
print("  Username: admin")
print("  Password: admin123")
print("=" * 50)
app.run(debug=False, host='0.0.0.0', port=port)
