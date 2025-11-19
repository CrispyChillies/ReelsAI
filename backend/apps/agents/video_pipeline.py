"""
Unified Post Processing Pipeline

This module combines post analysis (transcription, summarization) with 
knowledge graph construction into a single streamlined pipeline.
"""

import json
import logging
import tempfile
import os
from typing import Dict, Any, Optional, BinaryIO
from datetime import datetime
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .video_analysis.image_understanding import summarize_video
from .kg_constructor.text_processor import TextProcessor
from .kg_constructor.config import get_google_llm

logger = logging.getLogger(__name__)


class UnifiedPostProcessor:
    """
    Complete pipeline that processes posts and creates knowledge graphs.
    
    Pipeline stages:
    1. Post Analysis: Extract textual content from a post
    2. Knowledge Graph Construction: Create Neo4j knowledge graph from analysis
    """
    
    def __init__(self, 
                 use_gemini_for_post: bool = True,
                 use_whisper_for_audio: bool = True,
                 llm=None,
                 enable_kg_resolution: bool = True):
        """
        Initialize the unified processor.
        
        Args:
            use_gemini_for_post: Use Gemini for post understanding
            use_whisper_for_audio: Use OpenAI Whisper for audio transcription
            llm: Optional LLM instance for knowledge extraction
            enable_kg_resolution: Whether to enable graph resolution for duplicates
        """
        self.use_gemini_for_post = use_gemini_for_post
        self.use_whisper_for_audio = use_whisper_for_audio
        
        # Initialize LLM for KG construction
        self.llm = llm or get_google_llm(model="gemini-2.5-flash")
        
        # Initialize KG processor
        self.kg_processor = TextProcessor(
            llm=self.llm,
            enable_resolution=enable_kg_resolution
        )
        
        logger.info(f"UnifiedPostProcessor initialized - Gemini: {use_gemini_for_post}, "
                   f"Whisper: {use_whisper_for_audio}, KG Resolution: {enable_kg_resolution}")
    
    def validate_video_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Validate the incoming video processing payload.
        
        Args:
            payload: The video processing payload
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['user', 'video_file', 'topic', 'source']
        
        for field in required_fields:
            if field not in payload:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate user data
        user = payload.get('user', {})
        if not user.get('user_id'):
            logger.error("User must have user_id")
            return False
        
        # Validate video file
        video_file = payload.get('video_file')
        if not video_file:
            logger.error("Post file is required")
            return False
        
        # Check if it's a valid file-like object
        if not hasattr(video_file, 'read') and not hasattr(video_file, 'chunks'):
            logger.error("Invalid video file format")
            return False
        
        return True
    
    def extract_video_analysis(self, video_file, video_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract analysis from video file using available methods.
        
        Args:
            video_file: Post file object (Django UploadedFile or similar)
            video_metadata: Post metadata for context
            
        Returns:
            Analysis result with transcript, summary, etc.
        """
        analysis_result = {
            'transcript': '',
            'summary': '',
            'detected_language': 'unknown',
            'analysis_method': '',
            'processing_time_seconds': 0,
            'error': None
        }
        
        start_time = datetime.now()
        
        try:
            # Method 1: Try Gemini video understanding (visual + audio)
            if self.use_gemini_for_video:
                try:
                    summary = self._analyze_with_gemini(video_file)
                    if summary and not summary.startswith("Error"):
                        analysis_result.update({
                            'summary': summary,
                            'analysis_method': 'gemini_video_understanding',
                            'detected_language': 'vi',  # Gemini returns Vietnamese
                        })
                        logger.info("Successfully analyzed video with Gemini")
                        return analysis_result
                except Exception as e:
                    logger.warning(f"Gemini video analysis failed: {e}")
            
            # Method 2: Fall back to OpenAI Whisper (audio only)
            if self.use_whisper_for_audio:
                try:
                    whisper_result = self.video_captioning.transcribe_and_summarize(video_file)
                    analysis_result.update({
                        'transcript': whisper_result.get('transcript', ''),
                        'summary': whisper_result.get('summary', ''),
                        'detected_language': whisper_result.get('detected_language', 'unknown'),
                        'analysis_method': 'whisper_openai'
                    })
                    logger.info("Successfully analyzed video with Whisper + OpenAI")
                    return analysis_result
                except Exception as e:
                    logger.warning(f"Whisper analysis failed: {e}")
                    analysis_result['error'] = f"Whisper analysis failed: {e}"
            
            # If both methods fail
            analysis_result['error'] = "All video analysis methods failed"
            logger.error("All video analysis methods failed")
            
        except Exception as e:
            analysis_result['error'] = f"Post analysis error: {e}"
            logger.error(f"Post analysis error: {e}")
        
        finally:
            analysis_result['processing_time_seconds'] = (datetime.now() - start_time).total_seconds()
        
        return analysis_result
    
    def _analyze_with_gemini(self, video_file) -> str:
        """
        Analyze video using Gemini video understanding.
        
        Args:
            video_file: Post file object
            
        Returns:
            Summary string from Gemini
        """
        # Create temporary file for Gemini processing
        temp_video_path = None
        
        try:
            # Create temporary video file
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                if hasattr(video_file, 'chunks'):
                    # Django UploadedFile
                    for chunk in video_file.chunks():
                        temp_video.write(chunk)
                else:
                    # File-like object
                    video_file.seek(0)
                    temp_video.write(video_file.read())
                temp_video_path = temp_video.name
            
            # Use Gemini to analyze the video
            summary = summarize_video(temp_video_path)
            print(summary)
            return summary
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            raise e
        
        finally:
            # Clean up temporary file
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp video file: {e}")
    
    def create_kg_payload_from_analysis(self, original_payload: Dict[str, Any], 
                                      analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert video analysis result to KG processor payload format.
        
        Args:
            original_payload: Original video processing payload
            analysis_result: Result from video analysis
            
        Returns:
            Payload formatted for KG processor
        """
        # Generate unique video ID if not provided
        video_metadata = original_payload.get('video', {})
        if not video_metadata.get('video_id'):
            # Generate video ID from file name or timestamp
            video_file = original_payload.get('video_file')
            if hasattr(video_file, 'name') and video_file.name:
                base_name = os.path.splitext(video_file.name)[0]
                video_id = f"video_{base_name}_{int(datetime.now().timestamp())}"
            else:
                video_id = f"video_{int(datetime.now().timestamp())}"
            video_metadata['video_id'] = video_id
        
        # Use summary as the main content for KG construction
        summarization_text = analysis_result.get('summary', '')
        if not summarization_text and analysis_result.get('transcript'):
            # Fall back to transcript if no summary
            summarization_text = analysis_result.get('transcript', '')
        
        # Create KG payload
        kg_payload = {
            'user': original_payload['user'],
            'video': {
                'video_id': video_metadata['video_id'],
                'title': video_metadata.get('title', f"Post {video_metadata['video_id']}"),
                'description': video_metadata.get('description', ''),
                'duration': video_metadata.get('duration', 0),
                'upload_date': video_metadata.get('upload_date', datetime.now().isoformat()),
                'url': video_metadata.get('url', ''),
                # Add analysis metadata
                'analysis_method': analysis_result.get('analysis_method', ''),
                'detected_language': analysis_result.get('detected_language', 'unknown'),
                'has_transcript': bool(analysis_result.get('transcript')),
                'analysis_processing_time': analysis_result.get('processing_time_seconds', 0)
            },
            'topic': original_payload['topic'],
            'source': original_payload['source'],
            'summarization': summarization_text
        }
        
        return kg_payload
    
    def process_video_to_knowledge_graph(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete pipeline: process video file and create knowledge graph.
        
        Args:
            payload: Post processing payload with video_file
            
        Returns:
            Complete processing result
        """
        start_time = datetime.now()
        
        try:
            # Validate payload
            if not self.validate_video_payload(payload):
                raise ValueError("Invalid video payload structure")
            
            user_id = payload['user']['user_id']
            video_file = payload['video_file']
            
            logger.info(f"Starting video processing pipeline for user: {user_id}")
            
            # Stage 1: Post Analysis
            logger.info("Stage 1: Analyzing video content...")
            video_metadata = payload.get('video', {})
            analysis_result = self.extract_video_analysis(video_file, video_metadata)
            
            if analysis_result.get('error'):
                # Post analysis failed
                processing_time = (datetime.now() - start_time).total_seconds()
                return {
                    'status': 'error',
                    'stage': 'video_analysis',
                    'error_message': analysis_result['error'],
                    'processing_time_seconds': processing_time,
                    'analysis_result': analysis_result
                }
            
            logger.info(f"Post analysis completed: {analysis_result['analysis_method']}")
            
            # Stage 2: Knowledge Graph Construction
            logger.info("Stage 2: Constructing knowledge graph...")
            kg_payload = self.create_kg_payload_from_analysis(payload, analysis_result)
            kg_result = self.kg_processor.process_video_summarization(kg_payload)
            
            # Calculate total processing time
            total_processing_time = (datetime.now() - start_time).total_seconds()
            
            # Combine results
            combined_result = {
                'status': 'success',
                'pipeline_type': 'unified_video_to_kg',
                'total_processing_time_seconds': total_processing_time,
                
                # Post analysis stage results
                'video_analysis': {
                    'analysis_method': analysis_result['analysis_method'],
                    'detected_language': analysis_result['detected_language'],
                    'has_transcript': bool(analysis_result.get('transcript')),
                    'summary_length': len(analysis_result.get('summary', '')),
                    'transcript_length': len(analysis_result.get('transcript', '')),
                    'processing_time_seconds': analysis_result['processing_time_seconds']
                },
                
                # Knowledge graph stage results (inherit from kg_result)
                'knowledge_graph': kg_result,
                
                # Combined metadata
                'video_id': kg_payload['video']['video_id'],
                'user_id': user_id,
                'final_summarization_text': kg_payload['summarization']
            }
            
            logger.info(f"Pipeline completed successfully in {total_processing_time:.2f}s")
            return combined_result
            
        except Exception as e:
            total_processing_time = (datetime.now() - start_time).total_seconds()
            error_result = {
                'status': 'error',
                'stage': 'pipeline_error',
                'error_message': str(e),
                'total_processing_time_seconds': total_processing_time
            }
            logger.error(f"Pipeline failed: {e}")
            return error_result


def process_video_file_to_kg(video_file, user_data: Dict[str, Any], 
                           video_metadata: Dict[str, Any] = None,
                           topic_data: Dict[str, Any] = None,
                           source_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to process a video file to knowledge graph.
    
    Args:
        video_file: Post file object (Django UploadedFile, file handle, etc.)
        user_data: User information dict with user_id
        video_metadata: Optional video metadata
        topic_data: Optional topic information
        source_data: Optional source information
        
    Returns:
        Processing result
    """
    # Set defaults
    video_metadata = video_metadata or {}
    topic_data = topic_data or {'name': 'General', 'category': 'Uncategorized'}
    source_data = source_data or {'name': 'Direct Upload', 'type': 'User Upload'}
    
    payload = {
        'user': user_data,
        'video_file': video_file,
        'video': video_metadata,
        'topic': topic_data,
        'source': source_data
    }
    
    processor = UnifiedPostProcessor()
    return processor.process_video_to_knowledge_graph(payload)


# Example usage payload
EXAMPLE_VIDEO_PAYLOAD = {
    "user": {
        "user_id": "user_123",
        "name": "John Doe",
        "email": "john@example.com"
    },
    "video_file": None,  # This would be the actual video file object
    "video": {
        "title": "Khóc cười chuyện sĩ tử kiêng kỵ trước ngày thi THPT",
        "description": "Chuyện thi THPTQG",
        "duration": 1800,  # seconds (optional)
        "upload_date": "2025-11-14T10:00:00Z",  # optional
        "url": ""  # optional
    },
    "topic": {
        "name": "Thi cử",
        "description": "Thi cử THTPQG",
        "category": "Education"
    },
    "source": {
        "name": "Educational Platform",
        "type": "Video Upload",
        "url": "https://example.com",
        "description": "Direct video upload to platform"
    }
}
# EXAMPLE_VIDEO_PAYLOAD = {
#     "user": {
#         "user_id": "user_123",
#         "name": "John Doe",
#         "email": "john@example.com"
#     },
#     "video_file": None,  # This would be the actual video file object
#     "video": {
#         "title": "Machine Learning Tutorial",
#         "description": "Introduction to ML concepts",
#         "duration": 1800,  # seconds (optional)
#         "upload_date": "2025-11-14T10:00:00Z",  # optional
#         "url": ""  # optional
#     },
#     "topic": {
#         "name": "Machine Learning",
#         "description": "Artificial intelligence and data science",
#         "category": "Technology"
#     },
#     "source": {
#         "name": "Educational Platform",
#         "type": "Video Upload",
#         "url": "https://example.com",
#         "description": "Direct video upload to platform"
#     }
# }