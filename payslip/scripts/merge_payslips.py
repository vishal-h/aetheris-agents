#!/usr/bin/env python3
import glob
import os
import subprocess
import sys
import tempfile


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <employee_output_dir>", file=sys.stderr)
        sys.exit(1)

    employee_output_dir = sys.argv[1]
    html_files = sorted(
        glob.glob(os.path.join(employee_output_dir, "*.html")),
        reverse=True,
    )

    if not html_files:
        print(f"No HTML files found in {employee_output_dir}")
        sys.exit(0)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_pdfs = []
        for html_path in html_files:
            basename = os.path.splitext(os.path.basename(html_path))[0]
            temp_pdf = os.path.join(tmpdir, basename + ".pdf")
            result = subprocess.run(
                ["wkhtmltopdf", html_path, temp_pdf],
                check=False,
                capture_output=True,
            )
            if result.returncode != 0:
                print(result.stderr.decode(), file=sys.stderr)
                sys.exit(1)
            temp_pdfs.append(temp_pdf)

        output_pdf = os.path.join(employee_output_dir, "merged.pdf")
        result = subprocess.run(
            ["gs", "-dBATCH", "-dNOPAUSE", "-q",
             "-sDEVICE=pdfwrite",
             f"-sOutputFile={output_pdf}"] + temp_pdfs,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            print(result.stderr.decode(), file=sys.stderr)
            sys.exit(1)

    print(f"PDF generated: {output_pdf}")


if __name__ == "__main__":
    main()
