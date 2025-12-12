"""Content generation service - OpenAI integration."""

import os
import time
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import httpx
from openai import AsyncOpenAI
import logging

from app.config import get_settings
from app.models.content import GeneratedContent

logger = logging.getLogger(__name__)
settings = get_settings()


class ContentGenerator:
    """Service for generating content using OpenAI APIs."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.uploads_dir = "uploads/generated"
        os.makedirs(self.uploads_dir, exist_ok=True)

    async def generate_document(
        self,
        prompt: str,
        document_type: str = "general",
        filename: str = "document.docx",
        profile_id: Optional[str] = None,
        db: Session = None,
    ) -> GeneratedContent:
        """
        Generate document content using GPT-4.

        Note: This generates the TEXT content. The actual .docx/.xlsx
        creation with embedded tokens is done by the USB builder.
        """
        start_time = time.time()

        # Build system prompt based on document type
        system_prompts = {
            "salary": "You are creating content for a confidential salary report. Include realistic but fictional employee names, salaries, bonuses, and compensation data. Make it look authentic.",
            "hr": "You are creating content for an HR policy document. Include realistic policies, procedures, and guidelines that would be found in a corporate HR department.",
            "financial": "You are creating content for a financial projection document. Include realistic revenue figures, expense categories, and budget allocations.",
            "technical": "You are creating content for technical documentation. Include server configurations, credentials (use placeholder values), and infrastructure details.",
            "general": "You are creating professional document content. Make it realistic and authentic-looking for a corporate environment.",
        }

        system_prompt = system_prompts.get(document_type, system_prompts["general"])
        system_prompt += "\n\nIMPORTANT: All content must be appropriate for professional settings (G, PG, or PG-13 rated). Do not include any inappropriate, offensive, or explicit content."

        # Generate content
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
        )

        generated_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename.replace('.docx', '.txt').replace('.xlsx', '.txt')}"
        file_path = os.path.join(self.uploads_dir, safe_filename)

        with open(file_path, "w") as f:
            f.write(generated_text)

        generation_time = int((time.time() - start_time) * 1000)

        # Create database record
        content = GeneratedContent(
            profile_id=profile_id,
            content_type="document",
            prompt=prompt,
            model_used="gpt-4-turbo-preview",
            filename=filename,
            file_path=file_path,
            file_size_bytes=len(generated_text.encode("utf-8")),
            mime_type="text/plain",
            metadata={
                "document_type": document_type,
                "original_filename": filename,
            },
            tokens_used=tokens_used,
            generation_time_ms=generation_time,
        )

        if db:
            db.add(content)
            db.commit()
            db.refresh(content)

        return content

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural",
        filename: str = "image.png",
        profile_id: Optional[str] = None,
        db: Session = None,
    ) -> GeneratedContent:
        """
        Generate an image using DALL-E 3.
        """
        start_time = time.time()

        # Add content policy reminder to prompt
        safe_prompt = f"{prompt}\n\nStyle: Professional, appropriate for corporate/business settings. Must be G, PG, or PG-13 rated."

        # Generate image
        response = await self.client.images.generate(
            model="dall-e-3",
            prompt=safe_prompt,
            size=size,
            quality="standard",
            style=style,
            n=1,
        )

        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt

        # Download image
        async with httpx.AsyncClient() as client:
            img_response = await client.get(image_url)
            image_data = img_response.content

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(self.uploads_dir, safe_filename)

        with open(file_path, "wb") as f:
            f.write(image_data)

        generation_time = int((time.time() - start_time) * 1000)

        # Create database record
        content = GeneratedContent(
            profile_id=profile_id,
            content_type="image",
            prompt=prompt,
            model_used="dall-e-3",
            filename=filename,
            file_path=file_path,
            file_size_bytes=len(image_data),
            mime_type="image/png",
            metadata={
                "size": size,
                "style": style,
                "revised_prompt": revised_prompt,
                "original_url": image_url,
            },
            generation_time_ms=generation_time,
        )

        if db:
            db.add(content)
            db.commit()
            db.refresh(content)

        return content
