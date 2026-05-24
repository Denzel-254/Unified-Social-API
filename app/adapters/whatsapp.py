"""WhatsApp Business Cloud API adapter."""

import httpx
from typing import Dict, Optional
from datetime import datetime
from app.adapters.base import BaseAdapter, PostResult, PlatformUser
from app.core.mock_oauth import is_mock_mode


class WhatsAppAdapter(BaseAdapter):
    """Adapter for WhatsApp Business Cloud API."""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, access_token: str, phone_number_id: str):
        """
        Initialize WhatsApp adapter.
        
        Args:
            access_token: Facebook/WhatsApp access token
            phone_number_id: WhatsApp Business phone number ID
        """
        super().__init__(access_token, "whatsapp")
        self.phone_number_id = phone_number_id
    
    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> PostResult:
        """
        Send a WhatsApp message.
        
        WhatsApp supports:
        - Text messages
        - Images, videos, documents
        - Message templates (for business)
        """
        
        # Mock mode for testing
        if is_mock_mode():
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=f"mock_wa_message_{hash(content) % 10000}",
                posted_at=datetime.utcnow(),
                raw_response={
                    "messages": [{"id": f"mock_wa_message_{hash(content) % 10000}"}]
                }
            )
        
        # Real API call
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Note: In production, you'd need the recipient's phone number
                # This is a simplified version
                if media_url and media_type:
                    # Send media message
                    data = {
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": "recipient_number",  # Would come from request
                        "type": media_type,
                        media_type: {
                            "link": media_url,
                            "caption": content[:100] if media_type == "image" else None
                        }
                    }
                else:
                    # Send text message
                    data = {
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": "recipient_number",  # Would come from request
                        "type": "text",
                        "text": {"preview_url": False, "body": content[:4096]}
                    }
                
                response = await client.post(
                    f"{self.BASE_URL}/{self.phone_number_id}/messages",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                result = response.json()
                
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=result.get("messages", [{}])[0].get("id"),
                    posted_at=datetime.utcnow(),
                    raw_response=result
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response else str(e)
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"WhatsApp API error: {error_detail}"
            )
        except Exception as e:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def send_template(
        self,
        template_name: str,
        language: str = "en_US",
        components: Optional[list] = None
    ) -> PostResult:
        """
        Send a templated WhatsApp message (for business approval).
        
        Args:
            template_name: Name of approved template
            language: Language code (en_US, es_ES, etc.)
            components: Template components (header, body, buttons)
        """
        
        if is_mock_mode():
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=f"mock_template_{template_name}",
                posted_at=datetime.utcnow(),
                raw_response={"template": template_name, "status": "sent"}
            )
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": "recipient_number",
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {"code": language},
                        "components": components or []
                    }
                }
                
                response = await client.post(
                    f"{self.BASE_URL}/{self.phone_number_id}/messages",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                result = response.json()
                
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=result.get("messages", [{}])[0].get("id"),
                    posted_at=datetime.utcnow(),
                    raw_response=result
                )
        except Exception as e:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Failed to send template: {str(e)}"
            )
    
    async def get_user_info(self) -> PlatformUser:
        """Get WhatsApp Business account info."""
        
        if is_mock_mode():
            return PlatformUser(
                platform_user_id="mock_whatsapp_44444",
                name="Mock WhatsApp Business",
                username="+1234567890",
                email="mock_whatsapp@example.com"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                response = await client.get(
                    f"{self.BASE_URL}/{self.phone_number_id}",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                return PlatformUser(
                    platform_user_id=data.get("id"),
                    name=data.get("display_phone_number"),
                    username=data.get("display_phone_number"),
                    email="whatsapp_business@business.com"
                )
        except Exception as e:
            print(f"Error getting WhatsApp account: {e}")
            return PlatformUser(
                platform_user_id="unknown",
                name="Unknown Business"
            )
    
    async def check_rate_limit(self) -> Dict:
        """Check WhatsApp rate limits."""
        
        if is_mock_mode():
            return {
                "remaining": 75,
                "limit": 80,
                "reset_time": datetime.utcnow().timestamp() + 3600
            }
        
        return {"remaining": "check Meta Developer Portal", "limit": 80}