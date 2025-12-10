# download_fonts.py
import requests
from pathlib import Path


def download_fonts():
    """Скачивает русские шрифты"""
    font_dir = Path("static/fonts")
    font_dir.mkdir(parents=True, exist_ok=True)

    # Ссылки на свободные шрифты
    font_urls = {
        "liberationsans-regular.ttf": "https://github.com/liberationfonts/liberation-fonts/files/2926169/LiberationSans-Regular.ttf",
        "liberationsans-bold.ttf": "https://github.com/liberationfonts/liberation-fonts/files/2926168/LiberationSans-Bold.ttf",
    }

    for filename, url in font_urls.items():
        font_path = font_dir / filename
        if not font_path.exists():
            print(f"Скачиваю {filename}...")
            response = requests.get(url)
            if response.status_code == 200:
                with open(font_path, "wb") as f:
                    f.write(response.content)
                print(f"Скачан: {filename}")
            else:
                print(f"Ошибка скачивания {filename}")

    print("Шрифты готовы к использованию")


if __name__ == "__main__":
    download_fonts()
