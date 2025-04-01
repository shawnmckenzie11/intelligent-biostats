class Config:
    """Base configuration."""
    DEBUG = False
    TESTING = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    pass

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
