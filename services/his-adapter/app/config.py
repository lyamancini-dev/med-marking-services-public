import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./his_mock.db")
CONNECTOR_URL = os.getenv("CONNECTOR_URL", "http://gis-mt-connector:8000")
API_V1_PREFIX = "/api/v1"