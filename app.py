import os
import subprocess
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"  #uploading the folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GS_PATH = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe" #ghostcript path


def get_size_kb(path):
    return os.path.getsize(path) / 1024


def reduction_percentage(original_kb, compressed_kb):  #calulating change percentage
    return round(((original_kb - compressed_kb) / original_kb) * 100, 2)


@app.route("/")
def home():
    return render_template("index.html")


# normal pdf compression with (low, medium, high ) level
@app.route("/normal", methods=["POST"])
def normal_compression():
    pdf = request.files["pdf"]
    level = request.form["level"]

    input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
    output_path = os.path.join(
        UPLOAD_FOLDER, f"normal_{level}_{pdf.filename}"
    )

    pdf.save(input_path)

    original_size = get_size_kb(input_path)

    quality = {
        "low": "/printer",
        "medium": "/ebook",
        "high": "/screen"
    }[level]

    command = [
        GS_PATH,
        "-sDEVICE=pdfwrite",
        f"-dPDFSETTINGS={quality}",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        f"-sOutputFile={output_path}",
        input_path
    ]

    subprocess.run(command, check=True)

    compressed_size = get_size_kb(output_path)
    percent = reduction_percentage(original_size, compressed_size)

    return render_template(
        "index.html",
        result=True,
        mode="normal",
        original=round(original_size, 2),
        compressed=round(compressed_size, 2),
        percent=percent,
        filename=os.path.basename(output_path)
    )


# pdf compression with specific ranges
@app.route("/range", methods=["POST"])
def range_compression():
    pdf = request.files["pdf"]
    level = request.form["level"]

    input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
    output_path = os.path.join(
        UPLOAD_FOLDER, f"range_{level}_{pdf.filename}"
    )

    pdf.save(input_path)
    original_size = get_size_kb(input_path)

    ranges = {
        "high": (100, 500),
        "medium": (500, 1000),
        "low": (1000, 2000)   #specified ranges in KB
    }

    min_kb, max_kb = ranges[level]

    dpi_low, dpi_high = 30, 150

    for _ in range(5):
        dpi = (dpi_low + dpi_high) // 2

        command = [
            GS_PATH,
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/screen",
            "-dDownsampleColorImages=true",
            f"-dColorImageResolution={dpi}",
            f"-dGrayImageResolution={dpi}",
            f"-dMonoImageResolution={dpi}",
            "-dNOPAUSE",
            "-dBATCH",
            "-dQUIET",
            f"-sOutputFile={output_path}",
            input_path
        ]

        subprocess.run(command, check=True)

        size_kb = get_size_kb(output_path)

        if min_kb <= size_kb <= max_kb:
            break
        elif size_kb > max_kb:
            dpi_high = dpi
        else:
            dpi_low = dpi

    compressed_size = get_size_kb(output_path)
    percent = reduction_percentage(original_size, compressed_size)

    return render_template(
        "index.html",
        result=True,
        mode="range",
        original=round(original_size, 2),
        compressed=round(compressed_size, 2),
        percent=percent,
        filename=os.path.basename(output_path)
    )


@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
