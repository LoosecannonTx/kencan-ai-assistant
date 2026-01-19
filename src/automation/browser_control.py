"""
Browser automation controller for Kencan
Handles browser operations like opening tabs, navigation, searching, etc.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional, Dict, Any, List
import time

class BrowserController:
    """Controller for browser automation"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize browser controller"""
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.browser_config = config.get('browser', {})
        
    def open_browser(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Open browser with optional URL"""
        try:
            if self.driver is None:
                options = Options()
                
                # Configure based on settings
                if self.browser_config.get('headless', False):
                    options.add_argument('--headless')
                
                user_data = self.browser_config.get('user_data_dir')
                if user_data:
                    options.add_argument(f'user-data-dir={user_data}')
                
                # Initialize driver
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                self.driver.maximize_window()
            
            if url:
                self.driver.get(url)
            else:
                self.driver.get("https://www.google.com")
            
            return {
                'success': True,
                'message': 'Browser opened',
                'url': self.driver.current_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def new_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Open a new tab"""
        try:
            if self.driver is None:
                return self.open_browser(url)
            
            # Open new tab
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            if url:
                self.driver.get(url)
            
            return {
                'success': True,
                'message': 'New tab opened',
                'url': self.driver.current_url if url else 'about:blank'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def close_tab(self, index: Optional[int] = None) -> Dict[str, Any]:
        """Close a tab by index (or current tab if None)"""
        try:
            if self.driver is None:
                return {'success': False, 'error': 'No browser open'}
            
            if index is not None:
                handles = self.driver.window_handles
                if 0 <= index < len(handles):
                    self.driver.switch_to.window(handles[index])
            
            self.driver.close()
            
            # Switch to remaining tab if any
            if len(self.driver.window_handles) > 0:
                self.driver.switch_to.window(self.driver.window_handles[0])
            
            return {
                'success': True,
                'message': 'Tab closed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def search(self, query: str) -> Dict[str, Any]:
        """Perform a web search"""
        try:
            if self.driver is None:
                self.open_browser()
            
            # Go to Google
            self.driver.get("https://www.google.com")
            time.sleep(1)
            
            # Find search box and enter query
            search_box = self.driver.find_element(By.NAME, "q")
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(2)
            
            # Get search results
            results = []
            try:
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
                for elem in result_elements[:5]:  # Top 5 results
                    try:
                        title_elem = elem.find_element(By.TAG_NAME, "h3")
                        link_elem = elem.find_element(By.TAG_NAME, "a")
                        
                        results.append({
                            'title': title_elem.text,
                            'url': link_elem.get_attribute('href')
                        })
                    except:
                        continue
            except:
                pass
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'url': self.driver.current_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def click(self, selector: str, by: str = 'css') -> Dict[str, Any]:
        """Click an element on the page"""
        try:
            if self.driver is None:
                return {'success': False, 'error': 'No browser open'}
            
            by_type = By.CSS_SELECTOR if by == 'css' else By.XPATH
            element = self.driver.find_element(by_type, selector)
            element.click()
            
            return {
                'success': True,
                'message': f'Clicked element: {selector}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def type_text(self, selector: str, text: str, by: str = 'css') -> Dict[str, Any]:
        """Type text into an element"""
        try:
            if self.driver is None:
                return {'success': False, 'error': 'No browser open'}
            
            by_type = By.CSS_SELECTOR if by == 'css' else By.XPATH
            element = self.driver.find_element(by_type, selector)
            element.clear()
            element.send_keys(text)
            
            return {
                'success': True,
                'message': f'Typed text into: {selector}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_page_content(self) -> Dict[str, Any]:
        """Get current page content"""
        try:
            if self.driver is None:
                return {'success': False, 'error': 'No browser open'}
            
            return {
                'success': True,
                'title': self.driver.title,
                'url': self.driver.current_url,
                'content': self.driver.page_source[:5000]  # Limit content size
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup(self):
        """Close browser and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
