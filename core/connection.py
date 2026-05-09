from core.config import settings

GNS3_URL_VERS = f"http://{settings.GNS3_IP}:{settings.GNS3_PORT}/v2/version"
GNS3_URL_PRJ = f"http://{settings.GNS3_IP}:{settings.GNS3_PORT}/v2/projects/{settings.PROJECT_ID}"
GNS3_URL_LINKS = f"http://{settings.GNS3_IP}:{settings.GNS3_PORT}/v2/projects/{settings.PROJECT_ID}/links"
GNS3_URL_NODES = f"http://{settings.GNS3_IP}:{settings.GNS3_PORT}/v2/projects/{settings.PROJECT_ID}/nodes"