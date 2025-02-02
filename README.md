### AlarmBot  
## Project Description  

This project is a Telegram bot for monitoring air raid alerts in Ukraine. The bot allows users to select a region for notifications and receive information about active alerts in the specified area. The data is fetched via an API and updated in real time.  

## Features  
- Request the current air raid alert status for the selected region.  
- Automatic notifications when the alert status changes.  
- Multi-threaded monitoring for each user.  
- Running a Flask server to host the bot.  

## Technologies Used  
- Python 3  
- Flask  
- Telegram Bot API  
- `requests` (for fetching data from the API)  
- `pytz` (for time zone adjustment)  

## Project Setup  
1. Install the required dependencies:  
   ```sh
   pip install -r requirements.txt
   ```  
2. Run the bot:  
   ```sh
   python bot.py
   ```  

## IMPORTANT  
The API token for retrieving alert data is sent via email and **must not be published** or shared with third parties. This is necessary for security and to prevent unauthorized access.  

## Bot Usage Examples  
- Example of the bot working for another user: [Screenshot](https://ibb.co/zVyXJNh4)  
- Example of the bot working for me: [Screenshot](https://ibb.co/gL625BX2)  

## Author  
Developer: [Глушко Анна]
