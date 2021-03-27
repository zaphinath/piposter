export DISPLAY=':0'



---------Disable screen dark


If you want to disable the blank screen at every startup, just update the /etc/lightdm/lightdm.conf file and add in the [SeatDefaults] section the following command:

[SeatDefaults]
xserver-command=X -s 0 -dpms


---------Hide display bar


Edit the file /etc/xdg/lxsession/LXDE-pi/autostart

comment out the line @lxpanel --profile LXDE-pi with # symbol

--------
https://img.cloudygif.com/full/fd19a6fd81a7cd0d.gif //Pirates Carabean GIF