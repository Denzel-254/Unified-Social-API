"""Platform adapters package."""

from app.adapters.base import BaseAdapter, PostResult, PlatformUser
from app.adapters.facebook import FacebookAdapter
from app.adapters.instagram import InstagramAdapter
from app.adapters.twitter import TwitterAdapter
from app.adapters.linkedin import LinkedInAdapter
from app.adapters.youtube import YouTubeAdapter
from app.adapters.whatsapp import WhatsAppAdapter

__all__ = [
    "BaseAdapter", 
    "PostResult", 
    "PlatformUser", 
    "FacebookAdapter", 
    "InstagramAdapter",
    "TwitterAdapter",
    "LinkedInAdapter",
    "YouTubeAdapter",
    "WhatsAppAdapter"
]