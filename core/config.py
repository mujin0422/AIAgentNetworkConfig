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

    DEFAULT_DEVICE_HOSTNAME=os.getenv("DEFAULT_DEVICE_HOSTNAME")
    DEFAULT_DEVICE_TYPE=os.getenv("DEFAULT_DEVICE_TYPE")
    DEFAULT_DEVICE_USERNAME=os.getenv("DEFAULT_DEVICE_USERNAME")
    DEFAULT_DEVICE_PORT=os.getenv("DEFAULT_DEVICE_PORT")
    DEFAULT_DEVICE_PASSWORD=os.getenv("DEFAULT_DEVICE_PASSWORD")

    NVIDIA_API_KEY=os.getenv("NVIDIA_API_KEY")

settings = Settings()