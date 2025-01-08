import os
import rawpy
import imageio
import typer
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize Typer app
app = typer.Typer()

# Function to process a single raw image
def process_raw(input_file: str, output_dir: str, output_ext: str):
    try:
        input_path = Path(input_file)
        output_file = Path(output_dir) / (input_path.stem + output_ext)
        with rawpy.imread(input_file) as raw:
            rgb = raw.postprocess()
            imageio.imsave(output_file, rgb, format=output_ext.removeprefix(".").lower())
    except Exception as e:
        typer.secho(f"Error processing {input_file}: {e}", fg=typer.colors.RED)

# CLI command
@app.command()
def convert_images(
    input_path: str = typer.Argument(..., help="Path to a raw image file or directory"),
    output_dir: str = typer.Argument(..., help="Directory to save processed images"),
    input_ext: str = typer.Option(".cr3", help="Input file extension (if directory is provided)"),
    output_ext: str = typer.Option(".png", help="Output file extension (e.g., .png, .jpg)"),
    threads: int = typer.Option(None, help="Number of threads to use (default: CPU count)"),
):
    """
    Convert raw images to another format using multithreading.
    Supports single file or directory input.
    """
    input_path = Path(input_path)
    output_path = Path(output_dir)

    # Create the output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Check if input path is a file or directory
    if input_path.is_file():
        # Process a single file
        typer.secho(f"Processing single file: {input_path.name}", fg=typer.colors.GREEN)
        process_raw(str(input_path), str(output_dir), output_ext)
    elif input_path.is_dir():
        # Get list of raw files
        raw_files = [str(file) for file in input_path.glob(f"*{input_ext.lower()}")]
        if not raw_files:
            typer.secho("No raw files found in the input directory!", fg=typer.colors.YELLOW)
            raise typer.Exit(1)

        # Determine number of threads
        num_threads = threads or os.cpu_count()
        typer.secho(f"Using {num_threads} threads to convert {len(raw_files)} files.", fg=typer.colors.GREEN)

        # Prepare tasks for threading
        tasks = [(file, output_dir, output_ext) for file in raw_files]

        # Process images using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_file = {
                executor.submit(process_raw, file, output_dir, output_ext): file for file, output_dir, output_ext in tasks
            }

            for future in as_completed(future_to_file):
                try:
                    future.result()
                except Exception as e:
                    typer.secho(f"Error in processing: {e}", fg=typer.colors.RED)
    else:
        typer.secho("Invalid input path! Provide a valid file or directory.", fg=typer.colors.RED)
        raise typer.Exit(1)

    typer.secho(f"Processing completed. Converted images saved in {output_dir}", fg=typer.colors.CYAN)

# Entry point
if __name__ == "__main__":
    app()

# Example usage:
# python Formatflip.py "E:\Test\raw" "E:\Test\conv" --input-ext ".cr3" --output-ext ".jpg" --threads 4
