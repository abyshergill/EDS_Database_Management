## 🔬 Enhanced EDS Data Collection System Version 2.0
A modern, secure data collection application for managing EDS (Energy Dispersive X-ray Spectroscopy) analysis results with VHX microscopy images.

### 🎯 Usage Guide

**Adding New Data**
- Click "➕ Add Data"
- Fill in the component name
- Select VHX and EDS images
- Add remarks/notes
- Click "💾 Save Entry"

**Viewing Images**
- Double-click any row in the data table
- View both VHX and EDS images side by side
- Download images individually

**Searching Data**
- Enter component name in search box
- Click "🔍 Search"
- Use "🔄 Clear" to show all entries

**Updating Entries**
- Select a row and click "✏️ Update Data"
- Modify any fields as needed
- Change images if required
- Click "💾 Save Changes"

```bash
📁 File Structure
EDS_Application/
├── main.py              
├── config.json          
├── requirements.txt     
├── license.txt          
├── README.md            
├── settings/            
│   └── config.json           
│   └── logging_config.py           
│   └── configmanager.py        
├── subwindows/                
│   └──loginwindows.py          
│   └── mainwindows.py        
│   └── registerwindows.py          
├── data/                
│   └── eds.db         # I already added username admin password 123456 for testing  
├── icon/                
│   └── logo.ico         
└── logs/                
    └── eds_app.log      

```
## Note:
This project main.py file contain both register and login option.
But in organzation, Two copyies 
- First copy under Support team which can generate the new account so in their copy will have both login and register option.
- Second copy for employee where then can login and use this dekstip application 

---

**🐛 Troubleshooting**

**Common Issues**

- "Failed to load image" error
    - Ensure image files are valid JPG/PNG format
    - Check file permissions


- Database connection errors
    - Verify **config.json** settings
    - Ensure data directory exists
    - Check file permissions


- Login issues
    - Use "Register" to create new account
    - Check username/password spelling
    - Verify database is properly initialized

### ✨ New Features in Version 2.0

**🔐 User Authentication**

- Secure login system with encrypted password storage
- User registration for new accounts
- Session management with user tracking
- All data entries are now linked to the user who created them

**🎨 Modern UI Design**

- Contemporary design with modern color scheme
- Enhanced typography using Segoe UI font
- Improved layouts with better spacing and organization
- Interactive buttons with hover effects and modern styling
- Professional data grid with better column management

**🗄️ Database Enhancements**

- Configurable database location via config.json
- PostgreSQL support (commented out, ready to use)
- Enhanced data model with user tracking and timestamps
- Audit logging capabilities
- Better error handling and data validation

**🔧 Configuration Management**

- External configuration file (config.json)
- Flexible database settings
- UI customization options
- Easy deployment configuration

**📋 Prerequisites**

- Python 3.7 or higher
- tkinter (usually comes with Python)
- PIL/Pillow for image processing

**🚀 Installation**

Clone or download the application files
Install dependencies:
```bash
pip install -r requirements.txt
```

Create necessary directories:
```bash
mkdir data logs
```

Run the application:
```bash
python master.py
```

**⚙️ Configuration**

The application uses a config.json file for configuration. Key settings include:

Database Configuration
```bash
json{
    "database": {
        "type": "sqlite",
        "sqlite_path": "data/eds.db"
    }
}
```
**PostgreSQL Setup (Optional)**

- To use PostgreSQL instead of SQLite:
- Install PostgreSQL driver:
    ```bash
    pip install psycopg2-binary
    ```
**Uncomment PostgreSQL lines in the code:**
- Uncomment import statement: import psycopg2
- Uncomment PostgreSQL initialization methods
- Uncomment PostgreSQL database operations


**Update config.json:**
```bash
json{
    "database": {
        "type": "postgresql",
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "database": "eds_db",
            "user": "your_username",
            "password": "your_password"
        }
    }
}
```

**👤 First Time Setup**

- Launch the application
- Click "Register" to create your first user account
- Login with your new credentials
- Start adding EDS data entries

**🔒 Security Features**

- Password hashing using SHA-256
- User session management
- Data access control (users can only see their own entries in some views)
- Input validation and sanitization
- Secure file handling for image uploads

**📊 Enhanced Data Management**
- New Data Fields
    - **Created By:** Tracks which user created each entry
    - **Creation Date:** Automatic timestamp for new entries
    - **Modified Date:** Tracks when entries were last updated

- Improved Search
    - Case-insensitive search by component name
    - Clear search functionality
    - Better result display

- Enhanced Image Handling
    - Improved image previews in dialogs
    - Better error handling for image operations
    - Organized download functionality

---



**Logging**
---

- Check **logs/eds_app.log** for detailed error information
Log level can be adjusted in config.json

- 🔄 Migration from Old Version
If you have an existing EDS database:

---
**Backup your current eds.db file**
---
- Run the new application - it will automatically add new columns
- Create user accounts for existing data access
- Existing data will be preserved but may show "N/A" for user fields

**🚀 Future Enhancements**

Planned features for future versions:

- Data export to Excel/CSV
- Batch image processing
- Advanced search filters
- Data visualization charts
- Backup/restore functionality
- Multi-user collaboration features

📞 Support
For issues or questions:
- Check the troubleshooting section
- Review log files for errors
- Create an issue on the project repository

## 👨‍💻 Developer
**Devloped and Maintained by:** Kuldeep Singh ( Aby )

**GitHub:** github.com/abyshergill

