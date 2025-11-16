import os
import subprocess
from pathlib import Path

def convert_file(input_file, output_file, sample_rate=44100):
    '''
    Convert a single audio file to another format with specified sample rate.
    
    Args:
        input_file: Path to the source audio file
        output_file: Path where the converted file will be saved
        sample_rate: Target sample rate in Hz (default: 44100)
    '''
    try:
        cmd = ["ffmpeg", "-i", input_file, "-ar", str(sample_rate), "-y", output_file]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Converted: {input_file} → {output_file}")
        return True
    except Exception as e:
        print(f"Error converting {input_file}: {e}")
        return False

def convert_directory(input_dir, output_dir, input_ext=".mp3", output_ext=".wav", sample_rate=44100):
    '''
    Convert all files of one type in a directory to another format.
    
    Args:
        input_dir: Directory containing files to convert
        output_dir: Directory where converted files will be saved
        input_ext: File extension to look for (default: .mp3)
        output_ext: Output file extension (default: .wav)
        sample_rate: Target sample rate in Hz (default: 44100)
    '''
    # Ensure directories exist
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Get all matching files
    files = list(input_dir.glob(f"*{input_ext}"))
    if not files:
        print(f"No {input_ext} files found in {input_dir}")
        return 0
    
    # Convert each file
    success_count = 0
    for i, file_path in enumerate(files):
        output_path = output_dir / (file_path.stem + output_ext)
        print(f"Converting {i+1}/{len(files)}: {file_path.name}")
        
        if convert_file(str(file_path), str(output_path), sample_rate):
            success_count += 1
    
    print(f"Successfully converted {success_count} of {len(files)} files")
    return success_count

# Example usage
if __name__ == "__main__":
    # Example 1: Convert a single file
    input_file = '/home/ajs7/Downloads/04 - Clair de Lune.mp3'
    output_file = '/home/ajs7/Music/cdl.wav'
    convert_file(input_file, output_file)
    
    # Example 2: Convert a directory (uncomment to use)
    # convert_directory(
    #     input_dir='/home/ajs7/Music/mp3',
    #     output_dir='/home/ajs7/Music/wav',
    #     input_ext='.mp3',
    #     output_ext='.wav'
    # )