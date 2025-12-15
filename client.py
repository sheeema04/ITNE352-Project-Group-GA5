import socket
import json
import sys

class NewsClient:
    def __init__(self, host='127.0.0.1', port=50555):
        """Initialize client with server connection details"""
        self.host = host
        self.port = port
        self.socket = None
        self.username = ""
        self.connected = False
        
        # Parameter options 
        self.countries = ['au', 'ca', 'jp', 'ac', 'sa', 'kr', 'us', 'ma']
        self.languages = ['ar', 'en']
        self.categories = ['business', 'general', 'health', 'science', 'sports', 'technology']
        
        # Store current list for details view
        self.current_headlines = []
        self.current_sources = []
        
    def connect_to_server(self):
        """Establish connection with server"""
        try:
            print(f"\nConnecting to server at {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            
            # Get username
            self.username = input("Enter your username: ").strip()
            if not self.username:
                self.username = "ClientB"
            
            # Connect to server
            self.socket.connect((self.host, self.port))
            
            # Send username to server (FIRST message)
            self.socket.send(self.username.encode('utf-8'))
            
            self.connected = True
            print("✅ Connected to server successfully!")
            return True
            
        except ConnectionRefusedError:
            print("Error: Server is not running or not reachable")
            print("Make sure server.py is running first")
            return False
        except socket.timeout:
            print("Error: Connection timeout")
            return False
        except Exception as e:
            print(f"Error: Connection error: {e}")
            return False
    
    def send_request(self, option, parameters=None):
        """Send request to server and get response"""
        if not self.connected:
            print("Not connected to server!")
            return None
        
        # Create request dictionary 
        request = {
            'option': option,
            'parameters': parameters or {}
        }
        
        try:
            # Send request as JSON
            request_json = json.dumps(request)
            self.socket.send(request_json.encode('utf-8'))
            
            # Receive response (handle large responses properly)
            response_data = b""
            chunk_size = 4096
            
            # Try to get complete response
            self.socket.settimeout(5)  # 5 second timeout for response
            
            while True:
                try:
                    chunk = self.socket.recv(chunk_size)
                    if not chunk:
                        break
                    response_data += chunk
                    
                    # Try to parse to see if we have complete JSON
                    try:
                        json.loads(response_data.decode('utf-8'))
                        break  # We have complete JSON
                    except json.JSONDecodeError:
                        # Check if we've received a lot of data (safety limit)
                        if len(response_data) > 100000:  # 100KB limit
                            print("Response too large, stopping reception")
                            break
                        continue  # Need more data
                except socket.timeout:
                    # If we have some data, try to parse it
                    if response_data:
                        break
                    else:
                        print("Response timeout")
                        return None
            
            response_str = response_data.decode('utf-8', errors='ignore')
            
            # Parse JSON response
            try:
                response = json.loads(response_str)
                return response
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                if len(response_str) > 500:
                    print(f"Response too long, showing first 500 chars:")
                    print(response_str[:500])
                else:
                    print(f"Raw response: {response_str}")
                return None
                
        except socket.timeout:
            print("Request timeout")
            return None
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def display_main_menu(self):
        """Display main menu"""
        print("\n" + "="*50)
        print("📰  NEWS CLIENT - MAIN MENU")
        print("="*50)
        print("1. Search Headlines")
        print("2. List of Sources")
        print("3. Quit")
        print("="*50)
    
    def display_headlines_menu(self):
        """Display headlines submenu"""
        print("\n" + "="*50)
        print("📰  HEADLINES MENU")
        print("="*50)
        print("1. Search by keyword")
        print("2. Search by category")
        print("3. Search by country")
        print("4. List all headlines")
        print("5. Back to Main Menu")
        print("="*50)
    
    def display_sources_menu(self):
        """Display sources submenu"""
        print("\n" + "="*50)
        print("📚  SOURCES MENU")
        print("="*50)
        print("1. Search by category")
        print("2. Search by country")
        print("3. Search by language")
        print("4. List all sources")
        print("5. Back to Main Menu")
        print("="*50)
    
    def get_user_choice(self, min_val, max_val):
        """Get and validate user input"""
        while True:
            try:
                choice = input(f"\nEnter choice ({min_val}-{max_val}): ").strip()
                if not choice:
                    continue
                
                choice_int = int(choice)
                if min_val <= choice_int <= max_val:
                    return choice_int
                else:
                    print(f"Please enter a number between {min_val} and {max_val}")
            except ValueError:
                print("Please enter a valid number")
    
    def get_keyword_input(self):
        """Get keyword search input"""
        keyword = input("\nEnter keyword to search: ").strip()
        if keyword:
            return {'keyword': keyword}
        else:
            print("No keyword entered, will show general headlines")
            return {}
    
    def get_category_input(self):
        """Get category input with validation"""
        print("\nAvailable categories:")
        for i, cat in enumerate(self.categories, 1):
            print(f"  {i}. {cat.capitalize()}")
        
        while True:
            choice = input("\nEnter category number or name: ").strip().lower()
            
            # If number entered
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(self.categories):
                    return {'category': self.categories[idx]}
            
            # If name entered
            if choice in self.categories:
                return {'category': choice}
            
            print(f"Invalid category. Choose from: {', '.join(self.categories)}")
    
    def get_country_input(self):
        """Get country input with validation"""
        print("\nAvailable countries (2-letter codes):")
        print("  au: Australia      ca: Canada")
        print("  jp: Japan          ac: Ascension Island")
        print("  sa: Saudi Arabia   kr: South Korea")
        print("  us: United States  ma: Morocco")
        
        while True:
            country = input("\nEnter country code: ").strip().lower()
            if country in self.countries:
                return {'country': country}
            print(f"Invalid country code. Choose from: {', '.join(self.countries)}")
    
    def get_language_input(self):
        """Get language input with validation"""
        print("\nAvailable languages:")
        print("  ar: Arabic")
        print("  en: English")
        
        while True:
            lang = input("\nEnter language code: ").strip().lower()
            if lang in self.languages:
                return {'language': lang}
            print("Invalid language. Use 'ar' or 'en'")
    
    def display_headlines_list(self, headlines_response):
        """Display list of headlines from server response"""
        if not headlines_response:
            print("\nNo response from server")
            return []
        
        if headlines_response.get('status') != 'success':
            message = headlines_response.get('message', 'Unknown error')
            print(f"\nError: {message}")
            return []
        
        data = headlines_response.get('data', [])
        if not data:
            print("\nNo headlines found")
            return []
        
        print(f"\nFound {len(data)} headlines:\n")
        
        # Store for details view
        self.current_headlines = data
        
        for item in data:
            idx = item.get('index', 0)
            source = item.get('source', 'Unknown')
            author = item.get('author', 'Unknown')
            title = item.get('title', 'No title')
            
            # Shortening long titles
            short_title = title[:70] + "..." if len(title) > 70 else title
            
            print(f"{idx:2}. {short_title}")
            print(f"    Source: {source} | Author: {author}")
            print()
        
        return data
    
    def display_sources_list(self, sources_response):
        """Display list of sources from server response"""
        if not sources_response:
            print("\nNo response from server")
            return []
        
        if sources_response.get('status') != 'success':
            message = sources_response.get('message', 'Unknown error')
            print(f"\nError: {message}")
            return []
        
        data = sources_response.get('data', [])
        if not data:
            print("\nNo sources found")
            return []
        
        print(f"\nFound {len(data)} sources:\n")
        
        # Store for details view
        self.current_sources = data
        
        for item in data:
            idx = item.get('index', 0)
            name = item.get('name', 'Unknown')
            print(f"{idx:2}. {name}")
        
        return data
    
    def display_headline_detail(self, headline):
        """Display detailed headline information"""
        print("\n" + "="*60)
        print("HEADLINE DETAILS")
        print("="*60)
        
        print(f"Source: {headline.get('source', 'Unknown')}")
        print(f"Author: {headline.get('author', 'Not specified')}")
        print(f"Title: {headline.get('title', 'No title')}")
        print("-"*60)
        print(f"🔗 URL: {headline.get('url', 'Not available')}")
        print(f"📝 Description: {headline.get('description', 'No description')}")
        
        # Format date if available
        published = headline.get('publishedAt', '')
        if published:
            print(f"Published: {published}")
        
        print("="*60)
    
    def display_source_detail(self, source):
        """Display detailed source information"""
        print("\n" + "="*60)
        print("SOURCE DETAILS")
        print("="*60)
        
        print(f"Name: {source.get('name', 'Unknown')}")
        print(f"Country: {source.get('country', 'Not specified')}")
        print(f"Category: {source.get('category', 'Not specified')}")
        print(f"Language: {source.get('language', 'Not specified')}")
        print(f"🔗 URL: {source.get('url', 'Not available')}")
        print(f"📝 Description: {source.get('description', 'No description')}")
        print("="*60)
    
    def handle_headlines_menu(self):
        """Handle headlines menu navigation"""
        while True:
            self.display_headlines_menu()
            choice = self.get_user_choice(1, 5)
            
            if choice == 1:  # Search by keyword
                params = self.get_keyword_input()
                response = self.send_request('headlines', params)
                if response:
                    items = self.display_headlines_list(response)
                    if items:
                        self.handle_item_selection(items, 'headline')
            
            elif choice == 2:  # Search by category
                params = self.get_category_input()
                response = self.send_request('headlines', params)
                if response:
                    items = self.display_headlines_list(response)
                    if items:
                        self.handle_item_selection(items, 'headline')
            
            elif choice == 3:  # Search by country
                params = self.get_country_input()
                response = self.send_request('headlines', params)
                if response:
                    items = self.display_headlines_list(response)
                    if items:
                        self.handle_item_selection(items, 'headline')
            
            elif choice == 4:  # List all headlines
                response = self.send_request('headlines', {})
                if response:
                    items = self.display_headlines_list(response)
                    if items:
                        self.handle_item_selection(items, 'headline')
            
            elif choice == 5:  # Back to main
                break
    
    def handle_sources_menu(self):
        """Handle sources menu navigation"""
        while True:
            self.display_sources_menu()
            choice = self.get_user_choice(1, 5)
            
            if choice == 1:  # Search by category
                params = self.get_category_input()
                response = self.send_request('sources', params)
                if response:
                    items = self.display_sources_list(response)
                    if items:
                        self.handle_item_selection(items, 'source')
            
            elif choice == 2:  # Search by country
                params = self.get_country_input()
                response = self.send_request('sources', params)
                if response:
                    items = self.display_sources_list(response)
                    if items:
                        self.handle_item_selection(items, 'source')
            
            elif choice == 3:  # Search by language
                params = self.get_language_input()
                response = self.send_request('sources', params)
                if response:
                    items = self.display_sources_list(response)
                    if items:
                        self.handle_item_selection(items, 'source')
            
            elif choice == 4:  # List all sources
                response = self.send_request('sources', {})
                if response:
                    items = self.display_sources_list(response)
                    if items:
                        self.handle_item_selection(items, 'source')
            
            elif choice == 5:  # Back to main
                break
    
    def handle_item_selection(self, items, item_type):
        """Handle user selecting an item for details"""
        if not items:
            return
            
        while True:
            try:
                choice = input(f"\nEnter item number for details (1-{len(items)}), or 0 to go back: ").strip()
                if not choice:
                    continue
                
                choice_int = int(choice)
                if choice_int == 0:
                    return
                elif 1 <= choice_int <= len(items):
                    # Send details request to server
                    params = {
                        'type': item_type,
                        'index': choice_int
                    }
                    
                    response = self.send_request('details', params)
                    
                    if response and response.get('status') == 'success':
                        details = response.get('data', {})
                        
                        if item_type == 'headline':
                            self.display_headline_detail(details)
                        else:  # source
                            self.display_source_detail(details)
                    else:
                        error_msg = response.get('message', 'Failed to get details') if response else 'No response'
                        print(f"{error_msg}")
                    
                    # Ask if user wants to select another
                    another = input("\nView another item? (y/n): ").strip().lower()
                    if another != 'y':
                        return
                else:
                    print(f"Please enter a number between 0 and {len(items)}")
            except ValueError:
                print("Please enter a valid number")
    
    def run(self):
        """Main client loop"""
        print("\n" + "="*50)
        print("     NEWS CLIENT - ITNE352 PROJECT")
        print("="*50)
        
        # Connect to server
        if not self.connect_to_server():
            print("\nFailed to connect to server. Exiting...")
            return
        
        # Main loop
        while True:
            self.display_main_menu()
            choice = self.get_user_choice(1, 3)
            
            if choice == 1:  # Headlines menu
                self.handle_headlines_menu()
            
            elif choice == 2:  # Sources menu
                self.handle_sources_menu()
            
            elif choice == 3:  # Quit
                print("\n👋 Goodbye!")
                break
        
        # Clean up
        if self.connected and self.socket:
            try:
                self.socket.close()
            except:
                pass

def main():
    """Main function with command-line argument support"""
    # Parse command line arguments
    if len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    elif len(sys.argv) == 2:
        host = sys.argv[1]
        port = 50555  # Default port from server
    else:
        host = '127.0.0.1'
        port = 50555
    
    print(f"Client settings: {host}:{port}")
    
    client = NewsClient(host, port)
    
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n\nClient interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()