import time
import random
import re
import pandas as pd
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# ── 1. List of products to compare ─────────────────────────────────────────────
PRODUCTS = [
    {
        "name": "Samsung Galaxy S22 Ultra",
        "amazon": "https://www.amazon.in/Samsung-Smartphone-Titanium-Storage-without/dp/B0CT5BJC16/ref=sr_1_1?dib=eyJ2IjoiMSJ9.l3Iykx6bCc44vtyTG51s1FB5xCEsfVF6Mt3xOmCsenp1JsXB8PUVcbd4ZbSW3ZYifqY6pdtizhWNpHFf7h4mazdMQx5raL7YEoIU_lnm1LleK5-Y1nhJ-jKEFY_CtoaFIVnYI9hlIEVaeMflgrLRrRi9L22iQAvSv7_YdTzEMQit39Ccn-DD_TDWoiQjsHKi5B94qbnxnf59-FdBcfmGEsIOjIXGnEt2QFF-61gtqM.jYr8Ry-eiZ0uTtEoMx1R9kro8NjUhyvorgBP5pLICtg&dib_tag=se&keywords=galaxy%2Bultra&qid=1745513495&sr=8-1&th=1",
        "flipkart": "https://www.flipkart.com/samsung-galaxy-s24-ultra-5g-titanium-black-256-gb/p/itm20b685e30271b?pid=MOBH3P4UM6ACEC2M&lid=LSTMOBH3P4UM6ACEC2MPVUFW8&marketplace=FLIPKART&q=s24+ultra&store=tyy%2F4io&srno=s_1_1&otracker=search&otracker1=search&fm=Search&iid=4e36d709-60dd-449d-a50e-afc604ac3abe.MOBH3P4UM6ACEC2M.SEARCH&ppt=sp&ppn=sp&ssid=sv05ixkna80000001745513562192&qH=9645cd762e4dc77e"
    },
    {
        "name": "Apple MacBook Air M1",
        "amazon": "https://www.amazon.in/Apple-MacBook-Chip-13-inch-256GB/dp/B08N5W4NNB/",
        "flipkart": "https://www.flipkart.com/apple-macbook-air-m2-8-gb-256-gb-ssd-mac-os-monterey-mlxy3hn-a/p/itm6533ea968a81e?pid=COMGFB2GWHPVFMJW&lid=LSTCOMGFB2GWHPVFMJWKVXDUX&marketplace=FLIPKART&q=macbook+air+m2&store=6bo%2Fb5g&srno=s_1_1&otracker=AS_Query_OrganicAutoSuggest_5_3_na_na_na&otracker1=AS_Query_OrganicAutoSuggest_5_3_na_na_na&fm=organic&iid=903c2443-5b07-43eb-b9e3-571dd4b59c2f.COMGFB2GWHPVFMJW.SEARCH&ppt=hp&ppn=homepage&ssid=n4hyg8s0000000001745513041939&qH=5be12f29ec3566a2"
    }
]
# ──────────────────────────────────────────────────────────────────────────────

def setup_driver():
    """Set up and return a configured Chrome WebDriver"""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--window-size=1920,1080")  # Set window size
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Add user agent to appear as a regular browser
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    # Install ChromeDriver if needed and initialize the driver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        print("If you're getting an error related to ChromeDriver, please make sure you have Chrome installed.")
        print("Alternatively, you can download ChromeDriver manually and specify its path.")
        return None

def parse_price(text: str):
    """Extract price from string like ₹1,000.00 or ₹1000"""
    if not text:
        return None
    
    # Look for price patterns with the ₹ symbol or Rs.
    m = re.search(r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)", text, re.IGNORECASE)
    
    if m:
        # Remove commas and convert to float
        return float(m.group(1).replace(",", ""))
    
    # If the above pattern doesn't match, try a more general approach
    m = re.search(r"([\d,]+(?:\.\d{1,2})?)", text)
    if m:
        return float(m.group(1).replace(",", ""))
    
    return None

def get_amazon_price(driver, url):
    """Extract price from Amazon using Selenium"""
    try:
        print(f"Navigating to Amazon URL: {url}")
        driver.get(url)
        
        # Wait for page to load and handle cookies/popups if needed
        time.sleep(random.uniform(3, 5))
        
        # Try multiple price selectors
        price_selectors = [
            "span.a-price-whole",
            "span#priceblock_ourprice",
            "span#priceblock_dealprice",
            "span.a-price span.a-offscreen",
            "span.a-price-whole",
            "span.a-color-price"
        ]
        
        for selector in price_selectors:
            try:
                # Wait for the price element to be present
                wait = WebDriverWait(driver, 5)
                price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
                price_text = price_element.text
                if price_text:
                    price = parse_price(price_text)
                    if price:
                        print(f"Found Amazon price: ₹{price}")
                        return price
            except (TimeoutException, NoSuchElementException):
                continue
        
        print("No price found on Amazon")
        return None
    except Exception as e:
        print(f"[Amazon] Error for {url}: {e}")
        return None

def get_flipkart_price(driver, url):
    """Extract price from Flipkart using Selenium with enhanced selectors"""
    try:
        print(f"Navigating to Flipkart URL: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(random.uniform(4, 6))
        
        # Close login popup if it appears
        try:
            close_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, '_2KpZ6l') and contains(@class, '_2doB4z')]")
            if close_buttons:
                close_buttons[0].click()
                time.sleep(1)
        except Exception as e:
            print(f"No login popup or couldn't close it: {e}")
        
        # Take screenshot before attempting to find price (for debugging)
        take_screenshot(driver, f"flipkart_debug_{int(time.time())}.png")
        
        # First try XPath approach which is more resilient to class changes
        price_xpath_patterns = [
            "//div[contains(@class, '_30jeq3')]",
            "//div[contains(@class, '_30jeq3') and contains(@class, '_16Jk6d')]",
            "//div[contains(@class, '_30jeq3') and contains(@class, '_1_WHN1')]",
            "//div[contains(text(), '₹')]",
            "//span[contains(text(), '₹')]"
        ]
        
        for xpath in price_xpath_patterns:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    price_text = element.text
                    if price_text and '₹' in price_text:
                        price = parse_price(price_text)
                        if price and price > 100:  # Basic sanity check
                            print(f"Found Flipkart price via XPath: ₹{price}")
                            return price
            except Exception as e:
                print(f"XPath search error: {e}")
                continue
        
        # Try extracting from page source as a fallback
        try:
            page_source = driver.page_source
            # Look for price in JSON-LD data
            match = re.search(r'"price":\s*"?(\d+(?:\.\d+)?)"?', page_source)
            if match:
                price = float(match.group(1))
                print(f"Found Flipkart price from page source: ₹{price}")
                return price
                
            # Look for price patterns in the entire page
            matches = re.findall(r'₹\s*([\d,]+)', page_source)
            if matches:
                # Get the most likely price (usually the largest number that's reasonable)
                prices = [float(match.replace(',', '')) for match in matches]
                # Filter out unreasonable prices
                reasonable_prices = [p for p in prices if 1000 < p < 500000]
                if reasonable_prices:
                    price = max(reasonable_prices)  # Typically the main price is the highest
                    print(f"Found Flipkart price from regex: ₹{price}")
                    return price
        except Exception as e:
            print(f"Page source extraction error: {e}")
        
        # Wait explicitly for price to appear
        try:
            # Wait up to 10 seconds for any element containing ₹ to appear
            wait = WebDriverWait(driver, 10)
            price_element = wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '₹')]"))
            )
            price_text = price_element.text
            price = parse_price(price_text)
            if price:
                print(f"Found Flipkart price after explicit wait: ₹{price}")
                return price
        except Exception as e:
            print(f"Explicit wait failed: {e}")
        
        print("No price found on Flipkart after all attempts")
        return None
    except Exception as e:
        print(f"[Flipkart] Error for {url}: {e}")
        return None

def take_screenshot(driver, filename):
    """Take a screenshot of the current page"""
    try:
        driver.save_screenshot(filename)
        print(f"Screenshot saved to {filename}")
    except Exception as e:
        print(f"Error taking screenshot: {e}")

def print_price_comparison(product_name, amazon_price, flipkart_price):
    """Print a formatted price comparison for a single product"""
    print(f"\n{'='*50}")
    print(f"{'PRICE COMPARISON':^50}")
    print(f"{'='*50}")
    print(f"{product_name:^50}")
    print(f"{'='*50}")
    
    # Format prices with thousand separators
    amazon_fmt = f"₹{amazon_price:,.2f}" if amazon_price else "Not available"
    flipkart_fmt = f"₹{flipkart_price:,.2f}" if flipkart_price else "Not available"
    
    # Determine which is cheaper
    if amazon_price and flipkart_price:
        if amazon_price < flipkart_price:
            comparison = f"Amazon is cheaper by ₹{flipkart_price - amazon_price:,.2f}"
        elif flipkart_price < amazon_price:
            comparison = f"Flipkart is cheaper by ₹{amazon_price - flipkart_price:,.2f}"
        else:
            comparison = "Prices are equal"
    else:
        comparison = "Price comparison not available (missing data)"
    
    # Print the comparison table
    print(f"{'Amazon':<25}{'Flipkart':<25}")
    print(f"{'-'*25:<25}{'-'*25:<25}")
    print(f"{amazon_fmt:<25}{flipkart_fmt:<25}")
    print(f"\n{comparison}")
    print(f"{'='*50}")

def scrape():
    """Main scraping function"""
    driver = setup_driver()
    if not driver:
        return None
    
    try:
        rows = []
        for product in PRODUCTS:
            print(f"\nFetching: {product['name']}")
            
            # Get prices from Amazon and Flipkart
            amazon_price = get_amazon_price(driver, product['amazon'])
            # Take a screenshot after loading Amazon
            take_screenshot(driver, f"amazon_{product['name'].replace(' ', '_')}.png")
            
            # Add a delay between requests
            time.sleep(random.uniform(5, 8))
            
            flipkart_price = get_flipkart_price(driver, product['flipkart'])
            # Take a screenshot after loading Flipkart
            take_screenshot(driver, f"flipkart_{product['name'].replace(' ', '_')}.png")
            
            # Print the price comparison for this product
            print_price_comparison(product['name'], amazon_price, flipkart_price)
            
            # Add a delay between products
            time.sleep(random.uniform(5, 8))
            
            # Determine the cheaper site
            cheaper_site = "-"
            price_diff = None
            if amazon_price and flipkart_price:
                cheaper_site = "Amazon" if amazon_price < flipkart_price else "Flipkart"
                price_diff = abs(amazon_price - flipkart_price)
            elif amazon_price:
                cheaper_site = "Amazon"
            elif flipkart_price:
                cheaper_site = "Flipkart"
                
            rows.append({
                "Product": product['name'],
                "Amazon Price (₹)": amazon_price,
                "Flipkart Price (₹)": flipkart_price,
                "Cheaper Site": cheaper_site,
                "Difference (₹)": price_diff
            })
        
        return pd.DataFrame(rows)
    
    finally:
        if driver:
            driver.quit()

def format_price(price):
    """Format price with thousand separators"""
    if pd.isna(price):
        return "N/A"
    return f"₹{price:,.2f}"

if __name__ == "__main__":
    print("Starting price comparison with Selenium...")
    
    # Create a backup of previously scraped data if available
    out_file = Path("electronics_price_comparison.csv")
    if out_file.exists():
        backup_file = Path(f"electronics_price_comparison_backup_{int(time.time())}.csv")
        out_file.rename(backup_file)
        print(f"Created backup of previous data: {backup_file}")
    
    try:
        df = scrape()
        
        if df is not None and not df.empty:
            # Format prices for display
            display_df = df.copy()
            for col in ["Amazon Price (₹)", "Flipkart Price (₹)", "Difference (₹)"]:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: format_price(x) if not pd.isna(x) else "N/A")
            
            print("\n---- Final Price Comparison Summary ----")
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            print(display_df.to_string(index=False))
            
            # Save the results as CSV with raw numbers
            df.to_csv(out_file, index=False)
            print(f"\nCSV written to {out_file.resolve()}")
            print("\nScreenshots of the product pages have been saved for verification.")
        else:
            print("\nNo data was collected. Please check the error messages above.")
    
    except Exception as e:
        print(f"Error during scraping: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have Chrome browser installed")
        print("2. Install required packages: pip install selenium webdriver-manager pandas")
        print("3. Check your internet connection")
        print("4. Try with different product URLs")
