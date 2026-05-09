from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    GNS3_IP=os.getenv("GNS3_IP")
    GNS3_PORT=os.getenv("GNS3_PORT")
    PROJECT_ID=os.getenv("PROJECT_ID")

    SSH_TIMEOUT=int(os.getenv("SSH_TIMEOUT"))
    SSH_AUTH_TIMEOUT=int(os.getenv("SSH_AUTH_TIMEOUT"))
    SSH_DELAY_FACTOR=float(os.getenv("SSH_DELAY_FACTOR"))
    SSH_KEEPALIVE=int(os.getenv("SSH_KEEPALIVE"))
    
settings = Settings()