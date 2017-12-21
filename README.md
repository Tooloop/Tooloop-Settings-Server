# Tooloop Settings Server

![](https://img.shields.io/badge/status-pre--release-red.svg)
![](https://img.shields.io/github/license/vollstock/tooloop-settings-server.svg)

A browser based settings app for [Tooloop OS](https://github.com/vollstock/tooloop-os). It’s using the [Flask framework](http://flask.pocoo.org/).

It's by no means ready for public use!


# Install

Clone the repository to `/opt/tooloop/settings-server`

    git clone https://github.com/vollstock/Tooloop-Settings-Server.git /opt/tooloop/settings-server

Install dependencies

    sudo bash /opt/tooloop/settings-server/install-dependencies.sh

Install systemd service

    sudo nano /etc/systemd/system/tooloop-settings-server.service

    [Unit]
    Description=Tooloop settings server
    
    [Service]
    Environment=DISPLAY=:0
    Environment=XAUTHORITY=/home/tooloop/.Xauthority
    ExecStart=/usr/bin/python /opt/tooloop/settings-server/tooloop-settings-server.py
    Restart=always
    
    [Install]
    WantedBy=graphical.target

Enable and start the service

    sudo systemctl enable tooloop-settings-server.service
    sudo systemctl start tooloop-settings-server.service



# Run debug

    sudo systemctl stop tooloop-settings-server.service && sudo python /opt/tooloop/settings-server/tooloop-settings-server.py


# Credits

**Flask (dynamically linked)**
The Tooloop Settings Server is based on the [Flask framework](http://flask.pocoo.org) which is licensed under a three clause BSD License. Read about the [Flask license](http://flask.pocoo.org/docs/0.12/license/).

**Python Augeas (dynamically linked)**
[GNU Lesser General Public License v2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)

**Python Crontab (dynamically linked)**
[GNU Lesser General Public License v3](http://www.gnu.org/licenses/lgpl-3.0)

**JQuery**
[MIT license](http://www.opensource.org/licenses/mit-license.php)

**Flot**
http://www.flotcharts.org/
[MIT license](http://www.opensource.org/licenses/mit-license.php)

**FastClick**
[MIT license](http://www.opensource.org/licenses/mit-license.php)
Copyright: The Financial Times Limited [All Rights Reserved]

**JQuery Mask**
https://igorescobar.github.io/jQuery-Mask-Plugin/
[MIT license](http://www.opensource.org/licenses/mit-license.php)


