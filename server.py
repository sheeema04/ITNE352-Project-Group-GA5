import socket
import threading
import json
import requests
from datetime import datetime

class NewsAPIServer:
    def __init__(self, host='127.0.0.1', port=50555):
        self.host = host
        self.port = port
        self.api_key = "581ce79e69aa4dffa9ab39bbf0084b5e"
        self.base_url = "https://newsapi.org/v2"
        self.group_id = "GA5"  
        
        # Allowed parameters 
        self.allowed_countries = ['au', 'ca', 'jp', 'ac', 'sa', 'kr', 'us', 'ma']
        self.allowed_languages = ['ar', 'en']
        self.allowed_categories = ['business', 'general', 'health', 'science', 'sports', 'technology']
        
        # Store client data for details retrieval
        self.client_data = {}
        
        # Create TCP socket connection
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  # Handle up to 5 simultaneous connections
        
        self.active_clients = []
        print(f"[SERVER] Server started on {self.host}:{self.port}")
        print("[SERVER] Waiting for connections...")

    def start(self):
        """Main server loop to accept connections"""
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"[SERVER] New connection from {client_address}")
                
                # Create a new thread for each client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down...")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        """Handle individual client connection"""
        client_name = None
        try:
            # Get client name
            client_name = client_socket.recv(1024).decode('utf-8').strip()
            print(f"[SERVER] Client '{client_name}' connected from {client_address}")
            
            # Add to active clients
            self.active_clients.append({
                'name': client_name,
                'socket': client_socket,
                'address': client_address
            })
            
            # Main client loop
            while True:
                # Receive client request
                request_data = client_socket.recv(4096).decode('utf-8')
                if not request_data:
                    break
                    
                try:
                    request = json.loads(request_data)
                    self.process_request(client_socket, client_name, request)
                except json.JSONDecodeError:
                    error_response = {
                        'status': 'error',
                        'message': 'Invalid request format'
                    }
                    self.send_json_response(client_socket, error_response)
                    
        except ConnectionResetError:
            print(f"[SERVER] Client '{client_name}' disconnected abruptly")
        except Exception as e:
            print(f"[SERVER] Error with client '{client_name}': {e}")
        finally:
            # Remove client from active list
            self.active_clients = [c for c in self.active_clients 
                                 if c['socket'] != client_socket]
            
            # Clear stored data for this client
            if client_name and client_name in self.client_data:
                print(f"[SERVER] Clearing stored data for '{client_name}'")
                del self.client_data[client_name]
            
            client_socket.close()
            print(f"[SERVER] Client '{client_name}' disconnected")

    def send_json_response(self, client_socket, response_data):
        """Send JSON response without truncation"""
        try:
            response_json = json.dumps(response_data)
            # Send the length first, then the data
            client_socket.send(response_json.encode('utf-8'))
        except Exception as e:
            print(f"[SERVER] Error sending response: {e}")

    def process_request(self, client_socket, client_name, request):
        """Process client request and call appropriate API"""
        option = request.get('option', '').lower()
        params = request.get('parameters', {})
        
        print(f"[SERVER] Request from '{client_name}': {option} with params {params}")
        
        if option == 'headlines':
            self.get_headlines(client_socket, client_name, params)
        elif option == 'sources':
            self.get_sources(client_socket, client_name, params)
        elif option == 'details':
            self.get_details(client_socket, client_name, params)
        else:
            error_response = {
                'status': 'error',
                'message': f'Invalid option: {option}'
            }
            self.send_json_response(client_socket, error_response)

    def get_proper_filename(self, client_name, option, params):
        """Generate filename as per project requirements: <client_name> <option> <group_ID>.json"""
        # Map options to proper names
        option_map = {
            'headlines': {
                'keyword': 'keyword_search',
                'category': 'category_search',
                'country': 'country_search',
                'default': 'all_headlines'
            },
            'sources': {
                'category': 'sources_by_category',
                'country': 'sources_by_country', 
                'language': 'sources_by_language',
                'default': 'all_sources'
            }
        }
        
        # Determine the specific option
        option_type = 'default'
        if 'keyword' in params:
            option_type = 'keyword'
        elif 'category' in params:
            option_type = 'category'
        elif 'country' in params:
            option_type = 'country'
        elif 'language' in params:
            option_type = 'language'
        
        # Get the final option name
        final_option = option_map.get(option, {}).get(option_type, option_type)
        
        # Generate filename (replace spaces with underscores for filesystem)
        filename = f"{client_name}_{final_option}_{self.group_id}.json"
        return filename

    def store_client_data(self, client_name, data_type, data):
        """Store client data for later details retrieval"""
        if client_name not in self.client_data:
            self.client_data[client_name] = {}
        self.client_data[client_name][data_type] = data

    def get_headlines(self, client_socket, client_name, params):
        """Get top headlines from NewsAPI"""
        try:
            # Build API parameters
            api_params = {
                'apiKey': self.api_key,
                'pageSize': 15  # Limit to 15 items
            }
            
            # Add allowed parameters
            if 'country' in params and params['country'] in self.allowed_countries:
                api_params['country'] = params['country']
            if 'category' in params and params['category'] in self.allowed_categories:
                api_params['category'] = params['category']
            if 'keyword' in params and params['keyword']:
                api_params['q'] = params['keyword']
                
            # For "List all headlines" with no parameters
            if not api_params.get('country') and not api_params.get('category') and not api_params.get('q'):
                api_params['country'] = 'us'
            
            # Call NewsAPI
            print(f"[DEBUG] API params: {api_params}")
            response = requests.get(f"{self.base_url}/top-headlines", params=api_params)
            data = response.json()
            
            if data.get('status') == 'ok':
                # Save to JSON file with proper naming
                filename = self.get_proper_filename(client_name, 'headlines', params)
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"[SERVER] Saved headlines to {filename}")
                
                # Prepare list response (limited information)
                articles_list = []
                for i, article in enumerate(data.get('articles', [])[:15]):
                    articles_list.append({
                        'index': i + 1,
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'author': article.get('author', 'Unknown'),
                        'title': article.get('title', 'No title'),
                        # Store full article for details
                        'full_data': article
                    })
                
                # Store data for details retrieval
                self.store_client_data(client_name, 'headlines', articles_list)
                
                # Send list to client
                response_data = {
                    'status': 'success',
                    'type': 'headlines_list',
                    'data': articles_list,
                    'message': f"Found {len(articles_list)} headlines"
                }
                
            else:
                response_data = {
                    'status': 'error',
                    'message': data.get('message', 'API error')
                }
                
        except Exception as e:
            response_data = {
                'status': 'error',
                'message': f'Failed to fetch headlines: {str(e)}'
            }
        
        self.send_json_response(client_socket, response_data)

    def get_sources(self, client_socket, client_name, params):
        """Get news sources from NewsAPI"""
        try:
            # Build API parameters
            api_params = {
                'apiKey': self.api_key
            }
            
            # Add allowed parameters
            if 'country' in params and params['country'] in self.allowed_countries:
                api_params['country'] = params['country']
            if 'language' in params and params['language'] in self.allowed_languages:
                api_params['language'] = params['language']
            if 'category' in params and params['category'] in self.allowed_categories:
                api_params['category'] = params['category']
            
            # Call NewsAPI
            response = requests.get(f"{self.base_url}/sources", params=api_params)
            data = response.json()
            
            if data.get('status') == 'ok':
                # Save to JSON file with proper naming
                filename = self.get_proper_filename(client_name, 'sources', params)
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"[SERVER] Saved sources to {filename}")
                
                # Prepare list response
                sources_list = []
                for i, source in enumerate(data.get('sources', [])[:15]):
                    sources_list.append({
                        'index': i + 1,
                        'name': source.get('name', 'Unknown'),
                        # Store full source for details
                        'full_data': source
                    })
                
                # Store data for details retrieval
                self.store_client_data(client_name, 'sources', sources_list)
                
                # Send list to client
                response_data = {
                    'status': 'success',
                    'type': 'sources_list',
                    'data': sources_list,
                    'message': f"Found {len(sources_list)} sources"
                }
                
            else:
                response_data = {
                    'status': 'error',
                    'message': data.get('message', 'API error')
                }
                
        except Exception as e:
            response_data = {
                'status': 'error',
                'message': f'Failed to fetch sources: {str(e)}'
            }
        
        self.send_json_response(client_socket, response_data)

    def get_details(self, client_socket, client_name, params):
        """Get detailed information for a specific item"""
        try:
            item_type = params.get('type', '')
            item_index = params.get('index', 0)
            
            # Get the stored data for this client
            if client_name not in self.client_data:
                response_data = {
                    'status': 'error',
                    'message': 'No data available. Please search first.'
                }
                self.send_json_response(client_socket, response_data)
                return
            
            if item_type == 'headline':
                # Get headlines data
                headlines_data = self.client_data[client_name].get('headlines', [])
                if 0 <= item_index - 1 < len(headlines_data):
                    article = headlines_data[item_index - 1].get('full_data', {})
                    
                    details = {
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'author': article.get('author', 'Unknown'),
                        'title': article.get('title', 'No title'),
                        'url': article.get('url', 'Not available'),
                        'description': article.get('description', 'No description'),
                        'publishedAt': article.get('publishedAt', 'Not specified'),
                        'content': article.get('content', 'No content available')
                    }
                    
                    response_data = {
                        'status': 'success',
                        'type': 'headline_details',
                        'data': details
                    }
                else:
                    response_data = {
                        'status': 'error',
                        'message': f'Invalid index. Please select 1-{len(headlines_data)}'
                    }
                    
            elif item_type == 'source':
                # Get sources data
                sources_data = self.client_data[client_name].get('sources', [])
                if 0 <= item_index - 1 < len(sources_data):
                    source = sources_data[item_index - 1].get('full_data', {})
                    
                    details = {
                        'name': source.get('name', 'Unknown'),
                        'country': source.get('country', 'Not specified'),
                        'description': source.get('description', 'No description'),
                        'url': source.get('url', 'Not available'),
                        'category': source.get('category', 'Not specified'),
                        'language': source.get('language', 'Not specified')
                    }
                    
                    response_data = {
                        'status': 'success',
                        'type': 'source_details',
                        'data': details
                    }
                else:
                    response_data = {
                        'status': 'error',
                        'message': f'Invalid index. Please select 1-{len(sources_data)}'
                    }
            else:
                response_data = {
                    'status': 'error',
                    'message': f'Invalid item type: {item_type}'
                }
            
        except Exception as e:
            response_data = {
                'status': 'error',
                'message': f'Failed to get details: {str(e)}'
            }
        
        self.send_json_response(client_socket, response_data)

def main():
    server = NewsAPIServer()
    server.start()

if __name__ == "__main__":
    main()