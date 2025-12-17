# **ITNE352 Network Programming Project**
## **News Client-Server System**

## **Group Information**
- Group: GA5
- Course: ITNE352 Network Programming  
- Semester: First Semester 2025-2026
- Instructor: Dr. Mohammed Almeer

## **Features**

### *Server*
- TCP multi-threaded server (handles ≥3 clients)
- NewsAPI integration for real-time news
- Saves data to JSON files: `clientname_option_GA5.json`
- Multi-client support with data isolation
- Object-Oriented Programming (OOP) implementation

### *Client*
- 3 menus: Main, Headlines, Sources
- 8 search options (keyword, category, country, language)
- Input validation for all parameters
- Details view for selected items
- Object-Oriented Programming (OOP) implementation

## **Object-Oriented Programming Implementation**

Our project uses OOP principles with these main classes:

### **NewsAPIServer Class**
- **Properties**: `api_key`, `base_url`, `client_data`, `active_clients`
- **Methods**: 
  - `handle_client()` - Manages client connections
  - `get_headlines()` - Fetches news from API
  - `get_sources()` - Gets news sources
  - `get_details()` - Provides detailed information
- **Purpose**: Central server handling multiple clients

### **NewsClient Class**  
- **Properties**: `socket`, `username`, `current_headlines`
- **Methods**:
  - `connect_to_server()` - Establishes connection
  - `send_request()` - Sends JSON requests
  - `display_menu()` - User interface
- **Purpose**: Client-side interaction with server

## **How to Run**
### *1. Install Requirements 'if needed'*
```bash
pip install requests
```

### *2. Start Server*
```bash
python3 server.py
```

### *3. Start Client*
```bash
python3 client.py
```

For custom server: `python3 client.py [IP] [PORT]`

## *Usage*
### *Main Menu*

1. Search Headlines
2. List of Sources  
3. Quit


### *Headlines Menu*

1. Search by keyword
2. Search by category
3. Search by country
4. List all headlines
5. Back to Main Menu


### *Sources Menu*

1. Search by category
2. Search by country
3. Search by language  
4. List all sources
5. Back to Main Menu


## *Supported Parameters*
- **Countries:** au, ca, jp, ac, sa, kr, us, ma
- **Languages:** ar, en
- **Categories:** business, general, health, science, sports, technology

## *the project includes the following*
- ✅ TCP socket server with multi-threading
- ✅ NewsAPI integration
- ✅ JSON file saving with correct naming
- ✅ All 8 menu options from Table 1
- ✅ Input validation for all parameters
- ✅ Details view for selected items
- ✅ Multi-client support (≥3 clients)
- ✅ Error handling and clean exit

## *Project Files*
- `server.py` - Multi-threaded TCP server
- `client.py` - Interactive client application  
- `README.md` - This documentation
- `requirements.txt` - Python dependencies
- `.gitignore` - Excludes generated files

## ITNE352-Project-Group-GA5/
├── server.py
├── client.py
├── README.md
├── requirements.txt
└── .gitignore