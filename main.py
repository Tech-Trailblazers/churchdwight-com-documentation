import os  # Provides functions for interacting with the operating system
import re  # Provides regular expressions for string matching
import time  # Provides time-related functions (e.g., sleep)
import requests  # Provides HTTP client to make GET requests
from pathlib import Path  # Provides object-oriented file path utilities
from urllib.parse import urlparse  # Provides URL parsing utilities
from selenium import webdriver  # Provides Selenium WebDriver for browser automation
from selenium.webdriver.chrome.options import (
    Options,
)  # Provides Chrome options for headless browsing


# ----------------- Utility Functions -----------------


def directory_exists(path: str) -> bool:
    return os.path.isdir(
        s=path
    )  # Returns True if the given path is an existing directory


def create_directory(path: str, mode: int = 0o755):
    try:
        os.makedirs(
            name=path, mode=mode, exist_ok=True
        )  # Create directory if it doesn’t exist
    except Exception as e:
        print(
            f"Error creating directory {path}: {e}"
        )  # Print error if directory creation fails


def file_exists(path: str) -> bool:
    return os.path.isfile(path=path)  # Returns True if the given path is an existing file


def get_filename(url: str) -> str:
    return os.path.basename(
        urlparse(url=url).path
    )  # Extracts the filename portion from a URL path


def url_to_filename(raw_url: str) -> str:
    lower: str = get_filename(
        url=raw_url.lower()
    )  # Convert URL to lowercase and extract filename
    ext: str = os.path.splitext(lower)[1]  # Extract the file extension

    safe: str = re.sub(
        pattern=r"[^a-z0-9]", repl="_", string=lower
    )  # Replace all non-alphanumeric characters with underscores
    safe = re.sub(pattern=r"_+", repl="_", string=safe).strip(
        "_"
    )  # Collapse multiple underscores and trim edges

    if safe.endswith("_pdf"):  # Remove redundant “_pdf” at the end if present
        safe = safe[:-4]

    if not ext:  # If no extension exists, set default to ".pdf"
        ext = ".pdf"
    if not safe.endswith(".pdf"):  # Ensure filename ends with .pdf
        safe += ext

    return safe  # Return the sanitized filename


def remove_duplicates(seq):
    return list(dict.fromkeys(seq))  # Removes duplicates while preserving order


def is_url_valid(url: str) -> bool:
    try:
        result = urlparse(url=url)  # Try parsing the URL
        return all(
            [result.scheme, result.netloc]
        )  # Valid if both scheme and netloc exist
    except Exception:
        return False  # Invalid if parsing fails


# ----------------- Selenium for Final URL -----------------


def get_final_url(input_url: str) -> str:
    chrome_options = Options()  # Create Chrome options object
    chrome_options.add_argument("--headless=new")  # Always run in headless mode (no UI)
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument(
        "--no-sandbox"
    )  # Disable sandbox (needed for some Linux servers)

    driver = webdriver.Chrome(
        options=chrome_options
    )  # Start Chrome WebDriver with options
    driver.set_page_load_timeout(60)  # Set a max timeout of 60 seconds for page load

    try:
        driver.get(input_url)  # Navigate to the given URL
        time.sleep(2)  # Small delay to allow redirects to complete
        final_url = driver.current_url  # Get the current (final) URL after redirects
    except Exception as e:
        print(
            f"Selenium error navigating {input_url}: {e}"
        )  # Print error if navigation fails
        final_url = ""  # Return empty string on error
    finally:
        driver.quit()  # Close the browser session

    return final_url  # Return the resolved final URL


# ----------------- PDF Handling -----------------


def download_pdf(final_url: str, output_dir: str) -> bool:
    filename = url_to_filename(final_url)  # Sanitize URL into a safe filename
    filepath = Path(output_dir) / filename  # Build the full file path

    if file_exists(filepath):  # Skip download if file already exists
        print(f"File already exists, skipping: {filepath}")
        return False

    try:
        resp = requests.get(
            final_url, timeout=900, stream=True
        )  # Download file with 15-min timeout
        resp.raise_for_status()  # Raise exception if HTTP status code is not 200

        content_type = resp.headers.get("Content-Type", "")  # Get response content type
        if not ("application/pdf" in content_type or "text/html" in content_type):
            print(
                f"Invalid content type for {final_url}: {content_type}"
            )  # Reject non-PDF responses
            return False

        with open(filepath, "wb") as f:  # Open file for binary writing
            for chunk in resp.iter_content(
                8192
            ):  # Stream in chunks to avoid memory issues
                f.write(chunk)

        print(f"Downloaded: {final_url} → {filepath}")  # Print success message
        return True
    except Exception as e:
        print(f"Failed to download {final_url}: {e}")  # Print failure message
        return False


# ----------------- Scraping -----------------


def get_data_from_url(uri: str) -> str:
    print(f"Scraping {uri}")  # Print which URL is being scraped
    try:
        resp = requests.get(uri, timeout=60)  # Send GET request with timeout
        resp.raise_for_status()  # Raise error if status code not OK
        return resp.text  # Return the page HTML
    except Exception as e:
        print(f"Error scraping {uri}: {e}")  # Print error if scraping fails
        return ""


def extract_pdf_urls(html: str):
    pdf_url_pattern = re.compile(
        pattern=r"https?://[^\s'\"]+/pdf/\?productID=\d+"
    )  # Regex for PDF links
    matches = pdf_url_pattern.findall(string=html)  # Find all matching URLs
    if not matches:  # Print if no matches found
        print("No PDF URLs found.")
    return matches  # Return list of PDF URLs


# ----------------- Main -----------------


def main():
    remote_api_urls = [  # List of initial HTML pages to scrape
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42015812-Natural-Deodorizers-Charcoal.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42012514-Natural-Deodorizers-Coconut.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42013627-Natural-Deodorizers-Juniper-Berry.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42014404-Natural-Deodorizers-Magnesium-Vanilla-Sandalwood.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42013628-Natural-Deodorizers-Orange-Citrus.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42013626-Natural-Deodorizers-Rosemary-Lavender.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42013629-Natural-Deodorizers-Unscented.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40002569-ultramax-clear-gel-cool-blast.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40500295-ultramax-solid-active-sport.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40500294-ultramax-solid-cool-blast.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40500296-ultramax-solid-fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40500293-ultramax-solid-powder-fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40500292-ultramax-solid-unscented.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40500987-arrid-dry-spray-invigorate.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40500986-arrid-dry-spray-renew.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42000042-arrid-xx-morning-clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42000044-arrid-xx-extra-dry-regular.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40002406-arrid-gel-cool-shower.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40002408-arrid-gel-morning-clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42000006-arrid-regular-scent-aerosol-aed.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42013064-arrid-solid-cool-shower.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40500396-arrid-solid-regular.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42013063-XX-Extra-Extra-Dry-Solid-Ultra-Fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/40500298-arrid-solid-unscented.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42000043-arrid-xx-ultra-fresh-ultra-clear.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/0384-Curash-Aloe-Vera-Chamomile-Wipes.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/3301061-Curash-Baby-Rash-Powder.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/3301062-Curash-Family-Medicated-Rash-Powder.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/F3143-Curash-Fragrance-Free-Wipes.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/ASM067-004-3150720-Curash-Gentle-Head-to-Toe-wash-CoC-CID.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/SPA064-025-3150721-Curash-Gentle-Shampoo-Conditioner-CoC-CID.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/T-CW011-Curash-Multi-purpose-Healing-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/SPA064-028-FORCW80C-Curash-Nappy-Rash-Cream-CoC-CID.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/F3138-Curash-Simply-Water-Baby-Wipes.aspx",
        "https://churchdwight.com/ingredient-disclosure/baby-care/0383-Curash-Vitamin-E-Wipes.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000845-ah-Baking-Soda.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42016832-ah-carpet-deodorizer-Fresh-breeze.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/400002792-ah-cat-litter-deodorizer.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40002486-ah-daily-litter-fragrance-booster.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40002388-ah-double-duty-litter-deodorizer.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40501130-ah-extra-strength-carpet-odor-eliminator.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42016832-Forever-Fresh-Cat-Litter-Deodorizer.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40500498-ah-fresh-scentsations-carpet-room-odor-eliminator-island-mist.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000004-Ah-Fresh%20Scentsations-Carpet-Odor-Eliminator-Island-Mist-Foam.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40501122-ah-carpet-deodorizer-fresh-breeze.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000020-ah-max-odor-eliminator.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40002783-ah-pet-fresh-carpet-odor-eliminator.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40500142-ah-plus-oxiclean-stain-and-odor-eliminator-for-carpet.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40002488-clean-shower-daily-shower-cleaner.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40501022-kaboom-Plus-Disinfex-3-in1-Bathroom-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000070-kaboom-scrub-free.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40002493-Hardwater-Trigger-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000223-orange-glo-hardwood-floor-4-in-1.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000164-orange-glo-everyday-hardwood-floor-cleaner.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000283-orange-glo-wood-furniture-2-in-1-clean-and-polish.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42011957-OxiClean-bathroom-cleaner-fresh-scent.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000278-oxiclean-carpet-and-area-rug-pet-stain-and-odor-remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40501230-oxiclean-carpet-area-rug-stain-remover-spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000005-OxiClean-foamtastic-citrus.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000010-OxiClean-foamtastic-fresh-scent.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40501215-Large-Area-Carpet-Cleaner.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40500092-OxiClean-mold-and-mildew-stain-remover-with-bleach.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42013688-Multipurpose-Daily-Clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42013706-Multipurpose-3in1-Deep-Clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40500415-OxiClean-shower-guard.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/40002295-Scrub-Free-Mildew-Stain-Remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000220-scrub-free-total-bathroom-cleaner-lemon-scent.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101702-ZICAM-Allergy-Relief-No-Drip-Liquid-Nasal-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/42016217-ZICAM-Cold-Flu-Like-Symptoms.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101706-ZICAM-Cold-Remedy-Medicated-Fruit-Drops%E2%80%93Assorted-Fruit.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101705-ZICAM-Cold-Remedy-Medicated-Fruit-Drops-Elderberry.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101709-ZICAM-ColdRemedy-Medicated-Fruit-Drops-Manuka-Honey-Lemon.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101707-ZICAM-Cold-Medicated-Fruit-Drops%E2%80%93Ultimate-Orange.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101718-ZICAM-Col-Remed-Medicate-Nasa-Swab.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101700-42016856-zicam-cold-remedy-nodrip-nasal-spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101701-ZICAM-Cold-Remedy-Oral-Mist-Arcti-Mint.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/42014475-ZICAM-Col-Remed-Pre-Cold-Fighte-Zinc-Elderberry-Lozengel.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101711-ZICAM-Cold-RemedyRapidMelts-Cherry.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101713-ZICAM-Cold-RemedyRapidMelts-Citrus.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101716-ZICAM-Cold-Remedy-RapidMelts-Citru-plus-Elderberry.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101712-ZICAM-Cold-Remedy-RapidMelts-Lemo-Lime.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/42018335-ZICAM-Cold-Remedy-RapidMelts-Nighttime-Concord-Grape.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101714-ZICAM-Cold-Remedy-Ultr-RapidMelts-Cherry.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101715-ZICAM-Cold-Remedy-Ultra-RapidMelts-Orange-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101710-ZICAM-Cold-Remedy-Wild-Cherry-Lozenges.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/42016147-42016359-ZICAM-Extrem-Congestion-Relief-No-Drip-Liquid-Nasal-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/42016146-42016354-ZICAM-Intense-Sinus-Relief-No-Drip-Liquid-Nasal-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/cough-allergy/40101719-ZICAM-Nasa-AllClear-Nasa-Swab.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40003025-aim-toothpaste-aim-multi-benefit-cavity-protection-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40003021-aim-toothpaste-kids.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40003018-aim-toothpaste-aim-multi-benefit-cavity-protection-red-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40003023-aim-toothpaste-aim-multi-benefit-tartar-control-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40003024-aim-toothpaste-aim-multi-benefit-whitening-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42010258-Arm-Hammer-Advanced-White-Baking-Soda-and-Peroxide.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40002536-arm-and-hammer-toothpaste-advance-white-breath-freshening.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42010259-arm-hammer-toothpaste-extreme-whitening-stain-defense.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300932-arm-and-hammer-advance-white-toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40500377-arm-hammer-toothpaste-truly-radiant-bright-and-strong.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40500907-arm-hammer-toothpaste-truly-radiant-clean-and-fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300829-Arm-Hammer%E2%84%A2-Charcoal-White.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300831-Arm-Hammer%E2%84%A2-Coconut-White.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40002537-Arm-Hammer-Complete-Care-All-in-1-Gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40500377-ah-complete-care-enamel-strengthening.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42014050-Complet-Car-Intense-Freshening.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40002971-ah-toothpaste-complete-care-whitening-stain-defense.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42014051-Arm-Hammer-Denta-Care-Original-Paste.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40002529-arm-hammer-toothpaste-dental-care.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42014052-Arm-Hammer-Enamel-Care.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42012468-arm-hammer-essentials-healthy-teeth-dental-care.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42012470-arm-hammer-essentials-activated-charcoal.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300447-arm-hammer-extra-white.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42014576-Arm-Hammer-%20Kids-Fruity-Bubble-Toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40002969-arm-hammer-toothpaste-orajel-sensitive-enamal-strength.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42010260-ah-toothpaste-peroxicare-tartar-control.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42016641-Breath-Fresheners-Icy-Mint.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40500630-40500631-arm-hammer-toothpaste-truly-radiant-rejuvenating.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40002970-arm-hammer-toothpaste-oj-sen-white-tartar-control.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300448-Arm-Hammer%E2%84%A2-Sensitive-Care.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40002968-Sensitive-Toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42014049-Arm-Hammer-White-Sparkle-Advance-White-Tartar-Control.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40003019-close-up-freshening.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40003017-close-up-whitening.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300457-Email-Diamant-Blancheur-Absolue.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300444-Email-Diamant-Double-blancheur.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300457-Email-Diamant-Formule-Rouge.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300788-Email-Diamant-Le-Charbon.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300450-Email-Diamant-White-Booster.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40003016-pepsodent-toothpaste-complete-care-original.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300468-Pearl-Drops-Instant-Natural-White.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300436-Pearl-Drops-Smokers-Tarter-Control-Strongmint-Gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300790-PERLWEISS-Exper-Weiss.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/300782-PERLWEISS-Regular.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101806-TheraBreath-Anticavity-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101809-Charcoal-Whitening-Fresh-Breath-Toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42017222-TheraBreath-Complete-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42016638-TheraBreath-Deep-Clean-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42017564-TheraBreath-Deep-Clean-Toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101814-Dry-Mouth-Lozenge-Mandarin-Mint.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101815-TheraBreath-Dry-Mouth-Lozenge-Tart-Berry.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101807-TheraBreath-Dry-Mouth-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101821-Fresh-Breath-Gums.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101802-Fresh-Breath-Icy-Mint-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101804-Fresh-Breath-Mild-Mint-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101810-Fresh-Breath-Mild-Mint-Toothpaste-with-Fluoride.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101811-Fresh-Breath-Mild-Mint-Toothpaste-without-Fluoride.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101805-Fresh-Breath-Plus-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101813-Fresh-Breath-PLUS-Toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101803-Fresh-Breath-Rainforest-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101801-Fresh-Healthy-Smile-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101800-Healthy-Gums-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42017566-TheraBreath-Healthy-Gums-Toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42017530-Kids-Bubblegum-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42016703-therabreath-overnight-rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42016070-Plaque-Control-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101819-Plus-Power-Drops.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/40101808-Whitening-Oral-Rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/42017563-TheraBreath-Whitening-Toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/3063861-ultrafresh-breath-spray-cool-mint.aspx",
        "https://churchdwight.com/ingredient-disclosure/dental-care/3066023-ultrafresh-breath-spray-fresh-mint.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300767-300640-Nair-Bikini-Brush-On.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42010553-sensitive-bikini-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42013123-Bladeless-Shave-Whipped-Cr%C3%A8me.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42013124-Bladeless-Shave-Whipped-Cr%C3%A8me-Lavender.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42013349-Bladeless-Shave-Whipped-Cr%C3%A8me-Rosewater.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42016530-Nair-Body-Cream-with-Oat-Milk-Vanilla.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42016528-nair-body-cream-with-aloe-water-lily.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300580-Nair-Coco-Butter-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42016527-Nair-body-cream-with-cocoa-butter-vitamin-e.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/C19334_1-Cold-Wax-Strips-Armpits%20-Bikini-Peach.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/C17344_4-Cold-Wax-Strips-Face-Milk-Honey.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/C22349_1-Cold-Wax-Strips-With-Organic-Aloe-Vera.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/40500274-nair-face-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/40002958-aloe-lanolin-cucumber-melon.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/40002957-nair-lotion-with-baby-oil.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300250-Nair-Kiwi-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/40002960-cocoa-butter.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300101-300359-Nair-Lemon-Lotion.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300398-Nair-Lemon-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42011656-Leg-Mask-with-Clay-Charcoal.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42011657-Leg-Mask-with-Clay-Seaweed.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42012133-Leg-Mask-with-Clay-Shea-Butter.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/7833V2-Nair-Bikini-Brush-On.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300490-Nair-Male-Depilatory-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/40500100-nair-men-hair-remover-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300620-Nair-Moisturizing-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42016525-Nair-Moroccan-Argan-Oil-Shower-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/40500312-shower-power-moroccan-argan-oil.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/40501221-40501222-nair-body-renewal.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/40501219-40501220-nair-nourish-skin-renewal-body.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42010508-nair-nourish-moroccan-argan-oil-sprays-away.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/Nair-Post-Depilatory-Oil.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42015408-Nair-Prep-Smooth-Face-Hair-Remover-Hydrating-with-Watermelon-Extract-Hyaluronic-Acid.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300100-300358-Nair-Rose-Lotion.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300397-Nair-Rose-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42016526-nair-sensitive-coconut-shower-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42016526-sensitive-formula-shower-power.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42015409-Sensitive-Prep-Smooth-Face-Hair-Remover-Soothing-with-Coconut-Milk-and-Collagen.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42014692-Nair-Sensitive-Chamomile-Wax-Strips.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42010576-shower-power-sensitive.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42013761-Spa-Sugar-Wax.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300725-Nair-Tough-Hair.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/300725-Nair-Underarm-and-Bikini-Moisturizing-Hair-Removal.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/42010440-nair-bikini-pro-wax-kit.aspx",
        "https://churchdwight.com/ingredient-disclosure/depilatories/C17330-3-Nair-Wax-Ready-Strips-Orchid-Cherry-Blossom-Extracts.aspx",
        "https://churchdwight.com/ingredient-disclosure/Digestive-Relief/40000050-Carters-Little-Pills.aspx",
        "https://churchdwight.com/ingredient-disclosure/Digestive-Relief/42015788-Gastrovol-Liquid-Gels.aspx",
        "https://churchdwight.com/ingredient-disclosure/Digestive-Relief/40000152-vol-Baby-Drops-30ML-40MG.aspx",
        "https://churchdwight.com/ingredient-disclosure/Digestive-Relief/40000155-Regular-Strength-Tablets.aspx",
        "https://churchdwight.com/ingredient-disclosure/Digestive-Relief/42014289-Ultra-Strength-Capsules.aspx",
        "https://churchdwight.com/ingredient-disclosure/Digestive-Relief/40000149-Ultra-Strength-Tablets.aspx",
        "https://churchdwight.com/ingredient-disclosure/dryer-sheets/40002591-Fabric-Softener-Sheets-Clean-Mountain.aspx",
        "https://churchdwight.com/ingredient-disclosure/dryer-sheets/42000105-Fabric-Softener-Sheets-Purifying-Waters.aspx",
        "https://churchdwight.com/ingredient-disclosure/dryer-sheets/42000104-Fabric-Softener-Sheets-Tropical-Paradise.aspx",
        "https://churchdwight.com/ingredient-disclosure/dryer-sheets/40002593-Fabric-Softener-Sheets-Lavender-White-Linen.aspx",
        "https://churchdwight.com/ingredient-disclosure/dryer-sheets/40002594-Fabric-Softener-Sheets-Mountain-Rain.aspx",
        "https://churchdwight.com/ingredient-disclosure/dryer-sheets/42015375-Fabric-Softener-Sheets-Fresh-Botanical.aspx",
        "https://churchdwight.com/ingredient-disclosure/dryer-sheets/42015294-Fabric-Softener-Sheets-Odor-Blasters.aspx",
        "https://churchdwight.com/ingredient-disclosure/dryer-sheets/40002897-Fresh-Soft-Fabric-Softener-Sheets-Perfume.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/300808-FemFresh-Sensitive-Wash.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/2484-FemFresh-Sensitive-Wipes.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/300563-FemFresh-Active-Fresh-Deodorant.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/300810-FemFresh-Active-Wash.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/300564-FemFresh-Daily-Deodorant.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/300807-FemFresh-Daily-Intimate-Wash.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/CD4001776-Daily-Powder.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/2466-FemFresh-Daily-Wipes.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/42014873-FemFresh-Intimate-Foam-Oat-N-Shea.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/42014838-FemFresh-Intimate-Foam-Rose-Cotton-Flower.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/300809-FemFresh-Soothing-Wash.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/42014606-Pre-Seed-Fertility-Lubricant.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/42011905-Odor-Eliminating-Gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/42011501-cooling-relief-spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/42000263-replens-long-lasting-vaginal-moisturizer-applicator.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/42000254-replens-long-lasting-vaginal-moisturizer-tube.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/40501273-replens-external-comfort.aspx",
        "https://churchdwight.com/ingredient-disclosure/feminine-hygiene/42000266-replens-silky-smooth-personal-lubricant.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/2070A-Batiste-1-Day-Express-Hair-Color-Deep-Teal.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/2067A-Batiste-1-Day-Express-Hair-Color-Rose-Quartz.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/2068A-Batiste-1-Day-Express-Hair-Color-Stardust-Shimmer.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/2068A-Batiste-1-Day-Express-Hair-Color-Wild-Viole.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/ASM102-021-batiste-24h-active.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/ASM102-022-batiste-24h-fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000084-batiste-bare.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000046-batiste-beautiful-brunette.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000013-batiste-blush.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000048-batiste-brilliant-blond.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42017180-batiste-cucumber-cooler.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000049-batiste-cherry.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014383-Batiste-Cozy-Cashmere.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014259-Batiste-Defrizzing-Dry-Shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000014-batiste-divine-dark.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42012937-batiste-detoxifying-overnight-dry-shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000045-batiste-fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42012942-benefitscolorProtectShampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014548-Hair-Mask-Repair.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014546-Hair-Mask-Smooth.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014547Hair-Mask-Strengthen.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/GB026-171-Batiste-Happy-90s.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42013833-Batiste-Dry-Shampoo-Heavenly-Volume.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015062_42013827-Batiste-Dry-Shampoo-Blonde.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015061_42013829-Batiste-Dry-Shampoo-Brunette.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015060_42013831-Batiste-Dry-Shampoo-Dark.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42011459-Hydrating-Dry-Shampoobrunette.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42017232-batiste-light-mellow-melon.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42017468-batiste-lightzen-matcha.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42018226-limited-edition-courtside-couture.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014394-Batiste-Love-Love.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014614-Batiste-Luxe.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/AR016-115-Batiste-Naughty.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014500-Naturally-Bamboo-Gardenia.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014499-Naturally-Green-Tea-Chamomile.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014501-Batiste-Naturally-Hemp-Coconut.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/AR016-114-Batiste-Nice.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000007-batiste-original.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015151_42012937-Batiste-Overnight.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42011394-Batiste-Pink-Pineapple.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42018050-Powder-Dry-Shampoo-Bare.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42018049-Powder-Dry-Shampoo-Original.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42018051-Powder-Dry-Shampoo-Unscented.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015093-Batiste-Radiance.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42010734-Batiste-Rose-Gold.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/GB026-158-Batiste-Star-Kissed.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014600-Batiste-Self-Love.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42010734-Batiste-Rose-Gold.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/ASM067-084-Batiste-Summer-Escape.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42016482-Batiste-Sweat-Activated.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000062-batiste-sweetie.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015180_42015698-Texturizing-Dry-Shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42016480-Batiste-Touch-Activated.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42014319-Touch-of-Gloss.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42000051-batiste-tropical.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/PSS084-069-batiste-unwind.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/420150636_42011458-Batiste-Volumizing-Dry-Shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42012338-Waterless-Cleansing-Foam-Hydrate.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42012335-Waterless-Cleansing-Foam-Shine.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42012337-Waterless-Cleansing-Foam-Smooth.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42012336-Waterless-Cleansing-Foam-Strength.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/GB053-156-Waterless-Conditioning-Foam-Blush.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/GB053-151-Waterless-Conditioning-Foam-Original.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/GB053-152-Waterless-Conditioning-Foam-Tropical.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015054_42014145_GB026-148-batiste-Dry-Shampoo-Wildflower.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42010734-Batiste-Wonder-Woman.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/ASM067-039-Batiste-XXL-Styling.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/Batiste-XXL-Volume-Dry-Shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/toppik-brow-building-fibers-set.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/toppik-colored-hair-thickener.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/toppik-fiber-hold-spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42016633-Fill-Me-In-Hairline-Filler-Black.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42016634-Fill-Me-In-Hairline-Filler-Dark-Brown.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42016636-Fill-Me-In-Hairline-Filler-Medium-Blonde.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42016635-Fill-Me-In-Hairline-Filler-Medium-Brown.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/toppik-hair-building-conditioner.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/toppik-hair-building-fibers-all.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/toppik-hair-building-shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42012025-Toppik-Hair-Fattener.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/toppik-root-touch-up-spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015328-Viviscal-Exfoliating-Scalp-Scrub.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-woman-supplement.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-densifying-elixir.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42013106-Hair-Therapy-Beauty-Stress-Relief.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015330-Viviscal-Hair-Thickening-Serum.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-man-fortifying-shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-man-supplement.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-man-supplement-collagen-blend.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-pro-elixir.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-pro-shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-pro-supplement.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-pro-conditioner.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015492-Viviscal-Scalp-Nourish.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015327-Viviscal-Strengthening-Conditioner.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015326-Viviscal-Thickening-Shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/42015090-Viviscal-Volumizing-Dry-Shampoo.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-woman-supplement.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/viviscal-woman-supplement-collagen-blend.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/xfusion-fiber-hold-spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/xfusion-hair-fattener-advanced-thickening-serum.aspx",
        "https://churchdwight.com/ingredient-disclosure/hair-care/xfusion-keratin-hair-fibers-all-shades.aspx",
        "https://churchdwight.com/ingredient-disclosure/hand-sanitizer/42013194-Anti-Bacterial-Hand-Sanitizer.aspx",
        "https://churchdwight.com/ingredient-disclosure/hemorrhoid-relief/42014336-Anusol-Cleansing-Wipes.aspx",
        "https://churchdwight.com/ingredient-disclosure/hemorrhoid-relief/42014464-Anusol-Multi-symptom-Ointment.aspx",
        "https://churchdwight.com/ingredient-disclosure/hemorrhoid-relief/42014249-Anusol-Multi-symptom-Suppository.aspx",
        "https://churchdwight.com/ingredient-disclosure/hemorrhoid-relief/40076002-Anusol-plus-Ointment.aspx",
        "https://churchdwight.com/ingredient-disclosure/hemorrhoid-relief/40076003-Anusol-plus-Suppository.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500935-ah-plus-oxiclean-4-in-1-power-paks.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42013871-5-in-1-Power-Paks-Clean-Burst.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42010865-ah-sensitive-scents-5-in-1-power-paks.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015520-Arm-Hammer-Baby-Cuddly-Clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42012557-Care-Rewear-Clothing-Refresher-Mist-Delightful-Denim.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42012561-Care-Rewear-Clothing-Refresher-Mist-Original.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011801-ah-clean-scentsations-scent-booster-clean-meadow.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015482-Liquid-Laundry-Detergent-Crisp-Clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011809-arm-hammer-scent-booster-maui-sunset.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500734-arm-hammer-scent-booster-purifying-waters.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011323-ah-clean-scentsations-scent-booster-tropical-paradise.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42010990-arm-hammer-scent-booster-fresh-burst.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42017665-Arm-Hammer-Deep-Clean-Liquid-Laundry-Detergent.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42017907-arm-hammer-Deep-Clean-Free-Power-Paks.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42016512-arm-hammer-deep-clean-odor-power-paks.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42016428-arm-hammer-deep-clean-stain-power-paks.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42013367-Scent-Booster-Lavendar-Escape-Crisp-Clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42013368-Scent-Booster-Lavendar-Escape.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42017170-lightscent-booster-peony-blossom.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015594-Liquid-Laundry-Detergent-Deep-Clean-Odor%E2%80%93Radiant-Burst.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015590-Liquid-Laundry-Detergent-Deep-Clean-Stain%E2%80%93Sparkling-Clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015441-ah-laundry-detergent-2-in-1-orchard-bloom.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015484-ah-laundry-detergent-clean-burst.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015525-ah-laundry-detergent-perfume-and-dye-free.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015522-ah-laundry-detergent-sensitive-skin-plus-scent.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015527-ah-detergent-clean-scentsations-trop-paradise.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018468-Odor-Blasters-Fabric-Rinse-Fresh-Burst.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018470-Odor-Blasters-Fabric-Rinse-Fresh-Escape.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42016265-Odor-Blasters-Scent-Booster%E2%80%93Fresh-Botanicals.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42016266-Odor-Blasters-Scent-Booster%E2%80%93Fresh-Escape.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011907-ah-detergent-bleach-alternative-clean-burst.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011163-ah-plus-oxiclean-stainfighters-5-in-1-power-paks-odor-blasters.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40501324-Plus-Oxiclean-5-in-1-Unit-Dose-Fresh-Scent.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42012848-ah-plus-oxiclean-fresh-scent-plus-stain-fighters.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015532-ah-plus-oxiclean-liquid-detergent-clean-meadow.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015535-ah-plus-oxiclean-liquid-fade-defense-sparkling-waters.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015531-ah-plus-oxiclean-liquid-fresh-scent-cool-breeze.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42016063-ah-plus-oxiclean-liquid-laundry-odor-blasters-fresh-botanicals.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015533-ah-plus-oxiclean-liquid-laundry-odor-blasters.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015340-ah-plus-oxi-max-liquid-detergent-fresh-scent.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42012117-ah-plus-oxiclean-super-concentrated.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011926-ah-complete-crisp-clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002389-ah-powder-laundry-detergent-alpine-clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002337-ah-powder-laundry-detergent-clean-burst.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500234-powder-detergent-plus-oxiclean-crisp-clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002380-arm-hammer-powder-laundry-free.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42012971-arm-hammer-powder-detergentBag-FreeofPerfumes.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002341-ah-powder-laundry-detergent-plus-oxiclean.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42016386-Power-Sheets-Laundry-Detergent%E2%80%93Fresh-Free.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42016191-Power-Sheets-Laundry-Detergent%E2%80%93Fresh-Linen.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42017360_Arm-Hammer%E2%84%A2Power-Sheets-Laundry-Detergent-Fresh-Breeze.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002697-arm-hammer-super-washing-soda.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42017168-arm-Hammer-scent-booster-cool-woods.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500533-oxiclean-maxforce-pre-treat-spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002384-oxi-versatile-stain-remover-baby-stain-soaker.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002368-oxiclean-color-boost-fresh-scent.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002369-oxiclean-color-boost-perfume-and-dye-free.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500067-oxi-pwr-crystals-color-shield-single-chamber.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011772-oxiclean-dark-protect-liquid.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011773-oxiclean-dark-protect-powder.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42013621-Clear-Liquid-Laundry-Booster.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40501323-oxiclean-sparkling-fresh-triple-chamber.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42013603%20-Laundry-Home-Sanitizer.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015222-Oxiclean-Laundry-Stain-Remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015223-Oxiclean-Laundry-Stain-Remover-Free.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40501313-oxiclean-refreshing-lavender-and-lily.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40501312-oxiclean-sparkling-fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011756-Max-Efficiency-Laundry-Stain-Remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018216-Oxiclean-Max-Force-Advanced-Stain-Remover-Powder.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500533-oxiclean-maxforce-laundry-stain-remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011756-oxiclean-max-efficiency-odor-stain-remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018104-oxiclean-maxforce-liquid-additive-laundry-stain-remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500737-oxiclean-maxforce-gel-stick.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018346-OxiClean-Max-Force-Power-Paks.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018475_OxiCleanTM-Odor-BlastersTM-Clean-Rinse-Fabric-Rinse-Sparkling-Fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018286-Oxiclean-Blasters-Max-Efficiency-Stain-Remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42016200-Odor-Blaster-Power-Paks.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015225-oxiclean-pre-treat-max-efficiency-laundry-stain-remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018220-oxiclean-triple-action-odor-blaster.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018218-Oxiclean-3X-Versatile-Stain-Remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018219-Oxiclean-3X-Versatile-Stain-Remover-Free.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42018217-Oxiclean-Triple-Action-White-Revive-Laundry-Whitener-and-Stain-Remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002385-oxiclean-versatile-stain-remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40002383-oxi-versatile-stain-remover-fragrance-free.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015219-oxi-versatile-stain-remover-club-compaction.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500711-oxiclean-versatile-stain-remover-odor-blaster.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500547-oxiclean-washing-machine-cleaner.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500666-oxiclean-white-revive-laundry-stain-remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40500413-oxi-white-revive-power-pak-laundry-stain-rmvr.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/40501171-oxiclean-white-revive-whitener-and-stain-remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42011155-oxiclean-odor-blasters-odor-stain-remover-liquid.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015438-xtra-liquid-laundry-detergent-summer-fiesta.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015805-xtra-liquid-laundry-detergent-lavender-and-sweet-vanilla.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42017717-42017724-42017725-liquid-laundry-detergent-plus-odor-blasters-fresh-scent.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42012706-Liquid-Laundry-Detergent-Long-Lasting-Freshness-Sparkling-Fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015435-xtra-liquid-laundry-detergent-mountain-rain.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015436-xtra-liquid-laundry-detergent-tropical-passion.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015803-xtra-liquid-plus-oxiclean-laundry-detergent-mountain-rain.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015804-xtra-plus-oxiclean-liquid-laundry-detergent-crystal-clean.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42010948-xtra-plus-oxiclean-powder-laundry-detergent-summer-breeze.aspx",
        "https://churchdwight.com/ingredient-disclosure/laundry-fabric-care/42015437-xtra-liquid-laundry-detergent-calypso-fresh.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/40500290-simply-saline-instant-relief.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/40500443-simply-saline-nighttime-nasal-mist.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/40500340-simply-saline-extra-strength-severe-congestion.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/40500337-simply-saline-baby-nasal-relief-mist.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/42017425-simply-saline-moisture-and-soothe-with-aloe.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/505231-505234-Sterimar-Allergic-Nose.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/503425-503426-Sterimar-Baby-Bloked-Nose.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/503421-503424-Sterimar-Baby-Hygiene-Comfort.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/504144-Sterimar-Baby-Stop-Protect-cold-Sinus.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/503834-503840-Sterimar-Blocked-Nose.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/502514-Sterimar-Ear.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/503865-503871-Sterimar-Hygiene-Comfort.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/503838-503874-Sterimar-Nose-Prone-to-Colds.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/503842-503843-Sterimar-Sensititve-Nose.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/505713-Sterimar-Sinusitis-Very-Blocked-Nose.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/22054-05-Sterimar-Soothing-Nasal-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/503886-Sterimar-Stop-Protect-Allergy-Response.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/503888-Sterimar-Stop-Protect-Irritations.aspx",
        "https://churchdwight.com/ingredient-disclosure/nasal-care/13081-25-Stop-Protect-Very-Blocked-Nose.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40501367-Gravol-Comfort-Shaped-Suppositories.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/42013299-Gravol-Ginge-Chewabl-Lozenges.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40500256-Gravol-Ginger-Liquid-Gel-Capsule.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40002859-Gravol-Ginger-Multi-symptom-Cold-Fever.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40501085-Gravol-Ginger-Nighttime.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40000118-Gravol-Ginger-Tablets.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/42015020-Ginger-Traveler-Shield-Probiotic.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40000109-IM-Dimenhydrinate-Injection.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40000121-Gravol-Immediate-Release-Long-Acting-Caplets.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40000113-Gravol-Motion-Sickness-Relief-oated-Tablets.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/42013506-Gravol-Motion-Sickness-Relief.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40500832-Gravol-Quick-Dissolve-Chewable.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40501367-Kids-Comfort-Shaped-Suppositories.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40000110-Kids-Gravol-Liquid.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40501258-Kids-Gravol-Liquid-Dye-Free.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40501258-Kids-Gravol-Motion-Sickness-Relief-Syrup.aspx",
        "https://churchdwight.com/ingredient-disclosure/Nausea-Relief/40501086-Kids-Gravol-Quick-Dissolve-Chewable.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42014159-Cooling-Tablets-for-Teething-with-Vitamin-D.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011229-42011230-Non-Medicated%20Cooling%20Gels%20for%20Teething.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011953-baby-orajel-non-medicated-cooling-swabs-for-teething.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40500754-40500755-baby-orajel-tooth-gum-cleanser.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/ORAS7913-1-DELABARRE-Gingival-Gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42015912-orajel-2X-strength-toothache-gum-medicated-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011630-orajel-3X-medicated-mouth-sore-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40500591-orajel-alcohol-free-antiseptic-mouth-sore-rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40500633-40500069-orajel-anticavity-fluoride-toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40500594-orajel-antiseptic-mouth-sore-rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011892-orajel-denture-pain-3x-medicated-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011631-orajel-double-medicated-cold-sore-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40501206-orajel-toothache-double-medicated-rinse.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40500753-40500756-orajel-fluor-free-training-paste.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011895-Gum-Pain-3X-Medicated-Gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42013386-Kids-Anticavity-Fluoride-Toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42013382-Kids-Fluoride-Free-Training-Toothpaste.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40002640-orajel-maximum-strength-toothache-oral-pain-relief-swabs.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40002640-orajel-maximum-strength-toothache-pain-relief-swabs.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40002657-orajel-medicated-nighttime-teething-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40501116-orajel-moisturelock-cold-sore-treatment.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40002640-orajel-mouth-sore-swabs.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40002645-orajel-regular-mild-toothache-relief-medicated-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40501058-orajel-severe-pm-toothache-triple-med-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40501186-orajel-severe-toothache-gum-relief-plus-double-med-liquid.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40501057-orajel-severe-toothache-gum-relief-plus-triple-med-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40501059-orajel-severe-toothache-gum-relief-plus-triple-med-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/40501186-orajel-severe-toothache-double-medicated-liquid.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011564-orajel-Toothache-Stripsswabs.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011895-orajel-toothache-gum-3X-medicated-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011934-orajel-toothache-gum-4X-medicated-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011892-orajel-toothache-gum-4X-medicated-gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42011935-orajel-toothache-gum-4X-medicated-nighttime-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/oral-care/42000190-orajel-touch-free-cold-sore-treatment.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/0119-Dencorub-Arthritis-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/0129-Dencorub-Dual%20Action-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/0106-Dencorub-Extra-Strength-Heat-Gel.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/0141-0144-Dencorub-Pain-Relieving-Heat-Patches.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/42000273-Legatrinpm.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/40501359-Arthritis-Flare-Up-Relief-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/42014489-Arthritis-Pain-Relief-Heat-Roll-On-Lotion.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/42015696-Foot-Cooling-Soothing-Relief-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/40000166-Injury-Gel-Ice.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/40000172-Injury-Ice-to-Heat-Relief-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/40501362-MUSCLE-JOINT-EXTRA-STRENGTH-HEAT.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/40000173-Muscle-Joint-Maximum-Strength-Heat.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/42014449-Muscle-Joint-No-Odour-Regular-Strength-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/42014450-Muscle-Joint-No-Odour-Extra-Regular-Strength-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/40501363-Muscle-Joint-Regular-Strength-Heat.aspx",
        "https://churchdwight.com/ingredient-disclosure/pain-relief/40501360-Natural-Source-Arnica-Cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/42011640-ah-Breathe-Easy-Clumping-Litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/42011990-42012376-42016608-cloud-control-platinum-cat-litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40002235-ah-double-duty.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40500556-arm-hammer-double-duty-complete-cat-litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/42014571_42014572-Cedarwood-Scented-Cat-Litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/42014125-Lavender-Scented-Cat-Litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/42015187-Arm-Hammer-Hardball-Clumping-Litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/62011585-Health-IQ-Crystals.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40500717-ah-multicat.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40002302-ah-multicat-unscented.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/42017812-Plant-POWER-Clumping-Litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40501290-ah-slide-multi-cat.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40501292-ah-slide-nonstop-odor-control.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/42011582-42012716-42012381-slide-platinum-cat-litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40002300-ah-super-scoop-fragrance-free.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40500715-Super-Scoop-Fresh-Cat-Litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40002954-ah-ultra-last.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/42014712-42014713-Ultra-Last-Unscented-Cat-Litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/clump-and-seal/42012754-Clump-Seal-Absorb-Multi-Cat.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/clump-and-seal/42012864-Clump-Seal-Absorb-Multi-Cat-Unscented.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/clump-and-seal/40500670-clump-seal-fresh-home.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/clump-and-seal/40500644-clump-seal-lw-fresh-scent.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/clump-and-seal/40500650-clump-seal-lw-multicat.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/clump-and-seal/40501308-clump-seal-microguard.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/arm-and-hammer/40500349-clump-seal-multi-cat-litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/clump-and-seal/40500349-42016580-clump-seal-multi-cat-litter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/clump-and-seal/40500846-clump-seal-lw-hhs-powerseal.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/clump-and-seal/40500757-clump-seal-power-seal.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/essentials/40500097-Essentials-Naturals-Double-Duty-CatLitter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/essentials/42000149-Essentials-Naturals-Multi-CatLitter.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/feline-pine/40500869-40500870-feline-pine-clumping.aspx",
        "https://churchdwight.com/ingredient-disclosure/pet-care/feline-pine/40002978-40500767-40500678-fp-nonclump.aspx",
        "https://churchdwight.com/ingredient-disclosure/pool-products/42000141-arm-hammer-clear-balance.aspx",
        "https://churchdwight.com/ingredient-disclosure/sexual-health/42013964-Delay-Spray.aspx",
        "https://churchdwight.com/ingredient-disclosure/sexual-health/40500113-trojan-lubricants-arouses-intensifies.aspx",
        "https://churchdwight.com/ingredient-disclosure/sexual-health/40500378-trojan-lubricants-arouses-releases.aspx",
        "https://churchdwight.com/ingredient-disclosure/sexual-health/60501046-Trojan-Lubricants-Bareskin.aspx",
        "https://churchdwight.com/ingredient-disclosure/sexual-health/trojan-lubricants-explore.aspx",
        "https://churchdwight.com/ingredient-disclosure/sexual-health/40500706-trojan-lubricants-h2o-closer.aspx",
        "https://churchdwight.com/ingredient-disclosure/sexual-health/40500704-trojan-lubricants-h2o-sensitive-touch.aspx",
        "https://churchdwight.com/ingredient-disclosure/sexual-health/60501046-Trojan-Lubricants-Bareskin.aspx",
        "https://churchdwight.com/ingredient-disclosure//sexual-health/42011341-trojan-lubricants-magnum.aspx",
        "https://churchdwight.com/ingredient-disclosure/sexual-health/42011815-trojan-lubricants-willa.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/42017017-hero-cosmetics-bright-eyes-Illuminating-eye-cream.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101331-hero-cosmetics-clear-collective-balancing-capsule-toner.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101327-hero-cosmetics-clear-collective-clarifying-prebiotic-moisturizer.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101329-hero-cosmetics-clear-collective-exfoliating-jelly-cleanser.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101312-hero-cosmetics-clear-collective-gentle-milky-cleanser.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/42016977-Hero-Cosmetics-Dark-Spot-Correct.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/42018286-Oxiclean-Blasters-Max-Efficiency-Stain-Remover.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101311-hero-cosmetics-force-shield-superfuel-serum-stick.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101317-hero-cosmetics-force-shield-spf-30.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/42016959-hero-cosmetics-glow-balm.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101325-hero-cosmetics-lightning-swipe.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101302-40101307-hero-cosmetics-micropoint-blemishes.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101301-hero-cosmetics-micropoint-dark-spots.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/42017603-hero-cosmetics-mighty-patch-fine-lines.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/42017031%20Hero%20Cosmetics%20Mighty%20Patch%E2%84%A2%20for%20Tired%20Eyes.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101300-40101303-hero-cosmetics-mighty-patch-original.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101319-hero-cosmetics-pimple-correct.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101320-hero-cosmetics-pore-release.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/42016980-hero-cosmetics-pore-purity-clay-mask.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101328-hero-cosmetics-rescue-balm.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101326-hero-cosmetics-rescue-retinol.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101323-hero-cosmetics-rescue-balm-red-correct.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/40101324-hero-cosmetics-rescue-balm-dark-spot-retouch.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/12011.02-amincissant-ventres-culpt.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/12051.20-Intense-Scrub.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/SD12332.17V2-Slimming-J-14.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/SFB-O06-Slimming-Concentrate-Cafei-Sculpt.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/SFB-N40-Slimming-Duo-Sculpt-2in1-Slimming-Serum-Glove.aspx",
        "https://churchdwight.com/ingredient-disclosure/skin-care/3154544-prickly-heat-powder.aspx",
        "https://churchdwight.com/ingredient-disclosure/wound-care/42000173-simply-saline-wound-wash-3-in-1.aspx",
        "https://churchdwight.com/ingredient-disclosure/wound-care/42000165-simply-saline-wound-wash-sterile-saline.aspx",
        "https://churchdwight.com/ingredient-disclosure/cleaning-products/42000845-ah-Baking-Soda.aspx",
        "https://churchdwight.com/ingredient-disclosure/commercial-professional/42000023-Carpet-Allergen-Reducer-Odor.aspx",
        "https://churchdwight.com/ingredient-disclosure/commercial-professional/42000025-ah-deodorizing-air-freshener.aspx",
        "https://churchdwight.com/ingredient-disclosure/commercial-professional/42000019-ah-fabric-carpet-foam-deodorizer.aspx",
        "https://churchdwight.com/ingredient-disclosure/commercial-professional/42000844-ah-fridge-n-freezer.aspx",
        "https://churchdwight.com/ingredient-disclosure/commercial-professional/42000164-ah-hard-surface-cleaner.aspx",
        "https://churchdwight.com/ingredient-disclosure/antiperspirant-deodorant/42015812-Natural-Deodorizers-Charcoal.aspx",
        "https://churchdwight.com/ingredient-disclosure/commercial-professional/42000024-ah-trash-can-dumpster-deodorizer.aspx",
    ]
    output_dir = "PDFs"  # Directory to store downloaded PDFs

    if not directory_exists(path=output_dir):  # Create directory if it does not exist
        create_directory(path=output_dir)

    get_data = []  # Store all scraped HTML data
    for url in remote_api_urls:
        html = get_data_from_url(url)  # Fetch page HTML
        get_data.append(html)

    final_pdf_list = extract_pdf_urls(
        "".join(get_data)
    )  # Extract PDF links from combined HTML
    final_pdf_list = remove_duplicates(seq=final_pdf_list)  # Remove duplicate PDF URLs

    for pdf_url in final_pdf_list:
        resolved_url: str = get_final_url(input_url=pdf_url)  # Resolve final URL after redirects
        if is_url_valid(url=resolved_url):  # Validate URL format
            download_pdf(final_url=resolved_url, output_dir=output_dir)  # Download the PDF


if __name__ == "__main__":  # Entry point for script
    main()
