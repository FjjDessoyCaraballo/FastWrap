import os

# Set environment variables BEFORE any imports that load config
# This ensures tests connect to localhost instead of Docker service names
os.environ['REDIS_HOST'] = 'localhost'
os.environ['DATABASE_URL'] = 'postgresql://fdessoy:supersecret@localhost:5432/fastwrap_db'
