# On-Campus Event Management System  
**DAMG6210 - Database Management and Database Design | Project by Group 6**

## Overview  
This repository contains the implementation of the **On-Campus Event Management System**, a comprehensive project designed to manage on-campus events with the following features:  

- **Visualizations:**  
  Created in both Power BI and Tableau.  
- **Graphical User Interface (GUI):**  
  Built using Python Flask and Jinja2. The GUI provides CRUD functionalities and allows users to experience the platform as an **admin**, **host**, or **participant**.

All required documents, scripts, and resources have been uploaded to this repository. The project files are publicly available at:  
[GitHub Repository Link](https://github.com/Belide-Aakash/DAMG6210_Group_6)

---

## File Execution Order  
The following scripts must be executed in the specified order to avoid errors, particularly during encryption setup:

1. `create_tables.sql`  
2. `insert_script.sql`  
3. `indexes_script.sql`  
4. `encryption_script.sql`  
5. `psm_script.sql`  

Running the scripts in nay other order may lead to errors.

---

## GUI Setup Instructions  

### Prerequisites  
1. Install Python (preferably 3.8 or later).  
2. Set up a virtual environment (optional but recommended).  

### Steps  
1. Install dependencies by running:  
   ```bash
   pip install -r requirements.txt
2.	Create a .env file in the root directory and add the following details:
    ```bash
    DB_USERNAME=<Your_Local_DB_Username>
    DB_PASSWORD=<Your_Local_DB_Password>
3.	Ensure your local database is running and accessible to external clients.
4.	(Optional) Activate your virtual environment.
5.	Navigate to the Event_Management_GUI folder in the terminal:
    ```bash
    cd Event_Management_GUI
6.	Run the Flask application:
    ```bash
    python main.py
7.	Open the link provided in the terminal to log in or sign up as a new participant.

---

## Notes
* **User Credentials:**
Test usernames (emails) and passwords can be found using the test code in encryption_script.sql.

* **Version Compatibility:**
The Flask application may encounter issues if the libraries or Python version differ significantly.

* **Contact:**
For any setup or demo-related assistance, please reach out to Aakash Belide.

* **Testing PSM Commands:**
Test commands for PSM are provided below each script in the repository for reference.