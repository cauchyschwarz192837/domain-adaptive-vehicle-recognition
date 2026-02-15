from PIL import Image
from io import BytesIO
import requests
import json
import os
import time

#-----------------------------------------------
"""
BASE_URL = "https://apim.dealix.com/vis/v3/prod/get-inventory"
image_folder = "images_cars"
os.makedirs(image_folder, exist_ok=True)

GET_LIST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "Accept": "application/json",
    "se-aw": "d0fccada64f04a5180785e81fdd4bdec"
}

zip_codes = ["94506", "94016", "90210", "10001", "30301"]  # TESTING

metadata_list = []
image_count = 0

for zip_code in zip_codes:
    page = 1
    while True:
        params = {
            "SourceID": "33378",
            "Radius": "50",
            "Zip": zip_code,
            "PageCurrent": page,
            "PageSize": 20,
            "SortBy": "none"
        }

        try:
            response = requests.get(BASE_URL, params=params, QUERY_CARFAX_LIST=GET_LIST_HEADERS, timeout=10)
            data = response.json()
            cars = data.get("carsForSale", [])

            if not cars:
                break

            for car in cars:
                make = car.get("make", "N/A")
                model = car.get("model", "N/A")
                color = car.get("exteriorColor", "N/A")
                image_url = car.get("imageUrl", "")

                if not image_url:
                    continue

                try:
                    img_response = requests.get(image_url, QUERY_CARFAX_LIST={"User-Agent": GET_LIST_HEADERS["User-Agent"]}, timeout=10)
                    if img_response.status_code == 200:
                        img = Image.open(BytesIO(img_response.content))
                        filename = f"car_{image_count}.jpg"
                        filepath = os.path.join(image_folder, filename)
                        img.save(filepath)

                        metadata_list.append({
                            "filename": filename,
                            "make": make,
                            "model": model,
                            "color": color,
                            "imageUrl": image_url,
                            "zip": zip_code,
                            "page": page
                        })

                        print(f"Saved {filename}")
                        image_count += 1
                except requests.RequestException as e:
                    print(f"Can't download: {e}")

            page += 1
            time.sleep(0.5)

        except Exception as e:
            break

with open("car_metadata.json", "w") as f:
    json.dump(metadata_list, f, indent=4)
"""

#-----------------------------------------------------------------------------------------------------------
# If the scraping process is INTERRUPTED, remember to:
# 1. update image_count to the latest number,
# 2. rename the currently compiled JSON file to prevent overwriting of images or existing JSON
#    when resuming the code
# 3. remove completed models from the dictionary 
# 4. the separate JSON files can be easily merged later

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import requests
import json
import hashlib

def makecap(make, model, color):
    return f"{color.lower()} {make} {model}"

makemodeldict = {

    #--------------------------------------------------------------------
    # THESE ARE THE COMPLETED MODELS (INFORMATION CAN BE FOUND IN JSON, IMAGES CAN BE FOUND IN "carfax_images" DIRECTORY)):
    #
    # "Acura": ["ADX", "ILX", "Integra", "MDX", "NSX", "RDX", "RLX", "TLX","CL", "CSX", "EL", "Legend", "RL", "RSX", "SLX", "TL", "TSX",
    #          "Vigor", "ZDX"],
    # "Alfa Romeo": ["4C", "Giulia", "Stelvio", "Tonale", "164", "8C Competizone", "8C Spider", "GTV", "Milano", "Spider"],
    # "Audi": ["A3", "A4", "A5", "A6", "A7", "A8", "Allroad", "Q3", "Q4 e-tron", "Q5", "Q6 e-tron", "Q7", "Q8 e-tron", "Q8", "R8", "RS Q8"],
    # "BMW": ["2 Series", "3 Series", "4 Series", "5 Series", "6 Series", "7 Series", "8 Series", "M2", "M2 CS", "M2 Competition", "M3", 
    #         "M4", "M5", "M6"
    #--------------------------------------------------------------------
    # !TODO
    
    "BMW": ["M7", "M8", "X1", "X2", "X3 M", "X4", "X4 M", "X5", "X5 M", "X6", "X6 M", "X7", "XM", "Z4", "i3", "i4", "i5",
            "i7", "i8", "iX", "1 Series", "Alpina", "L7", "M", "M Roadster", "Z3", "Z4M", "Z8"],
    "Buick": ["Cascada", "Enclave", "Encore", "Encore GX", "Envision", "Envista", "LaCrosse", "Regal", "Allure", "Century", "Electra",
              "LeSabre", "Lucerne", "Park Avenue", "Rainier", "Reatta", "Rendezvous", "Riviera", "Roadmaster", "Skyhawk", "Skylark",
              "Somerset", "Terraza", "Verano"],
    "Cadillac": ["ATS", "CT4", "CT5", "CT6", "CTS", "Escalade", "Escalade IQ", "Lyriq", "Optiq", "Vistiq", "XT4", "XT5", "XT6", "XTS", 
                 "Allante", "Brougham", "Catera", "Cimarron", "DTS", "DeVille", "ELR", "Eldorado", "Fleetwood", "SRX", "STS", "Seville",
                 "Sixty Special", "XLR"],
    "Chevrolet": ["Blazer", "Blazer EV", "Bolt EUV", "Bolt EV", "BrightDrop", "Camaro", "City Express", "Colorado", "Corvette", "Cruze",
                  "Equinox", "Equinox EV", "Express", "Impala", "Malibu", "Silverado 1500", "Silverado 2500HD", "Silverado 3500HD", 
                  "Silverado EV", "Sonic", "Spark", "Suburban", "Tahoe", "TrailBlazer", "Traverse", "Trax", "Volt",
                  "Astro", "Avalanche 1500", "Avalanche 2500", "Aveo", "Beretta", "C/K 10", "C/K 1500", "C/K 20", "C/K 2500", "C/K 30",
                  "C/K 3500", "Caprice", "Captiva Sport", "Cavalier", "Celebrity", "Chevette", "Citation", "Cobalt", "Corsica", "D30",
                  "El Camino", "G-Series", "HHR", "HHR Panel", "Lumina", "Luv", "Malibu Classic", "Malibu Maxx", "Metro", "Monte Carlo",
                  "Nova", "Optra", "Orlando", "P20", "P30", "Prizm", "R/V 10", "R/V 20", "R/V 30", "R/V 3500", "S-10", "SS", "SSR",
                  "Silverado 1500HD", "Silverado 2500", "Silverado 3500", "Silverado Hybrid", "Spark EV", "Spectrum", "Sprint",
                  "Suburban 10", "Suburban 1500", "Suburban 20", "Suburban 2500", "Tracker", "Uplander", "Venture"],
    "Chrysler": ["300", "Pacifica", "Voyager", "200", "300M", "Aspen", "Cirrus", "Concorde", "Conquest", "Cordoba", "Crossfire", "E Class",
                 "Executive", "Fifth Avenue", "Grand Voyager", "Imperial", "Intrepid", "LHS", "Laser", "LeBaron", "Neon", "New Yorker", 
                 "PT Cruiser", "Prowler", "Sebring", "TC", "Town & Country"],
    "Dodge": ["Challenger", "Charger", "Durango", "Grand Caravan", "Hornet", "Journey", "400", "600", "Aries", "Avenger", "Caliber",
              "Caravan", "Colt", "Dakota", "Dart", "Daytona", "Diplomat", "Dynasty", "Intrepid", "Lancer", "Magnum", "Mini Ram",
              "Mirada", "Monaco", "Neon", "Nitro", "Omni", "Power Ram", "Power Ram 50", "Raider", "Ram 100", "Ram 150", "Ram 1500",
              "Ram 250", "Ram 2500", "Ram 350", "Ram 3500", "Ram 4500", "Ram 50", "Ram 5500", "Ram Van", "Ram Wagon", "Ram Charger",
              "Rampage", "SRT Viper", "Shadow", "Shelby", "Spirit", "Sprinter", "Stealth", "Stratus", "Viper", "W100"],
    "Fiat": ["124 Spider", "500", "500L", "500X", "500e", "2000", "Pininfarina"],
    "Ford": ["Bronco", "Bronco Sport", "C-Max", "E-Transit", "EcoSport", "Econoline", "Edge", "Escape", "Expedition", "Expedition MAX",
             "Explorer", "F-150", "F-150 Lightning", "F-250", "F-350", "F-450", "F-53", "F-550", "Fiesta", "Flex", "Focus", "Fusion",
             "Maverick", "Mustang", "Mustang Mach-E", "Ranger", "Taurus", "Transit", "Transit Connect", "Aerostar", "Aspire", "Bronco II",
             "Cobra", "Contour", "Courier", "Crown Victoria", "EXP", "Escort", "Excursion", "Expedition EL", "Explorer Sport Trac", "F-100",
             "F-59", "F-Super Duty", "Fairmont", "Festiva", "Five Hundred", "Freestar", "Freestyle", "GT", "LTD", "Probe", "Taurus X",
             "Tempo", "Thunderbird", "Windstar"],
    "GMC": ["Acadia", "Canyon", "Hummer EV", "Savana", "Sierra 1500", "Sierra 2500HD", "Sierra 3500HD", "Sierra EV", "Terrain", "Yukon",
            "Yukon XL", "1000", "C/K 1500", "C/K 2500", "C/K 3500", "Caballero", "Envoy", "Jimmy", "P3500", "R/V 3500", "Rally", "S-15",
            "S-15 Jimmy", "Safari", "Sierra 1500 Hybrid", "Sierra 1500HD", "Sierra 2500", "Sierra 3500", "Sonoma", "Suburban", "Typhoon",
            "Vandura"],
    "Genesis": ["G70", "G80", "G90", "GV60", "GV70", "GV80"],
    "Honda": ["Accord", "CR-V", "Civic", "Clarity", "Fit", "HR-V", "Insight", "Odyssey", "Passport", "Pilot", "Prologue", "Ridgeline",
              "Accord Crosstour", "CR-Z", "CRX", "City", "Element", "Prelude", "S2000"],
    "Hyundai": ["Accent", "Elantra", "Elantra N", "Ioniq", "Ioniq 5", "Ioniq 6", "Kona", "Kona N", "Nexo", "Palisade", "Santa Cruz",
                "Santa Fe", "Santa Fe Sport", "Santa Fe XL", "Sonata", "Tucson", "Veloster", "Veloster N", "Venue", "Azera", "Entourage",
                "Equus", "Excel", "Genesis", "Scoupe", "Tiburon", "Veracruz", "XG300", "XG350"],
    "Infiniti": ["Q50", "Q60", "Q70", "QX30", "QX50", "QX55", "QX60", "QX80", "EX35", "EX37", "FX35", "FX37", "FX45", "FX50", "G20", "G25",
                 "G35", "G37", "I30", "I35", "J30", "JX35", "M30", "M35", "M37", "M45", "M56", "Q40", "Q45", "QX4", "QX56", "QX70"],
    "Jaguar": ["E-Pace", "F-Pace", "F-Type", "I-Pace", "XE", "XF", "XJ", "S-Type", "X-Type", "XK"],
    "Jeep": ["Cherokee", "Compass", "Gladiator", "Grand Cherokee", "Grand Cherokee L", "Grand Wagoneer", "Renegade", "Wagoneer", "Wrangler",
             "CJ", "Comanche", "Commander", "J10", "J20", "Liberty", "Patriot", "Scrambler"],
    "Kia": ["Cadenza", "Carnival", "EV6", "EV9", "Forte", "Forte5", "K4", "K5", "K900", "Niro", "Niro EV", "Optima", "Rio", "Sedona",
            "Seltos", "Sorento", "Soul", "Soul EV", "Sportage", "Stinger", "Telluride", "Amanti", "Borrego", "Rio5", "Rondo", "Sephia",
            "Spectra", "Spectra5"],
    "Land Rover": ["Defender", "Discovery", "Discovery Sport", "Range Rover", "Range Rover Epoque", "Range Rover Sport", "Range Rover Velar",
                   "Freelander", "LR2", "LR3", "LR4"],
    "Lexus": ["ES", "GS", "GX", "IS", "LC", "LS", "LX", "NX", "RC", "RX", "RZ", "TX", "UX", "CT", "HS", "LFA", "SC"],
    "Lincoln": ["Aviator", "Continental", "Corsair", "MKC", "MKT", "MKX", "MKZ", "Nautilus", "Navigator", "Navigator L", "Blackwood", "LS",
                "MKS", "Mark LT", "Mark Series", "Town Car", "Zephyr"],
    "Mazda": ["CX-3", "CX-30", "CX-5", "CX-50", "CX-70", "CX-9", "CX-90", "MX-30", "Mazda3", "Mazda6", "Miata", "323", "626", "929",
              "B-Series", "CX-7", "GLC", "MAZDASPEED MX-5 Miata", "MAZDASPEED3", "MAZDASPEED5", "MPV", "MX-3", "MX-6", "Mazda2", "Mazda5",
              "Millenia", "Navajo", "Protege", "RX-7", "RX-8", "Tribute"],
    "Mercedes-Benz": ["A-Class", "AMG GT", "C-Class", "CLA", "CLE", "CLS", "E-Class", "EQB", "EQE", "EQS", "G-Class", "GLA", "GLB", "GLC",
                      "GLE", "GLS", "Metris", "S-Class", "SL-Class", "SLC", "Sprinter", "eSprinter", "190", "240", "260", "280", "300",
                      "350", "380", "400", "420", "500", "560", "600", "B-Class", "CL-Class", "CLK", "GL-Class", "GLK", "M-Class", "R-Class",
                      "SLK", "SLR", "SLS AMG"],
    "Mini": ["Cooper", "Cooper Clubman", "Cooper Countryman", "Cooper Coupe", "Cooper Paceman", "Cooper Roadster"],
    "Mitsubishi": ["Eclipse Cross", "Mirage", "Mirage G4", "Outlander", "Outlander Sport", "3000GT", "Cordia", "Diamante", "Eclipse",
                   "Endeavor", "Expo", "Galant", "Lancer", "Lancer Evolution", "Mighty Max", "Montero", "Montero Sport", "Pajero",
                   "Precis", "RVR", "Raider", "Sigma", "Starion", "Van", "i-MiEV"],
    "Nissan": ["Altima", "Ariya", "Armada", "Frontier", "GT-R", "Kicks", "Leaf", "Maxima", "Murano", "NV", "NV200", "Pathfinder", "Rogue",
               "Rogue Sport", "Sentra", "Titan", "Titan XD", "Versa", "Versa Note", "Z", "200SX", "240SX", "720", "Axxess", "Cube", "Juke",
               "Micra", "NX", "Pickup", "Pulsar", "Qashqai", "Quest", "Skyline", "Stanza", "Van", "X-Trail", "Xterra"],
    "Porsche": ["718 Boxster", "718 Cayman", "718 Spyder", "911", "Boxster", "Cayenne", "Cayman", "Macan", "Panamera", "Taycan", "918",
                "924", "928", "930", "944", "968", "Carrera GT"],
    "Ram": ["1500", "2500", "3500", "4500", "5500", "ProMaster", "ProMaster City", "ProMaster EV", "C/V", "Dakota"],
    "Subaru": ["Ascent", "BRZ", "Crosstrek", "Forester", "Impreza", "Legacy", "Outback", "STI S209", "Solterra", "WRX", "Baja", "Brat",
               "DL", "GL", "GLF", "Justy", "Loyale", "SVX", "Tribeca", "XT", "XV Crosstrek"],
    "Tesla": ["Cybertruck", "Model 3", "Model S", "Model X", "Model Y", "Roadster"],
    "Toyota": ["4Runner", "86", "Avalon", "C-HR", "Camry", "Corolla", "Corolla Cross", "Corolla iM", "Crown", "Crown Signia", "GR Corolla",
               "GR Supra", "GR86", "Grand Highlander", "Highlander", "Land Cruiser", "Mirai", "Prius", "Prius Prime", "Prius c", "RAV4",
               "Sequoia", "Sienna", "Tacoma", "Tundra", "Venza", "Yaris", "Yaris iA", "bZ4X", "Camry Solara", "Celica", "Corona", "Cressida",
               "Echo", "FJ Cruiser", "MR2", "MR2 Spyder", "Matrix", "Paseo", "Pickup", "Previa", "Prius Plug-in", "Prius v", "Supra", "T100",
               "Tercel", "Van"],
    "Volkswagen": ["Arteon", "Atlas", "Beetle", "Golf", "ID.4", "ID.Buzz", "Jetta", "Passat", "Taos", "Tiguan", "Transporter", "e-Golf",
                   "Bora", "CC", "Cabrio", "Cabriolet", "Corrado", "Eos", "Eurovan", "Fox", "GTI", "New Beetle", "Phaeton", "R32", "Rabbit",
                   "Routan", "Scirocco", "Touareg", "Vanagon"],
    "Volvo": ["C40", "EC40", "EX30", "EX40", "EX90", "S60", "S90", "V60", "V90", "XC40", "XC60", "XC90", "240", "244", "245", "260", "740",
              "760", "780", "850", "900-Series", "C30", "C70", "S40", "S70", "S80", "V40", "V50", "V70", "XC70"]
}

image_count = 10719 # !TODO, THIS IS THE INDEX AT WHICH WE STOP EVERYTIME THE CODE IS INTERRUPTED

results = []
unwanted_hash = hashlib.md5(open("unwanted.jpg", "rb").read()).hexdigest()
os.makedirs("carfax_images", exist_ok=True)

def scrape_make_model(make, model, image_count, results):
    options = uc.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options)

    try:
        driver.get("https://www.carfax.com/cars-for-sale")
        time.sleep(5)  # Need to make this longer and solve the Captcha / puzzle yourself if this appears

        driver.find_element(By.XPATH, "//button[contains(., 'Enter ZIP Code')]").click()
        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, ":r3:"))).send_keys("12345")

        miles_dropdown = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//select[@aria-label='Search Radius']"))
        ))

        for option in ["200", "500", "250"]: # possible mile options, CHANGE IF NECESSARY 
            for o in miles_dropdown.options:
                if o.text.strip() == option:
                    miles_dropdown.select_by_visible_text(option)
                    break
            else:
                continue
            break

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Apply')]"))
        ).click()

        time.sleep(2)

        make_dropdown = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "undefined-make-input"))
        ))
        make_dropdown.select_by_visible_text(make)
        time.sleep(2)

        model_dropdown = Select(driver.find_element(By.ID, "undefined-model-input"))
        model_dropdown.select_by_visible_text(model)
        time.sleep(1)

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.CLASS_NAME, "search-button"))).click()
        time.sleep(3)

        no_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@data-theme='blue']"))
        )
        if "Show Me" not in no_button.text:
            print(f"No results: {make} {model}")
            return image_count
        no_button.click()

        total_results_elem = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "totalResultCount"))
        )
        total_results = int(total_results_elem.text.strip().replace(",", ""))
        total_pages = (total_results + 23) // 24
        print(f"Found {total_results} results for {make} {model} ({total_pages} pages)")

        global_index = 0 

        for page_num in range(1, total_pages + 1):
            print(f"Scraping page {page_num}/{total_pages}...")
            time.sleep(2)

            listings = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[starts-with(@id, 'listing_')]"))
            )

            for idx, listing in enumerate(listings):
                if global_index >= total_results:
                    break
                try:
                    try:    # open More button
                        details_toggle = listing.find_element(By.XPATH, ".//details[contains(@class, 'details_toggle')]")
                        driver.execute_script("arguments[0].open = true;", details_toggle)
                        time.sleep(0.3)
                    except:
                        pass

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", listing)
                    time.sleep(0.5)
                    img_elems = listing.find_elements(By.XPATH, ".//img[contains(@class, 'listing-image')]")
                    if not img_elems:
                        continue

                    img_elem = img_elems[0]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_elem)
                    time.sleep(0.3)

                    img_url = img_elem.get_attribute("src") or img_elem.get_attribute("data-src")
                    if img_url and " " in img_url:
                        img_url = img_url.split(" ")[0]
                    if not img_url:
                        continue

                    img_data = requests.get(img_url).content
                    img_hash = hashlib.md5(img_data).hexdigest()
                    filename = f"car_{image_count}.jpg"
                    with open(os.path.join("carfax_images", filename), "wb") as f:
                        f.write(img_data)

                    color = "Unknown"
                    info_spans = listing.find_elements(By.CLASS_NAME, "srp-list-item__basic-info-value")
                    for span in info_spans:
                        if "Color:" in span.text:
                            color = span.text.replace("Color:", "").strip()
                            break

                    caption = makecap(make, model, color)

                    results.append({
                        "image": filename,
                        "image_id": image_count,
                        "label": caption,
                        "description": caption,
                        "validity": "INVALID" if img_hash == unwanted_hash else img_url,
                        "make": make,
                        "model": model,
                        "color": color,
                    })
                    print(f"Saved {filename} | {color}")
                    if img_hash == unwanted_hash:
                        print(" | INVALID")
                    image_count += 1
                    global_index += 1 

                except Exception as e:
                    print(f"Error on listing {idx+1}: {e}")
                    global_index += 1

            if page_num < total_pages:
                try:
                    next_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Go to next page')]"))
                    )
                    driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(3)
                except:
                    break

    except Exception as e:
        print(f"Failed on {make} {model}: {e}")
        raise

    finally:
        driver.quit()

    return image_count

for make, models in makemodeldict.items():
    for model in models:
        success = False
        for attempt in range(1, 4):
            print(f"\nAttempt {attempt} for {make} {model}")
            try:
                prev_count = image_count
                image_count = scrape_make_model(make, model, image_count, results)
                success = True
                break
            except Exception as e:
                print(f"Attempt {attempt} failed for {make} {model}: {type(e).__name__} - {str(e)}")
                raise

        if not success:
            print(f"All attempts failed for {make} {model}, moving on...\n")
        else:
            print(f"Progress saved after {make} {model} ({image_count - prev_count} images)")
        
        with open("carfax_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
