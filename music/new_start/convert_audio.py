"""
Audio File Conversion Utilities

This module provides tools to convert between audio formats and extract sounds from SF2 soundfonts.
Requires external tools: ffmpeg and sf2extract to be installed on the system.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Union, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_audio(
    source_path: Union[str, Path],
    target_path: Union[str, Path],
    sample_rate: int = 44100,
    overwrite: bool = True
) -> bool:
    """
    Convert audio files between formats with specified sample rate.
    
    Args:
        source_path: Path to the source audio file
        target_path: Path where the converted file will be saved
        sample_rate: Target sample rate in Hz (default: 44100)
        overwrite: Whether to overwrite the target file if it exists (default: True)
    
    Returns:
        bool: True if conversion was successful, False otherwise
    
    Examples:
        >>> convert_audio("input.mp3", "output.wav", sample_rate=48000)
        >>> convert_audio("input.wav", "output.flac", overwrite=False)
    """
    try:
        # Ensure paths are properly quoted to handle spaces
        source_path = str(source_path)
        target_path = str(target_path)
        
        # Build ffmpeg command with proper argument passing
        command = [
            "ffmpeg",
            "-i", source_path,
            "-ar", str(sample_rate),
            target_path
        ]
        
        # Add overwrite flag if needed
        if overwrite:
            command.append("-y")
        
        # Execute the command using subprocess for better security
        result = subprocess.run(
            command, 
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Conversion failed: {result.stderr}")
            return False
        
        logger.info(f"Successfully converted {source_path} to {target_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        return False


def extract_sf2_to_wav(
    sf2_path: Union[str, Path],
    output_dir: Union[str, Path]
) -> bool:
    """
    Extract samples from a SoundFont 2 (.sf2) file to WAV files.
    
    Args:
        sf2_path: Path to the source SF2 file
        output_dir: Directory where extracted WAV files will be saved
    
    Returns:
        bool: True if extraction was successful, False otherwise
    
    Note:
        Requires sf2extract tool to be installed on the system
    """
    try:
        # Ensure the output directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build and execute sf2extract command
        command = ["sf2extract", str(sf2_path), str(output_dir)]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"SF2 extraction failed: {result.stderr}")
            return False
            
        logger.info(f"Successfully extracted {sf2_path} to {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error during SF2 extraction: {str(e)}")
        return False


def process_directory(
    directory: Union[str, Path],
    sample_rate: Optional[int] = None
) -> int:
    """
    Process all compatible audio files in a directory, converting them to the specified sample rate.
    
    Args:
        directory: Directory containing audio files to process
        sample_rate: Target sample rate in Hz (default: None, keeps original rate)
    
    Returns:
        int: Number of successfully processed files
    """
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory {directory} does not exist")
        return 0
        
    success_count = 0
    files = list(directory.iterdir())
    
    for i, file_path in enumerate(files):
        if not file_path.is_file():
            continue
            
        # Process only audio files
        if file_path.suffix.lower() not in ('.wav', '.mp3', '.flac', '.ogg'):
            continue
            
        logger.info(f"Processing file {i+1}/{len(files)}: {file_path.name}")
        
        if sample_rate is not None:
            # Convert the file in place with new sample rate
            success = convert_audio(file_path, file_path, sample_rate=sample_rate)
            if success:
                success_count += 1
                
    return success_count


def main():
    """Example usage of the conversion functions."""
    # Example 1: Extract sounds from SF2 soundfont
    sf2_file = '/home/ajs7/Downloads/essential.sf2'
    output_dir = '/home/ajs7/Downloads/music/essential/'
    
    logger.info(f"Extracting soundfont: {sf2_file}")
    extract_sf2_to_wav(sf2_file, output_dir)
    
    # Example 2: Process all files in the output directory
    logger.info(f"Converting all extracted files to 44.1kHz")
    file_count = process_directory(output_dir, sample_rate=44100)
    logger.info(f"Successfully processed {file_count} files")
    
    # Example 3: Convert a single file (commented out)
    # source_file = '/media/ajs6/3537-6630/synsound/rush.wav'
    # target_file = '/media/ajs6/3537-6630/synsound/rush.mp3'
    # convert_audio(source_file, target_file)


if __name__ == "__main__":
    main()