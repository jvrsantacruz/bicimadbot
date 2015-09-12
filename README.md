# BiciMadBot

Telegram chat Bot for BiciMad information

The [@BiciMadBot](https://telegram.me/bicimadbot) Telgram contact will help you find a bike, a
station or a free parking around Madrid. You can send messages to the bot using several commands
and search for stations using their id, name or address. Or even better, share your position with
the Bot and will search for the closest stations around you.

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

*About info*: The information offered by this service is **not official** in any way and should not
be regarded as such. Replies are based on the same data used by the BiciMad official phone
application. Any issues regarding the number free parkings, available bikes or stations are thus
non related to this software.

*About reliability*: The BiciMad company **does not** offer real-time data accessible through an
API for developers to build their tools on it. This is a very simple hack, but a hack still. As the
source of this data is subject to arbitrary changes in availability, shape or authentication
requirements at any time, the Bot can break or misbehave without previous notice for an undefined
amount of time. This sucks, I know.
