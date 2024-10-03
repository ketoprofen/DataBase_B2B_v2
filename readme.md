
# DataBaseB2B

```

        ______
       //  ||\ \
 _____//___||_\ \___
 )  _          -    _(
 |_/ \__________/ \__|
___\_/____________\_/____


```

## Table of Contents
- [Introduction](#introduction)
- [Installation and Setup](#installation-and-setup)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Future Improvements](#future-improvements)

## Introduction
**DataBaseB2B** is a Python-based application designed to manage and track vehicle data in a business-to-business context. It provides a comprehensive interface for inserting, updating, searching, and exporting data related to vehicle repairs, maintenance status, and more.

## Installation and Setup

Follow these steps to set up and run **DataBaseB2B** on a Windows machine.

1. **Install Python:**
   Make sure you have Python installed. If not, download it from [Python's official website](https://www.python.org/downloads/).

2. **Install Dependencies:**
   Use `pip` to install all required libraries. Open a terminal or command prompt and run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup:**
   Ensure that the `app_database.db` SQLite database file is in the project directory. This file will be created automatically upon the first launch if it does not already exist.

4. **Run the Application:**
   To launch the application, navigate to the project directory and run:
   ```bash
   python main.py
   ```

5. **Login Information:**
   Use the default login credentials to access the app:
   - Username: `b2b`
   - Password: `0000v`

## Dependencies
The following Python libraries are required to run this project:
- `PyQt5`: For GUI development
- `sqlite3`: For database management
- `pandas`: For data manipulation
- `bcrypt`: For password hashing and verification

These dependencies can be manually installed (skip this step if the dependencies were installed at step 2) through `pip` using:
```bash
pip install PyQt5 sqlite3 pandas bcrypt
```

## Usage
The application consists of several tabs:
1. **Dati Tab:** For inserting and updating vehicle records.
2. **Notifiche Tab:** For viewing notifications and status updates based on predefined conditions.
3. **Stato Lavorazioni Tab:** For tracking the current status of various vehicle work orders.

## Future Improvements
The following features are planned for future releases:

1. **User Authentication Enhancements:**
   - **Multi-User Support:** Allow multiple user roles (admin, mechanic, etc.) with different permissions.
   - **Password Reset Feature:** Allow users to reset their password securely.

2. **Data Analytics & Reports:**
   - **Advanced Filtering and Sorting:** Allow more complex data analysis, such as filtering by date ranges or status.
   - **PDF/Excel Report Generation:** Provide more options for exporting data in different formats.

3. **Notification System Upgrades:**
   - **Automated Email Notifications:** Alert users about important status updates via email.
   - **Customizable Notification Rules:** Allow users to set rules for when they receive alerts based on vehicle status or work progress.

4. **Database Optimization:**
   - **Data Archival:** Provide an option to archive older records to maintain performance.
   - **Scheduled Backups:** Implement automatic backup and restore functionalities.

5. **UI/UX Improvements:**
   - **Dark Mode:** Provide an option for a dark theme in the user interface.
   - **Mobile Responsiveness:** Enhance the interface to support mobile devices.

## Usefull commands:
pyinstaller --onefile --windowed DataBaseB2B.py --add-data "app_database.db;."