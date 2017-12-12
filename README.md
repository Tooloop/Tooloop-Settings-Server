# Tooloop Settings Server

![](https://img.shields.io/badge/status-pre--release-red.svg)
![](https://img.shields.io/badge/license-Beer--Ware-blue.svg)

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
