# ECM1400 CA3 : Alarming Alarm

Hello there, this is my Continuous Assessment 3 project for the ECM1400 Programming Module at Exeter University.

This project is for setting text-to-speech alarms for Covid-19, News, and Weather Briefings as well as getting automatic hourly text notifications on the same topic.
## **Requirements:**
Firstly, this was made on a Windows10 machine using the Google Chrome browser. All information henceforth is based on this, I am unaware if anything differs for usage on macOS etc.

For this program you will need:

    Python version > 3.8

    A web browser (preferably Chrome)

The following python packages/modules will be needed:

    Python package flask

    Python module pyttsx3

    Python module sched (standard library)

    Python module time (standard library)

    Python module requests

    Python module json (standard library)

    Python module logging (standard library)

    Python package uk_covid19

Also, make sure that the current working directory is that of where the project is (or equivalent) so that the program can find the system_log and config files.
### Installing:
To install these packages and modules, in the command prompt enter the following:

    pip install Flask

    pip install pyttsx3==2.7.1

    pip install requests

    pip install uk_covid19

## Testing:
There is some limited unit testing of some functions from the main program (including on the API calls to see if they get anything returned, you cannot be specific as the return value would always be different) in the 'test_AlarmingAlarms.py' file.

To check these for your self you must have pytest installed `pip install pytest` then enter `python -m pytest` into the command prompt in the directory that includes the test file.
## **Deployment:**
After running the code in 'AlarmingAlarm.py' you will need to go to <http://127.0.0.1:5000/> in your browser (preferably chrome).
For the best experience, if you have many alarms that will go off within a few minutes of each other, try to refrain from adding another alarm until the announcement has ended. Furthermore, I don't think it would be an issue but not using any kind punctuation for the alarm label would make the program more stabile.
### Configuration File:
There is a file 'config.json' that contains some information that can be edited.

There is no need to change API key as mine should work, however if you like you can use your own.

For 'location' 'news' you should only put in the 2-letter ISO 3166-1 code of the country you want to get the top headlines for. Possible options:
```
ae ar at au be bg br ca ch cn co cu cz de eg fr gb gr hk hu id ie il in it jp kr lt lv ma mx my ng nl no nz ph pl pt ro rs ru sa se sg si sk th tr tw ua us ve za
```

For 'location' 'news' there is a large number of possible options. All of which is a location named followed by a comma then the 2-letter ISO 3166-1 code of the country the location is in (uk=gb). Not all locations will be recognised. Some example include:
```
Oranjestad,aw ; New York,us ; Manama,bh ; Exeter,uk ; London,gb
```

For 'location' 'covid' a small number of 'type' options and a large number of 'name' possibilities that have to work together. For example the 'type' options are:
```
overview = Overview data for the United Kingdom
nation = Nation data (England, Northern Ireland, Scotland, and Wales)
region = Region data
nhsRegion = NHS Region data
utla = Upper-tier local authority data
ltla = Lower-tier local authority data
```
While the 'name' possibilities are the name of an area which corresponds to the correct type. E.g.:
```
ltla, Exeter ; utla, Devon ; nhsRegion, London ; region, South West ; nation, England
```

For 'notif-minute' you just put a two digit number representing the minute you want the notification to go off every hour ("00" - "59"). The recommended time is "00".
### Logging:
There is a file 'system_log.log' which logs alarms/notifications placed, announced, and deleted as well as any Input Errors.
If you want the file cleared it will have to be done manually.
## **Extra Info:**
### Author:
+ Frederic Pecorini-White

### License:
```
    MIT License

    Copyright (c) 2020 Frederic Alexander Pecorini-White

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
```
