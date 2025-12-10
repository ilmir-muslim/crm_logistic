# test_fonts.py
import os
from pathlib import Path


def check_fonts():
    font_paths = [
        "static/fonts/arial.ttf",
        "static/fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    print("Проверка доступности шрифтов:")
    for path in font_paths:
        exists = os.path.exists(path)
        print(f"{'✓' if exists else '✗'} {path}")

    # Проверка системных путей
    print("\nПоиск шрифтов в системе:")
    for root, dirs, files in os.walk("/usr/share/fonts"):
        for file in files:
            if file.endswith(".ttf") and any(
                keyword in file.lower() for keyword in ["arial", "liberation", "dejavu"]
            ):
                print(f"  {os.path.join(root, file)}")


if __name__ == "__main__":
    check_fonts()
