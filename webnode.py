import os
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin
from colorama import Fore, Style, init

init(autoreset=True)

# Simulador de sugerencias (puedes conectar con una API real)
def suggest_sites(name):
    print(f"{Fore.CYAN}🔎 Buscando sitios similares a: {Style.BRIGHT}{name}")
    # Simuladas por ahora
    suggestions = {
        "YouTube": ["Vimeo", "Dailymotion", "Twitch", "TikTok", "Vevo"],
        "GitHub": ["GitLab", "Bitbucket", "SourceForge", "Codeberg", "Gitea"],
        "Wikipedia": ["Britannica", "Wiktionary", "Wikidata", "Scholarpedia", "Infoplease"]
    }
    return suggestions.get(name, [])

def fetch_title_and_icon(url):
    print(f"{Fore.YELLOW}🌐 Analizando página: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title else "Untitled"
    icon_link = soup.find("link", rel=lambda x: x and "icon" in x.lower())
    favicon_url = icon_link["href"] if icon_link else None
    if favicon_url and not favicon_url.startswith("http"):
        favicon_url = urljoin(url, favicon_url)
    return title, favicon_url

def download_icon(url, path):
    try:
        response = requests.get(url, stream=True)
        total = int(response.headers.get('content-length', 0))
        with open(path, "wb") as f, tqdm(total=total, unit='B', unit_scale=True, desc="🖼️ Icono") as pbar:
            for data in response.iter_content(chunk_size=1024):
                f.write(data)
                pbar.update(len(data))
        print(f"{Fore.GREEN}✅ Ícono guardado en: {path}")
    except Exception as e:
        print(f"{Fore.RED}⚠️ Error al descargar favicon: {e}")

def create_webapp(name, url, icon_url):
    folder = os.path.join("webapps", name.replace(" ", "_"))
    os.makedirs(folder, exist_ok=True)

    launcher = f"""
import webview

webview.create_window("{name}", "{url}", width=1000, height=700)
webview.start()
"""
    with open(os.path.join(folder, "launch.py"), "w") as f:
        f.write(launcher.strip())

    if icon_url:
        icon_path = os.path.join(folder, "icon.ico")
        download_icon(icon_url, icon_path)

    print(f"{Fore.MAGENTA}📦 App creada: {Style.BRIGHT}{folder}")

def main():
    parser = argparse.ArgumentParser(description="Generador de apps web estilo Influent")
    parser.add_argument("--url", help="URL del sitio web")
    parser.add_argument("--name", help="Nombre de la app")
    parser.add_argument("--sug", help="Nombre base para sugerencias")

    args = parser.parse_args()

    if args.sug:
        options = suggest_sites(args.sug)
        if not options:
            print(f"{Fore.RED}⚠️ No se encontraron sugerencias para: {args.sug}")
            return
        print(f"{Fore.BLUE}🎯 Sugerencias encontradas:")
        for i, site in enumerate(options, 1):
            print(f"{Fore.GREEN}{i}. {site}")
        choice = input(f"{Fore.CYAN}👉 Escribe el número del sitio que deseas usar: ")
        try:
            selected = options[int(choice)-1]
            url = f"https://www.{selected.lower().replace(' ', '')}.com"
            title, icon_url = fetch_title_and_icon(url)
            create_webapp(title, url, icon_url)
        except Exception as e:
            print(f"{Fore.RED}⚠️ Error: {e}")
        return

    if args.url:
        title, icon_url = fetch_title_and_icon(args.url)
        app_name = args.name if args.name else title
        print(f"{Fore.BLUE}🏷️ Nombre de la app: {Style.BRIGHT}{app_name}")
        create_webapp(app_name, args.url, icon_url)
    else:
        print(f"{Fore.RED}❌ Debes usar --url o --sug")

if __name__ == "__main__":
    main()

