"""
Nova 2 Sonic - Voice AI for SafeBite
Real-time speech synthesis for accessibility
"""

import boto3
import json
import logging
import base64
from typing import Optional

logger = logging.getLogger(__name__)


class NovaSonicVoice:
    """
    Amazon Nova 2 Sonic integration for voice synthesis
    Provides accessible audio summaries of allergen analysis
    """
    
    def __init__(self):
        """Initialize Bedrock client for Nova 2 Sonic"""
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            # Nova 2 Sonic model ID
            self.model_id = 'us.amazon.nova-sonic-v1:0'
            self.polly = boto3.client('polly', region_name='us-east-1')
            logger.info("Nova Sonic Voice initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Nova Sonic: {e}")
            self.bedrock = None
            self.polly = None
    
    async def generate_safety_audio(
        self,
        safe_count: int,
        caution_count: int,
        unsafe_count: int,
        detected_allergens: list,
        top_safe_dish: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate audio summary of menu analysis results
        
        Returns:
            Base64 encoded audio data (MP3)
        """
        # Build natural language summary
        summary = self._build_voice_summary(
            safe_count, caution_count, unsafe_count,
            detected_allergens, top_safe_dish
        )
        
        try:
            # Try Nova 2 Sonic first for natural voice
            audio_data = await self._synthesize_with_nova_sonic(summary)
            if audio_data:
                return audio_data
            
            # Fallback to Amazon Polly
            return await self._synthesize_with_polly(summary)
            
        except Exception as e:
            logger.error(f"Voice synthesis failed: {e}")
            return None
    
    def _build_voice_summary(
        self,
        safe_count: int,
        caution_count: int,
        unsafe_count: int,
        detected_allergens: list,
        top_safe_dish: Optional[str]
    ) -> str:
        """Build natural language summary for voice output"""
        
        total = safe_count + caution_count + unsafe_count
        
        # Opening
        if unsafe_count == 0 and caution_count == 0:
            opening = f"Great news! All {total} dishes on this menu appear safe for you."
        elif unsafe_count > 0:
            opening = f"Attention! I found {unsafe_count} dishes you should avoid."
        else:
            opening = f"I've analyzed {total} dishes on this menu."
        
        # Details
        details = []
        if safe_count > 0:
            details.append(f"{safe_count} dishes are safe to eat")
        if caution_count > 0:
            details.append(f"{caution_count} dishes need caution")
        if unsafe_count > 0:
            details.append(f"{unsafe_count} dishes contain your allergens")
        
        details_text = ", ".join(details) + "."
        
        # Allergen warning
        allergen_warning = ""
        if detected_allergens:
            unique_allergens = list(set(detected_allergens))[:3]
            allergen_warning = f" Watch out for {', '.join(unique_allergens)}."
        
        # Recommendation
        recommendation = ""
        if top_safe_dish:
            recommendation = f" I recommend trying the {top_safe_dish}."
        
        # Closing
        closing = " Always confirm with restaurant staff before ordering."
        
        return f"{opening} {details_text}{allergen_warning}{recommendation}{closing}"
    
    async def _synthesize_with_nova_sonic(self, text: str) -> Optional[str]:
        """
        Synthesize speech using Nova 2 Sonic
        Returns base64 encoded audio
        """
        if not self.bedrock:
            return None
            
        try:
            logger.info("Synthesizing with Nova 2 Sonic...")
            
            # Nova 2 Sonic request format
            request_body = {
                "text": text,
                "voice": {
                    "language": "en-US",
                    "gender": "female",
                    "style": "conversational"
                },
                "audioConfig": {
                    "format": "mp3",
                    "sampleRate": 24000
                }
            }
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='audio/mpeg',
                body=json.dumps(request_body)
            )
            
            # Read audio bytes
            audio_bytes = response['body'].read()
            
            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            logger.info("Nova 2 Sonic synthesis successful")
            return audio_base64
            
        except Exception as e:
            logger.warning(f"Nova 2 Sonic synthesis failed, falling back to Polly: {e}")
            return None
    
    async def _synthesize_with_polly(self, text: str) -> Optional[str]:
        """
        Fallback: Synthesize speech using Amazon Polly
        Returns base64 encoded audio
        """
        if not self.polly:
            return None
            
        try:
            logger.info("Synthesizing with Amazon Polly...")
            
            response = self.polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId='Joanna',  # Natural female voice
                Engine='neural'    # Neural engine for better quality
            )
            
            # Read audio stream
            audio_bytes = response['AudioStream'].read()
            
            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            logger.info("Polly synthesis successful")
            return audio_base64
            
        except Exception as e:
            logger.error(f"Polly synthesis failed: {e}")
            return None
    
    async def generate_dish_warning(self, dish_name: str, allergens: list) -> Optional[str]:
        """
        Generate quick audio warning for a specific dish
        """
        if not allergens:
            text = f"The {dish_name} appears safe for you."
        else:
            allergen_list = ", ".join(allergens)
            text = f"Warning! The {dish_name} contains {allergen_list}. Do not order this dish."
        
        return await self._synthesize_with_polly(text)
    
    async def generate_emergency_alert(self, dish_name: str, allergen: str) -> Optional[str]:
        """
        Generate urgent audio alert for severe allergen detection
        """
        text = f"Alert! {dish_name} contains {allergen}. This is a severe allergen for you. Do not consume this dish under any circumstances."
        
        return await self._synthesize_with_polly(text)
