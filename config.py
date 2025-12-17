import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bu-cok-gizli-bir-anahtardir-nexus-projesi-2025'