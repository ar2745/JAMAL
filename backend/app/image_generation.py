import logging
import os
import tempfile
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import torch
from compel import Compel
from diffusers import (EulerAncestralDiscreteScheduler,
                       StableDiffusionPipeline, StableDiffusionXLPipeline)
from huggingface_hub import HfFolder, hf_hub_download
from PIL import Image
from tqdm import tqdm

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ImageGenerator:
    def __init__(self, model_type: str = "sd15"):
        """
        Initialize the image generator with specified model type.
        
        Args:
            model_type (str): Either "sdxl" for Stable Diffusion XL or "sd15" for Stable Diffusion 1.5
        """
        try:
            # Set up device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")
            self.model_type = model_type
            
            # Create output directory
            self.output_dir = Path("/images/generated_images")
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create models directory
            self.models_dir = Path("/images/models")
            self.models_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize the appropriate pipeline
            logger.info(f"Loading {model_type} model...")
            try:
                if model_type == "sdxl":
                    logger.info("Initializing Stable Diffusion XL pipeline...")
                    model_id = "stabilityai/stable-diffusion-xl-base-1.0"
                    variant = "fp16" if self.device == "cuda" else None
                else:
                    logger.info("Initializing Stable Diffusion 1.5 pipeline...")
                    model_id = "runwayml/stable-diffusion-v1-5"
                    variant = None
                
                # Initialize the pipeline directly
                logger.info("Initializing pipeline...")
                if model_type == "sdxl":
                    self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                        model_id,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        use_safetensors=False,  # Use PyTorch weights instead
                        variant=variant,
                        cache_dir=str(self.models_dir),
                        local_files_only=False
                    )
                else:
                    self.pipeline = StableDiffusionPipeline.from_pretrained(
                        model_id,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        use_safetensors=False,  # Use PyTorch weights instead
                        variant=variant,
                        cache_dir=str(self.models_dir),
                        local_files_only=False
                    )
                logger.info("Pipeline loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load pipeline: {str(e)}\n{traceback.format_exc()}")
                raise
            
            try:
                logger.info("Moving pipeline to device...")
                self.pipeline = self.pipeline.to(self.device)
                logger.info("Pipeline moved to device successfully")
            except Exception as e:
                logger.error(f"Failed to move pipeline to device: {str(e)}\n{traceback.format_exc()}")
                raise
            
            try:
                logger.info("Initializing prompt weighting...")
                self.compel = Compel(
                    tokenizer=self.pipeline.tokenizer,
                    text_encoder=self.pipeline.text_encoder
                )
                logger.info("Prompt weighting initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize prompt weighting: {str(e)}\n{traceback.format_exc()}")
                raise
            
            try:
                logger.info("Setting up scheduler...")
                self.pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(
                    self.pipeline.scheduler.config
                )
                logger.info("Scheduler set up successfully")
            except Exception as e:
                logger.error(f"Failed to set up scheduler: {str(e)}\n{traceback.format_exc()}")
                raise
            
            logger.info("ImageGenerator initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize ImageGenerator: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        width: int = 512,
        height: int = 512,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate an image from a text prompt.
        
        Args:
            prompt (str): The text prompt describing the image
            negative_prompt (Optional[str]): Negative prompt for better control
            num_inference_steps (int): Number of denoising steps
            guidance_scale (float): How closely to follow the prompt
            width (int): Width of the generated image
            height (int): Height of the generated image
            seed (Optional[int]): Random seed for reproducibility
            
        Returns:
            Dict[str, Any]: Dictionary containing image path and metadata
        """
        try:
            logger.info(f"Generating image with prompt: {prompt}")
            # Generate the image
            generator = torch.Generator(device=self.device)
            if seed is not None:
                generator.manual_seed(seed)
            
            # Generate the image
            logger.info("Starting image generation...")
            image = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                generator=generator
            ).images[0]
            
            # Save the image
            image_id = str(uuid.uuid4())
            image_path = self.output_dir / f"{image_id}.png"
            logger.info(f"Saving image to {image_path}")
            image.save(image_path)
            
            # Return the result
            return {
                "image_url": f"/generated_images/{image_id}.png",
                "generation_time": 0.0  # TODO: Implement actual timing
            }
            
        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def cleanup(self, image_id: str) -> bool:
        """
        Clean up a generated image.
        
        Args:
            image_id (str): The ID of the image to clean up
            
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        try:
            image_path = self.output_dir / f"{image_id}.png"
            if image_path.exists():
                image_path.unlink()
            return True
        except Exception as e:
            error_msg = f"Failed to cleanup image {image_id}: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return False 