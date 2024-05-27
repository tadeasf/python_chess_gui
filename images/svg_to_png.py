import os
import tkinter as tk
from tkinter import filedialog, simpledialog
import cairosvg


def find_svg_files(directory):
    svg_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".svg"):
                svg_files.append(os.path.join(root, file))
    return svg_files


def convert_svg_to_png(svg_files, size, input_directory, output_directory):
    for svg_file in svg_files:
        relative_path = os.path.relpath(svg_file, input_directory)
        output_file_path = os.path.join(
            output_directory, os.path.splitext(relative_path)[0] + ".png"
        )

        # Create necessary subdirectories
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        cairosvg.svg2png(
            url=svg_file,
            write_to=output_file_path,
            output_width=size,
            output_height=size,
        )


def main():
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Ask the user to select an input directory
    input_directory = filedialog.askdirectory(title="Select Input Directory")
    if not input_directory:
        print("No directory selected. Exiting...")
        return

    # Ask the user for the size of the output PNG files
    size = simpledialog.askinteger(
        "Input", "Enter the size in pixels for the PNG files:"
    )
    if size is None:
        print("No size entered. Exiting...")
        return

    # Find all .svg files in the input directory
    svg_files = find_svg_files(input_directory)
    if not svg_files:
        print("No .svg files found in the selected directory.")
        return

    # Create the output directory
    output_directory = os.path.join(os.getcwd(), "pngs")
    os.makedirs(output_directory, exist_ok=True)

    # Convert .svg files to .png files
    convert_svg_to_png(svg_files, size, input_directory, output_directory)
    print("Conversion complete. PNG files are saved in:", output_directory)


if __name__ == "__main__":
    main()
