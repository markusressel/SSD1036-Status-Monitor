# SSD1036-Status-Monitor
A small python script that renders system and service status to a SSD1036 screen.

# Content
At the top the current uptime of the system is shown

Below that a row of services is shown that indicates the current status of a systemd service:
* If the service is up and running nothing will be shown
* If the service is stopped a rectangle with the short name will be shown
* If the service has failed to run two rectangles will be shown

At the bottom a CPU meter with a single bar for each CPU core is shown.
