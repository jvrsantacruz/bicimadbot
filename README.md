# BiciMadBot

Telegram chat Bot for BiciMad information

The [@BiciMadBot](https://telegram.me/bicimadbot) Telgram contact will help you find a bike, a
station or a free parking around Madrid. You can send messages to the bot using several commands
and search for stations using their id, name or address. Or even better, share your position with
the Bot and will search for the closest stations around you.

![Telegram conversation with @BiciMadBot](https://raw.github.com/jvrsantacruz/bicimadbot/master/bicimad_screenshot.jpg)

## Talk to the bot

Any user cand chat with the Bot and query info about the state of the service in several ways.

1. Share your location
   When you share your location with the Bot, it will automatically search for the closest active
   stations and will answer with information about how many bikes and free parkings are.

2. Send a command
   If you want to search for a specific station or don't want to share your location, use one of
   the following commands that will search for a station using its text.

   Accepted commands are:

   * `/bici` will search for bikes in the stations that matches the search terms. 
     eg: ```/bici matadero```
   * `/plaza` will search for free parkings in stations matching the search.
     eg: ```/plaza sol```
   * `/estacion` will search for all stations by id, name or position.
     eg: ```/estacion lavapies```

## Collaborate

If you have some new ideas about new functionality that you think the bot may include or the Bot
breaks or says something weird, feel free to open a Issue on Github.

Pull requests are welcome!

## Development

Install the application in development mode and run the tests:

```
pip install -e .
pip install tox
tox
```

The python version used for this bot is `Python 3.4`.

## Disclaimers

*About the info*: The information offered by this service is **not official** in any way and should
not be regarded as such. Replies are based on the same data used by the BiciMad official phone
application. Any issues regarding the number free parkings, available bikes or stations are thus
non related to this software.

*About reliability*: The BiciMad company **does not** offer real-time data accessible through an
API for developers to build their tools on it. This is a very simple hack, but a hack still. As the
source of this data is subject to arbitrary changes in availability, shape or authentication
requirements at any time, the Bot can break or misbehave without previous notice for an undefined
amount of time. This sucks, I know.
