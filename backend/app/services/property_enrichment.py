"""
Property Enrichment Service using Gemini AI

This service analyzes property images and descriptions using Gemini to generate
rich, searchable descriptions that improve matching with user queries.
"""

import google.generativeai as genai
import requests
from typing import Dict, List, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class PropertyEnrichmentService:
    """Service to enrich property descriptions using Gemini AI"""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("PropertyEnrichmentService: Gemini initialized")
        else:
            self.client = None
            logger.warning("PropertyEnrichmentService: No GEMINI_API_KEY found")

    def enrich_property_description(
        self,
        property_data: Dict,
        image_urls: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Generate enriched property description using Gemini.

        Args:
            property_data: Dictionary with property details (title, description, address, etc.)
            image_urls: Optional list of image URLs to analyze

        Returns:
            Dictionary with 'enriched_description' and 'search_keywords'
        """
        if not self.client:
            logger.warning("Gemini client not available, returning original data")
            return {
                'enriched_description': property_data.get('description', ''),
                'search_keywords': []
            }

        try:
            # Build analysis prompt
            prompt = self._build_enrichment_prompt(property_data)

            # If images available, analyze first image
            if image_urls and len(image_urls) > 0:
                return self._enrich_with_image(prompt, image_urls[0])
            else:
                return self._enrich_text_only(prompt)

        except Exception as e:
            logger.error(f"Error enriching property: {e}")
            return {
                'enriched_description': property_data.get('description', ''),
                'search_keywords': []
            }

    def _build_enrichment_prompt(self, property_data: Dict) -> str:
        """Build the prompt for Gemini to enrich property description."""
        title = property_data.get('title', '')
        description = property_data.get('description', '')
        address = property_data.get('address', '')
        prop_type = property_data.get('property_type', 'apartment')
        bedrooms = property_data.get('bedrooms', '')
        bathrooms = property_data.get('bathrooms', '')
        price = property_data.get('price', '')
        amenities = property_data.get('api_amenities', [])

        # Truncate inputs to prevent token overflow
        amenities_text = ', '.join(amenities[:5]) if amenities else 'None listed'
        desc_snippet = description[:150] if description else 'No description'

        prompt = f"""Write a real estate listing for this property.

{bedrooms}BR/{bathrooms}BA {prop_type} - ${price}/mo
{address}
Amenities: {amenities_text}
Info: {desc_snippet}

Create a 100-150 word description emphasizing location, features, and lifestyle. Extract 5-7 searchable keywords (parking, laundry, modern, spacious, quiet, etc.).
"""
        return prompt

    def _enrich_text_only(self, prompt: str) -> Dict[str, str]:
        """Enrich using text-only analysis."""
        try:
            response = self.client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=600,  # Reduced - 100-150 words + keywords fits in ~400-500 tokens
                    response_mime_type="application/json",  # Force JSON output
                    response_schema={
                        "type": "object",
                        "properties": {
                            "enriched_description": {
                                "type": "string",
                                "description": "100-150 word property description"
                            },
                            "search_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Array of 5-7 searchable keywords"
                            }
                        },
                        "required": ["enriched_description", "search_keywords"]
                    }
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )

            # Check if response was blocked
            if not response.candidates or len(response.candidates) == 0:
                logger.warning("Gemini returned no candidates")
                return {'enriched_description': '', 'search_keywords': []}

            candidate = response.candidates[0]

            # Check finish_reason (0=UNSPECIFIED, 1=STOP (success), 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION, 5=OTHER)
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason != 1:
                reason_map = {0: "UNSPECIFIED", 1: "STOP", 2: "MAX_TOKENS", 3: "SAFETY", 4: "RECITATION", 5: "OTHER"}
                reason_name = reason_map.get(candidate.finish_reason, f"UNKNOWN({candidate.finish_reason})")
                logger.warning(f"Gemini incomplete response (finish_reason={reason_name})")

                # If MAX_TOKENS, we might still have partial content - try to use it
                if candidate.finish_reason == 2 and hasattr(candidate, 'content') and candidate.content.parts:
                    logger.info("Attempting to parse partial response from MAX_TOKENS")
                    # Continue to parsing - might still get useful content
                else:
                    return {'enriched_description': '', 'search_keywords': []}

            # Check if content exists
            if not hasattr(candidate, 'content') or not candidate.content.parts:
                logger.warning("Gemini response has no content")
                return {'enriched_description': '', 'search_keywords': []}

            return self._parse_gemini_response(response.text)

        except Exception as e:
            logger.error(f"Text enrichment error: {e}")
            return {'enriched_description': '', 'search_keywords': []}

    def _enrich_with_image(self, prompt: str, image_url: str) -> Dict[str, str]:
        """Enrich using both text and image analysis."""
        try:
            import PIL.Image
            import io

            # Download image
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to download image: {image_url}")
                return self._enrich_text_only(prompt)

            # Convert to PIL Image
            image = PIL.Image.open(io.BytesIO(response.content))

            # Enhanced prompt with image context
            enhanced_prompt = prompt + "\n\nInclude visual details from the image: style, condition, lighting, layout."

            # Generate with image
            response = self.client.generate_content(
                [enhanced_prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=600,  # Same as text-only
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "enriched_description": {
                                "type": "string",
                                "description": "100-150 word property description"
                            },
                            "search_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Array of 5-7 searchable keywords"
                            }
                        },
                        "required": ["enriched_description", "search_keywords"]
                    }
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )

            # Check if response was blocked
            if not response.candidates or len(response.candidates) == 0:
                logger.warning("Gemini image analysis: no candidates, falling back to text-only")
                return self._enrich_text_only(prompt)

            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason != 1:
                reason_map = {0: "UNSPECIFIED", 1: "STOP", 2: "MAX_TOKENS", 3: "SAFETY", 4: "RECITATION", 5: "OTHER"}
                reason_name = reason_map.get(candidate.finish_reason, f"UNKNOWN({candidate.finish_reason})")
                logger.warning(f"Gemini image analysis incomplete (finish_reason={reason_name}), falling back to text-only")
                return self._enrich_text_only(prompt)

            if not hasattr(candidate, 'content') or not candidate.content.parts:
                logger.warning("Gemini image response has no content, falling back to text-only")
                return self._enrich_text_only(prompt)

            return self._parse_gemini_response(response.text)

        except Exception as e:
            logger.error(f"Image enrichment error: {e}")
            # Fallback to text-only
            return self._enrich_text_only(prompt)

    def _parse_gemini_response(self, response_text: str) -> Dict[str, str]:
        """Parse Gemini's JSON response (response_mime_type ensures valid JSON)."""
        import json

        try:
            # With response_mime_type="application/json", Gemini returns pure JSON
            data = json.loads(response_text.strip())
            return {
                'enriched_description': data.get('enriched_description', ''),
                'search_keywords': data.get('search_keywords', [])
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON: {e}")
            logger.debug(f"Response text: {response_text[:200]}")
            return {'enriched_description': '', 'search_keywords': []}


# Singleton instance
_enrichment_service = None


def get_enrichment_service() -> PropertyEnrichmentService:
    """Get or create singleton enrichment service."""
    global _enrichment_service
    if _enrichment_service is None:
        _enrichment_service = PropertyEnrichmentService()
    return _enrichment_service
