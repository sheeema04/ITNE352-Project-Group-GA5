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
        
        # Allowed parameters from Table provided
        self.allowed_countries = ['au', 'ca', 'jp', 'ac', 'sa', 'kr', 'us', 'ma']
        self.allowed_languages = ['ar', 'en']
        self.allowed_categories = ['business', 'general', 'health', 'science', 'sports', 'technology']
        
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
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                    
        except ConnectionResetError:
            print(f"[SERVER] Client '{client_name}' disconnected abruptly")
        except Exception as e:
            print(f"[SERVER] Error with client '{client_name}': {e}")
        finally:
            # Remove client from active list
            self.active_clients = [c for c in self.active_clients 
                                 if c['socket'] != client_socket]
            client_socket.close()
            print(f"[SERVER] Client '{client_name}' disconnected")

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
            client_socket.send(json.dumps(error_response).encode('utf-8'))

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
            
            # Call NewsAPI
            response = requests.get(f"{self.base_url}/top-headlines", params=api_params)
            data = response.json()
            
            if data.get('status') == 'ok':
                # Save to JSON file
                filename = f"{client_name}_headlines_{id(client_socket)}.json"
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
        
        client_socket.send(json.dumps(response_data).encode('utf-8'))

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
                # Save to JSON file
                filename = f"{client_name}_sources_{id(client_socket)}.json"
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
        
        client_socket.send(json.dumps(response_data).encode('utf-8'))

    def get_details(self, client_socket, client_name, params):
        """Get detailed information for a specific item"""
        try:
            item_type = params.get('type', '')
            item_index = params.get('index', 0)
            
            # for real implementation, you get the full data
            # from the previously saved response or cache
            
            if item_type == 'headline':
                details = {
                    'source': 'Example Source',
                    'author': 'Example Author',
                    'title': 'Example Title',
                    'description': 'Detailed description of the article',
                    'url': 'https://example.com/article',
                    'publishedAt': datetime.now().isoformat(),
                    'content': 'Full content of the article...'
                }
            elif item_type == 'source':
                details = {
                    'name': 'Example News Source',
                    'country': 'us',
                    'description': 'Detailed description of the news source',
                    'url': 'https://example.com',
                    'category': 'general',
                    'language': 'en'
                }
            else:
                details = {}
            
            response_data = {
                'status': 'success',
                'type': f'{item_type}_details',
                'data': details
            }
            
        except Exception as e:
            response_data = {
                'status': 'error',
                'message': f'Failed to get details: {str(e)}'
            }
        
        client_socket.send(json.dumps(response_data).encode('utf-8'))

def main():
    server = NewsAPIServer()
    server.start()

if __name__ == "__main__":
    main()