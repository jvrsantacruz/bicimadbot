4.5.0  2015-09-07
-----------------

* Adds --verbose flag to telegram cli
* Adds bot responses as telegram replies

4.4.0  2015-09-06
-----------------

* Adds update class to simplify message processing

4.3.0  2015-09-06
-----------------

* Adds separation for available and unavailable stations in location message
* Improves location message by removing emojis

4.2.4  2015-09-06
-----------------

* Adds upversion script
* Fixes bike emoji

4.2.3  2015-09-06
-----------------

* Adds emoji to location message
* Improves location message for better displaying

4.2.2  2015-09-05
-----------------

* Improves location message for better displaying

4.2.1  2015-09-05
-----------------

* Fixes distance in location message

4.2.0  2015-09-04
-----------------

* Adds free spaces and distance to location message

4.1.3 (2015-09-03)
------------------

* Fixes address to avoid showing NO OPERATIVA as address when unavailable

4.1.2 (2015-09-03)
------------------

* Fixes /plaza output that says empty station when its full

4.1.1 (2015-09-03)
------------------

* Fixes /plaza search results
* Fixes bad /bici /plaza message

4.1.0  2015-09-02
-----------------

* Adds disabled or empty stations to search results

4.0.1  2015-08-31
-----------------
* Fixes /plaza output which shows available bicis instead of free spaces

4.0.0  2015-08-31
-----------------
* Adds /plaza command

3.2.0  2015-08-31
-----------------
* Adds indexation of name and address for /bici search command

3.1.1  2015-08-31
-----------------
* Fixes help message

3.1.0  2015-08-31
-----------------
* Adds /help command

2.1.0  2015-08-31
-----------------
* Adds searching stations by id with /bici ID

2.0.0  2015-08-31
-----------------
* Adds /bici command implementation

1.1.0  2015-08-31
-----------------

* Adds --config and --timeout options for telegram commands in cli
* Adds 'real time' update processing via long polling
* Fixes development dependences

1.0.2  2015-08-31
-----------------
* Fixes command parsing error

1.0.1  2015-08-31
-----------------
* Adds /start command response
* Fixes unicode python3 error
* Adds python build directories to .gitignore
* Adds build/deploy makefile

1.0.0  2015-08-31
-----------------

Initial version
