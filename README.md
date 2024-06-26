for linux to auto start FanArduinoControllerLinux.py:
Run it as a service.

Create /etc/systemd/system/FanArduinoControllerLinux.service:



[Unit]
Description=Start running FanArduinoControllerLinux.py script for my laptop docking station automatically
After=network.target

[Service]
ExecStartPre=/bin/sleep 60
ExecStart=/usr/bin/python3 /home/yoni/LibreHardwareMonitor/FanArduinoControllerLinux.py
Restart=always
User=yoni

[Install]
WantedBy=multi-user.target




Here's what each part does:

    [Unit]: The Description field gives a brief description of the service. The After=network.target ensures that the service starts after the network is available.
    [Service]: The ExecStart field specifies the command to start your script. The Restart=always ensures that the service restarts automatically if it crashes. The User=yourusername ensures that the script runs under a specific user account.
    [Install]: The WantedBy=multi-user.target ensures that the service starts in the appropriate runlevel for multi-user (non-graphical) environments.


then run the commands:
sudo systemctl daemon-reload
sudo systemctl start FanArduinoControllerLinux
sudo systemctl status FanArduinoControllerLinux

the last command check the status, see if its active. if it is its good!