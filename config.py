"""
Configuration file for MCP Server
"""

import os

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Server configuration
    HOST = '0.0.0.0'
    PORT = 8000

    # CORS settings
    CORS_ORIGINS = ["*"]  # Allow all in development
    CORS_METHODS = ["GET", "POST", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    CORS_SUPPORTS_CREDENTIALS = False
    CORS_MAX_AGE = 3600


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CORS_ORIGINS = ["*"]  # Allow all origins in development


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

    # In production, specify exact domains
    CORS_ORIGINS = [
        "https://your-frontend-domain.com",
        "https://your-ai-agent-domain.com",
        # Add more allowed origins here
    ]

    # More restrictive in production
    CORS_SUPPORTS_CREDENTIALS = True  # If you need cookies/auth


class DockerConfig(Config):
    """Docker configuration"""
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 8000))

    # Get allowed origins from environment variable
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])