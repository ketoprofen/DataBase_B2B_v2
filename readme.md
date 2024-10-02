# SAFE Application

SAFE (Sistema di Amministrazione e Fleet Management) is a fleet management application designed to manage fleet cars, including notifications, record insertion, status updates, and exporting data to Excel. The app provides functionalities such as authentication, data imports/exports, and an intuitive tab-based user interface built using PyQt5.

## Features
- **User Authentication**: Secure login system with password encryption using `bcrypt`.
- **Fleet Management**: Add, update, and track fleet vehicles (targa, stato, data, etc.).
- **Notifications**: Visual notifications for upcoming events or actions (e.g., maintenance due), with color-coded urgency.
- **Data Export**: Export fleet data to Excel for easy reporting and sharing.
- **Email Notifications**: Send emails with selected data to designated recipients.
- **Modular Design**: Each tab of the application is modularized in separate classes/files for better organization and scalability.



# Usefull commands:
pyinstaller --onefile --windowed DataBaseB2B.py --add-data "app_database.db;."