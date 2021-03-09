from flask import render_template
from flask import Flask
from flask import request
import requests
from flask import Markup
import sched
import time
import pyttsx3
import json
from uk_covid19 import Cov19API
import logging


FORMAT = '%(levelname)s: %(asctime)s %(message)s'
logging.basicConfig(level=logging.NOTSET, filename='system_log.log',
                    format=FORMAT)

alarms = []
notifications = []
nd_flag = 0


def current_time_hhmmss() -> str:
    """Gets the current time in the 'hour:minutes:seconds' format."""
    hours = str(time.gmtime().tm_hour)
    if len(hours) == 1:
        hours = "0" + hours
    minutes = str(time.gmtime().tm_min)
    if len(minutes) == 1:
        minutes = "0" + minutes
    seconds = str(time.gmtime().tm_sec)
    if len(seconds) == 1:
        seconds = "0" + seconds
    return (hours + ":" + minutes + ":"
            + seconds)


def current_time_yyyymmdd() -> str:
    """Gets the current date in the 'year-month-day' format."""
    months = str(time.gmtime().tm_mon)
    if len(months) == 1:
        months = "0" + months
    days = str(time.gmtime().tm_mday)
    if len(days) == 1:
        days = "0" + days
    return (str(time.gmtime().tm_year) + "-" + months + "-"
            + days)


def current_time_yyyymmddhhmmss() -> str:
    """Returns the date and time in the 'date at time' format."""
    return str(current_time_yyyymmdd()
               + " at " + current_time_hhmmss())


def current_seconds_since_2020() -> int:
    """
    Finds the amount of seconds between 2020-01-01 00:00:00 and now,
    ignoring leap years and treating all months as 31 days long
    """
    current_time = current_time_yyyymmddhhmmss()
    # Edits the current date and time format to be more easily split.
    current_time = current_time.replace("on ", "")
    current_time = current_time.replace("-", "/")
    current_time = current_time.replace(" at ", "/")
    current_time = current_time.replace(":", "/")
    # Splits the date and time to find how many of each have passed since 2020.
    years_since = int(current_time.split('/')[0]) - 2020
    months_since = int(current_time.split('/')[1]) - 1
    days_since = int(current_time.split('/')[2]) - 1
    hours_since = int(current_time.split('/')[3])
    minutes_since = int(current_time.split('/')[4])
    # seconds_since = int(current_time.split('/')[5])
    # Converts to seconds
    abs_seconds_since = ((((years_since*365+(months_since*31)+days_since)*24
                          + hours_since)*60+minutes_since)*60)
    return abs_seconds_since


def alarm_seconds_2020(alarm_time: str) -> int:
    """
    Finds the amount of seconds between 2020-01-01 00:00:00 and when the alarm
    should go off, ignoring leap years and treating all months as 31 days long.

    Keyword arguments:
    alarm_time -- string generated from user submission (alarm content),
                  containg the date and time in the format:
                  'Alarm for year-month-day at hour:minutes will...'
    """
    time = str(alarm_time)
    # Edits the current date and time format to be more easily split.
    time = time.replace("Alarm for ", "")
    time = time.replace("-", "/")
    time = time.replace(" at ", "/")
    time = time.replace("T", "/")
    time = time.replace(":", "/")
    time = time.replace(" will", "/")
    # Splits the time to find how many of each will have passed since 2020.
    years_since = int(time.split('/')[0]) - 2020
    months_since = int(time.split('/')[1]) - 1
    days_since = int(time.split('/')[2]) - 1
    hours_since = int(time.split('/')[3])
    minutes_since = int(time.split('/')[4])
    # Converts to seconds
    abs_seconds_since = ((((years_since*365+(months_since*31)+days_since)*24
                          + hours_since)*60+minutes_since)*60)
    return abs_seconds_since


def alarm_management(alarm_time: str, alarm_name: str, news_flag: str,
                     weather_flag: str):
    """
    Gets the user submitted data from the alarm form then, if applicable,
    formats and appends the data to the alarm list.

    Keyword arguments:
    alarm_time -- when the user wanted the alarm to go of in the format:
                  'yyyy-mm-ddThh:mm'
    alarm_name -- what the user labelled the alarm
    news_flag -- a string that differs depending on whether the user checked
                 the 'include new?' box
    weather_flag -- a string that differs depending on whether the user checked
                    the 'include weather?' box
    """
    global alarms
    # Only adds an alarm if the user entered a time that's in the future.
    if ((alarm_time and alarm_name)
       and (alarm_seconds_2020(alarm_time) - current_seconds_since_2020()
       > 0)):
        if alarms:
            count = 0
            for alarm in alarms:
                # Adds alarms so that those going off earlier appear first.
                if (alarm_seconds_2020(alarm_time)
                   == alarm_seconds_2020(alarm['content'])):
                    logging.error("You cannot set multiple alarms for the same"
                                  + " time\n")
                    break
                elif (alarm_seconds_2020(alarm_time)
                      < alarm_seconds_2020(alarm['content'])):
                    alarms.insert(count, (dict(title=alarm_name
                                  + " (placed on "
                                  + current_time_yyyymmddhhmmss() + ")",
                                  content="Alarm for "
                                  + alarm_time.replace("T", " at ") + " will "
                                  + news_flag + " will " + weather_flag)))
                    break
                elif count == len(alarms)-1:
                    alarms.append(dict(title=alarm_name + " (placed on "
                                  + current_time_yyyymmddhhmmss() + ")",
                                  content="Alarm for "
                                  + alarm_time.replace("T", " at ") + " will "
                                  + news_flag + " will " + weather_flag))
                    break
                count += 1
        else:
            alarms.append(dict(title=alarm_name + " (placed on "
                               + current_time_yyyymmddhhmmss() + ")",
                               content="Alarm for "
                               + alarm_time.replace("T", " at ") + " will "
                               + news_flag + " will " + weather_flag))
    else:
        logging.error("You cannot set an alarm for the past or never.\n")


def announcement():
    """
    Checks to see if there is an alarm that needs to go off and, if so, a
    list is formatted from API data to be announecd.
    """
    global alarms
    # If alarms in empty there definitely isn't an alarm needing to be spoken.
    if alarms:
        # Checks if the alarm time for the next alarm is in the past.
        if (alarm_seconds_2020(alarms[0]['content'].split(' will ')[0][-19:])
           <= current_seconds_since_2020()):
            toAnnounce = alarms.pop(0)  # Removes the alarm being announced.
            # log
            announceLog = "This alarm will be announced and deleted: \n\n"
            announceLog = (announceLog + "\tTitle = " + toAnnounce['title']
                           + "\n")
            announceLog = (announceLog + "\tContent = " + toAnnounce['content']
                           + "\n")
            logging.warning(announceLog)
            #
            toSpeak = covid_call()  # Creates the list that may be added to.
            # Uses the 6th item in the config file.
            with open('config.json', 'r') as f:
                json_file = json.load(f)
            f.close()
            local = json_file["location"]["covid"]["name"]
            #
            toSpeak[0] = "Statistics for Covid-19 in " + local + ": "
            # Checks if 'include new?' box was ticked.
            if toAnnounce['content'].split(' will ')[1] == "include news and":
                # Uses the 1st item in the config file.
                with open('config.json', 'r') as f:
                    json_file = json.load(f)
                f.close()
                api_key = json_file["API-keys"]["news"]
                # Uses the 3rd item in the config file.
                country = json_file["location"]["news"]
                #
                everything_base_url = "https://newsapi.org/v2/top-headlines?"
                everything_complete_url = (everything_base_url + "country="
                                           + country + "&apiKey=" + api_key)
                everything_response = requests.get(everything_complete_url)
                everything_response = everything_response.json()
                everything_articles = everything_response["articles"]
                count = 0
                toSpeak.append("The top News Headline is: ")
                for article in everything_articles:
                    toSpeak.append(article['title'].replace(" - ", " from "))
                    count += 1
                    if count == 1:
                        break
            # Checks if 'include weather?' box was ticked.
            if toAnnounce['content'].split(' will ')[2] == "include weather":
                w_base_url = "http://api.openweathermap.org/data/2.5/weather?"
                # Uses the 4th item in the config file.
                with open('config.json', 'r') as f:
                    json_file = json.load(f)
                f.close()
                location = json_file["location"]["weather"]
                # Uses the 2nd item in the config file.
                w_api_key = json_file["API-keys"]["weather"]
                #
                weather_complete_url = (w_base_url + "q=" + location
                                        + "&APPID=" + w_api_key)
                weather_response = requests.get(weather_complete_url)
                weather_response = weather_response.json()
                w_description = weather_response['weather'][0]['description']
                w_temperature = (str(float(weather_response['main']['temp'])
                                 - 273.15)[:4] + " degrees Celcius")
                w_mintemp = (str(float(weather_response['main']['temp_min'])
                             - 273.15)[:4] + " degrees Celcius")
                w_maxtemp = (str(float(weather_response['main']['temp_max'])
                             - 273.15)[:4] + " degrees Celcius")
                weather_speed = (str(weather_response['wind']['speed'])
                                 + " meters per second")
                weather_list = []
                weather_list.append("There are " + w_description)
                weather_list.append("Current Temperature is " + w_temperature)
                weather_list.append("Minimum Temperature is " + w_mintemp)
                weather_list.append("Maximum Temperature is " + w_maxtemp)
                weather_list.append("Wind Speed is " + weather_speed)
                toSpeak.append("Weather information for " + location + ": ")
                for entry in weather_list:
                    toSpeak.append(entry)
            speak_now(toSpeak)  # Sends the created list to be spoken.
            announcement()  # To check if any other alarms need announcing.


def speak_now(toSpeak: list):
    """
    Runs text-to-speech on argument.

    Keyword arguments:
    toSpeak -- list of what needs to be spoken
    """
    engine = pyttsx3.init()
    engine.say(toSpeak)
    engine.runAndWait()


def notification_management():
    """
    Checks to see if the time is the same as when notifications should go off,
    if so, then collects the API data to add to the notification list.
    """
    global notifications
    global nd_flag
    # Uses the 7th item in the config file.
    with open('config.json', 'r') as f:
        json_file = json.load(f)
    f.close()
    minute_hand = json_file["notif-minute"]
    #
    times = current_time_hhmmss()
    # Checks if the current minute is the same notification minute.
    if times.split(':')[1] == minute_hand and nd_flag == 0:
        dict_insert = dict(title="Update: " + current_time_yyyymmddhhmmss(),
                           content=get_notification_content())
        if notifications:
            if notifications[0]['title'][:27] != dict_insert['title'][:27]:
                notifications.insert(0, dict_insert)
                nd_flag_manage()

        else:
            notifications.append(dict_insert)
            nd_flag_manage()


def get_notification_content() -> str:
    """
    Gets and formats the API data for notifications.
    """
    # Uses the 1st item in the config file.
    with open('config.json', 'r') as f:
        json_file = json.load(f)
    f.close()
    api_key = json_file["API-keys"]["news"]
    # Uses the 3rd item in the config file.
    country = json_file["location"]["news"]
    #
    everything_base_url = "https://newsapi.org/v2/top-headlines?"
    everything_complete_url = (everything_base_url + "country=" + country
                               + "&apiKey=" + api_key)
    everything_response = requests.get(everything_complete_url)
    everything_response = everything_response.json()
    everything_articles = everything_response["articles"]
    display = covid_call()  # Creates list of covid info to be added to.
    count = 0
    display.append(Markup('<u>Top News Headlines:</u> '))
    for article in everything_articles:
        toAppend = Markup(
                   '<a href="{url}" target="_blank">{message}</a>,'.format(
                          url=article['url'],
                          message=article['title'],
                   ))
        display.append(toAppend)
        count += 1
        if count == 5:
            break
    weather_base_url = "http://api.openweathermap.org/data/2.5/weather?"
    # Uses the 4th item in the config file.
    with open('config.json', 'r') as f:
        json_file = json.load(f)
    f.close()
    location = json_file["location"]["weather"]
    # Uses the 2nd item in the config file.
    w_api_key = json_file["API-keys"]["weather"]
    #
    weather_complete_url = (weather_base_url + "q=" + location + "&APPID="
                            + w_api_key)
    weather_response = requests.get(weather_complete_url)
    weather_response = weather_response.json()
    weather_description = weather_response['weather'][0]['description']
    w_temperature = (str(float(weather_response['main']['temp']) - 273.15)[:4]
                     + chr(176) + "C")
    w_mintemp = (str(float(weather_response['main']['temp_min']) - 273.15)[:4]
                 + chr(176) + "C")
    w_maxtemp = (str(float(weather_response['main']['temp_max']) - 273.15)[:4]
                 + chr(176) + "C")
    weather_speed = str(weather_response['wind']['speed']) + "m/s"
    weather_list = []
    weather_list.append("Description: " + weather_description)
    weather_list.append("Current Temperature: " + w_temperature)
    weather_list.append("Minimum Temperature: " + w_mintemp)
    weather_list.append("Maximum Temperature: " + w_maxtemp)
    weather_list.append("Wind Speed: " + weather_speed)
    display.append(Markup('<u>Weather in {l}:</u> '.format(l=location)))
    for entry in weather_list:
        display.append(entry)
    display_string = ""
    #  Changes list into a long line broken string.
    for stuff in display:
        display_string = display_string + stuff + Markup('<br>')
    return display_string


def covid_call() -> list:
    """
    Gets covid API data and formats it into a list.
    """
    # Uses the 5th item in the config file.
    with open('config.json', 'r') as f:
        json_file = json.load(f)
    f.close()
    area_type = json_file["location"]["covid"]["type"]
    # Uses the 6th item in the config file.
    area_name = json_file["location"]["covid"]["name"]
    #
    location_only = [
        'areaType=' + area_type,
        'areaName=' + area_name
    ]
    cases_and_deaths = {
        "date": "date",
        "areaName": "areaName",
        "areaCode": "areaCode",
        "newCasesBySpecimenDate": "newCasesBySpecimenDate",
        "cumCasesBySpecimenDate": "cumCasesBySpecimenDate",
        "newDeathsByDeathDate": "newDeathsByDeathDate",
        "cumDeathsByDeathDate": "cumDeathsByDeathDate",
        "cumDeaths28DaysByDeathDate": "cumDeaths28DaysByDeathDate"
    }
    api = Cov19API(filters=location_only, structure=cases_and_deaths)
    data = api.get_json()
    display = []
    display.append(Markup('<u>Covid stats for {a}:</u> '.format(a=area_name)))
    display.append("New cases = "
                   + str(data['data'][0]['newCasesBySpecimenDate']))
    display.append("Cumulative cases = "
                   + str(data['data'][0]['cumCasesBySpecimenDate']))
    display.append("New deaths = "
                   + str(data['data'][0]['newDeathsByDeathDate']))
    display.append("Cumulative deaths = "
                   + str(data['data'][0]['cumDeathsByDeathDate']))
    display.append("Cumulative deaths within 28 days = "
                   + str(data['data'][0]['cumDeaths28DaysByDeathDate']))
    return display


def nd_flag_manage():
    """
    Schedules flag that stops notifications from going off more than once.
    """
    global nd_flag
    nd_flag = 1
    s = sched.scheduler(time.time, time.sleep)
    s.enter(60, 0, flip_flag)
    s.run(blocking=False)
    logging.debug("Notifications can no longer appear\n")


def flip_flag():
    """
    Flips the flag that stops notifications from going off more than once.
    """
    global nd_flag
    nd_flag = 0
    logging.debug("Notifications can appear again\n")


def deletor(alarm_delete: str, notif_delete: str):
    """
    Checks if user wants anything deleted, if so, deletes chosen
    alarm/notification by name.

    Keyword arguments:
    alarm_delete -- the name of the alarm to be deleted
    notif_delete -- the name of the notification to be deleted
    """
    global alarms
    global notifications
    if alarm_delete:
        for alarm in alarms:
            if alarm_delete == alarm['title']:
                alarms.remove(alarm)
                # log
                aLog = "This alarm has been deleted: \n\n"
                aLog = aLog + "\tTitle = " + alarm['title'] + "\n"
                aLog = (aLog + "\tContent = " + alarm['content'] + "\n")
                logging.warning(aLog)
                #
                break
    elif notif_delete:
        for notification in notifications:
            if notif_delete == notification['title']:
                notifications.remove(notification)
                # log
                nLog = "This notification has been deleted: \n\n"
                nLog = nLog + "\tTitle = " + notification['title'] + "\n"
                nLog = (nLog + "\tContent = " + notification['content'] + "\n")
                logging.warning(nLog)
                #
                break


app = Flask(__name__)


@app.route('/')
def template():
    return (render_template('template.html', alarms=alarms,
            notifications=notifications, image="olaf.jpg",
            title=Markup(
             '<h style="font-size:32pt;color:#00ACDF;">The Alarming Alarm</h>'
            )))


@app.route('/index')
def index():
    global alarms
    global notifications
    alarm_time = request.args.get('alarm')
    alarm_name = request.args.get('two')
    news_flag = "not include news and"
    weather_flag = "not include weather"
    if request.args.get('news'):
        news_flag = "include news and"
    if request.args.get('weather'):
        weather_flag = "include weather"
    alarm_delete = request.args.get('alarm_item')
    notif_delete = request.args.get('notif')
    if alarm_delete or notif_delete:
        deletor(alarm_delete, notif_delete)
    alarm_management(alarm_time, alarm_name, news_flag, weather_flag)
    notification_management()
    template()
    announcement()
    # logging
    alarmLog = "Current Alarms are: \n"
    number = 0
    for alarm in alarms:
        alarmLog = alarmLog + "\n\tIndex " + str(number) + ":\n"
        alarmLog = alarmLog + "\tTitle = " + alarm['title'] + "\n"
        alarmLog = alarmLog + "\tContent = " + alarm['content'] + "\n"
        number += 1
    logging.info(alarmLog)
    notificationLog = "Current notifications are: \n"
    number = 0
    for notification in notifications:
        notificationLog = notificationLog + "\n\tIndex " + str(number) + ":\n"
        notificationLog = (notificationLog + "\tTitle = "
                           + notification['title'] + "\n")
        notificationLog = (notificationLog + "\tContent = "
                           + notification['content'] + "\n")
        number += 1
    logging.info(notificationLog)
    #
    return (render_template('template.html', alarms=alarms,
            notifications=notifications, image="olaf.jpg",
            title=Markup(
             '<h style="font-size:32pt;color:#00ACDF;">The Alarming Alarm</h>'
            )))


if __name__ == '__main__':
    app.run()
