from pydantic import BaseModel, Field
import os
import sys
import time
import subprocess
from typing import ClassVar, Optional, Dict, Any, Union
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options



current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', '..'))

from llm.llm_utils import get_code_from_text_response
from pipeline.execution.env import EnvConfig, Env, random_string

class HtmlEnvConfig(EnvConfig):
    """
    Configuration for the HTML environment.
    """
    module_name: str = Field(default='html_env', description="Code type: either python or html")
    cache_folder: str = Field(default=os.path.join(current_dir, '..', '..', 'temp', 'html'), description="Folder to cache HTML files")
    viewport_width: int = Field(default=1200, description="Viewport width for rendering")
    viewport_height: int = Field(default=800, description="Viewport height for rendering")
    render_wait_time: float = Field(default=0.5, description="Time to wait for rendering to complete (seconds)")

class HtmlEnv(Env):
    """
    Represents an HTML environment that can execute actions based on the provided configuration.
    """
    config: HtmlEnvConfig
    selenium_driver: ClassVar[Optional[Any]] = None
    
    def __init__(self, config: HtmlEnvConfig):
        super().__init__(config=config)
        self._initialize_selenium()
    
    def _initialize_selenium(self):
        """Initialize Selenium with WebDriver manager for automatic driver downloads"""
        try:
            
            
            # driver_path = ChromeDriverManager().install()

            # Configure Chrome options
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--window-size={self.config.viewport_width},{self.config.viewport_height}")
            
            options.add_argument("--disable-gpu")  # Important for some Linux distributions
            
            # Initialize Chrome
            HtmlEnv.selenium_driver = webdriver.Chrome(
                # service=ChromeService(driver_path),
                options=options
            )
                
            
        except Exception as e:
            print(f"Error initializing Selenium: {e}")
    
    def render_with_selenium(self, html_file_path: str, image_file_path: str) -> bool:
        """Render HTML to image using Selenium WebDriver"""
        if not HtmlEnv.selenium_driver:
            print("Selenium WebDriver is not initialized. Trying to initialize now...")
            self._initialize_selenium()
            if not HtmlEnv.selenium_driver:
                print("Failed to initialize Selenium WebDriver.")
                return False
        
        try:
            # Create the file URL
            file_url = f"file://{os.path.abspath(html_file_path)}"
            
            # Navigate to the HTML file
            HtmlEnv.selenium_driver.get(file_url)
            
            # Wait for JavaScript to execute
            time.sleep(self.config.render_wait_time)
            
            # Get original window size
            original_size = HtmlEnv.selenium_driver.get_window_size()
            
            # Get the required dimensions with JavaScript
            required_width = HtmlEnv.selenium_driver.execute_script('return document.body.parentNode.scrollWidth')
            required_height = HtmlEnv.selenium_driver.execute_script('return document.body.parentNode.scrollHeight')
            
            min_height = int(required_width * 0.75)
            required_height = max(int(required_height * 1.1), min_height)

            # Set the window size to capture everything
            HtmlEnv.selenium_driver.set_window_size(required_width, required_height)
            
            # Take screenshot of the entire page
            HtmlEnv.selenium_driver.save_screenshot(image_file_path)
            
            # Reset the window size to original dimensions
            HtmlEnv.selenium_driver.set_window_size(original_size['width'], original_size['height'])
            
            print(f"Full page screenshot saved to {image_file_path} (dimensions: {required_width}x{required_height})")
            return True
        except Exception as e:
            print(f"Selenium rendering failed: {e}")
            # Try to reset the driver if there was an error
            try:
                HtmlEnv.selenium_driver.quit()
                HtmlEnv.selenium_driver = None
                self._initialize_selenium()
            except:
                pass
            return False
    
    def step(self, action: str, run_name: str = '', tag: str = '') -> Dict[str, Any]:
        """
        Perform an action in the HTML environment.

        :param action: The action to perform.
        :return: Result of the action.
        """
        if not run_name:
            run_name = random_string(10)

        html_code = get_code_from_text_response(action)[-1]
        if html_code['language'] not in ['html', 'javascript', 'html5']:
            raise ValueError(f"Unsupported language: {html_code['language']}. Expected 'html', 'javascript', or 'html5'.")
        
        # Create folders for code and images
        os.makedirs(os.path.join(self.config.cache_folder, 'code', run_name), exist_ok=True)
        os.makedirs(os.path.join(self.config.cache_folder, 'images', run_name), exist_ok=True)
        
        run_time = time.strftime("%Y%m%d-%H%M%S")
        html_file_path = os.path.join(self.config.cache_folder, 'code', run_name, f"render_{tag}_{run_time}.html")
        image_file_path = os.path.join(self.config.cache_folder, 'images', run_name, f"render_{tag}_{run_time}.png")

        code = html_code['code']
        
        # Add common HTML fixes to ensure proper rendering
        if "<html" not in code:
            code = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rendered HTML</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script> 
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
{code}
</body>
</html>"""

        with open(html_file_path, 'w') as f:
            f.write(code)
        
        # Render with Selenium
        success = self.render_with_selenium(html_file_path, image_file_path)
            
        if not success:
            raise Exception("Failed to render HTML to image using Selenium")
        
        return {
            'code': code,
            'code_file_path': html_file_path,
            'image_file_path': image_file_path,
            'run_name': run_name,
        }
    
    def __del__(self):
        """Clean up resources when the object is destroyed"""
        if HtmlEnv.selenium_driver:
            try:
                HtmlEnv.selenium_driver.quit()
                HtmlEnv.selenium_driver = None
            except:
                pass


if __name__ == "__main__":
    # Simple HTML example to test rendering
    with open(os.path.join(current_dir, '..', '..', 'example', 'chart.html'), 'r') as f:
        html = f.read()
    action = '```html\n' + html + '\n```'
    env = HtmlEnv(config=HtmlEnvConfig())
    result = env.step(action, run_name='test_run', tag='test_tag')
    print(f"Image saved to: {result['image_file_path']}")