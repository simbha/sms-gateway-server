# SMS Gateway Server

## Required Software
The SMS Gateway Server is written in Python, which is required for the application to run. Python 2.5 is the required version, which can be found at: http://www.python.org/download/releases/2.5/

## 3rd Party Modules
The SMS Gateway Server makes use of the following modules, they are also required for the application to run.

- [PyQt4](http://www.riverbankcomputing.co.uk/software/pyqt/download)
- [pyserial 2.5](http://sourceforge.net/projects/pyserial/files/)

## Usage
When you first run the SMS Gateway Server you will need to configure your COM port and HTTP port settings. You can do this using the settings dialog at `File` -> `Settings`. Once you have chosen your COM port and server port, start the HTTP server by choosing `Server` -> `Start Server`, and connect the COM port by choosing `COM Port` -> `Connect COM Port`.

When you close the application it will minimise to the system tray and run in the background. To end the application either select `File` -> `Exit` on the main window or right click the system tray icon (a yellow envelope) and click Exit. To restore to main application window when it is minimised right click the system tray icon and select Restore.

Once you have chosen your settings the application will remember them. When you start the application and it finds the saved settings it will automatically start the server and connect the COM port, then minimise the application to the system tray.

### Sending an SMS From the Provided Web Form
To send an SMS message using the web form provided by the server:

- Make sure the server is running and that the serial port is connected.
- Open a web browser at http://hostname:port/sms_sender.html, where hostname and port match your current settings. You can also choose `Server` -> `Launch Browser` from the main application window.
- Fill in the form and click the "Send Message(s)" button.

You can send a message to multiple recipients using the web form. Recipient addresses should be separated by a comma.

### Sending an SMS From a Script Or Application
Refer to the files in the "Usage Examples" folder to see how to send SMS
messages using a script or application.

## Troubleshooting
If you have everything set up, but text messages are not being sent, any of the following reasons could cause a problem:

- Connecting to the wrong serial port. The application will blindly write to the chosen serial port, even if it is not a GSM modem or phone.
- Your GSM modem or phone does not support the required AT commands for sending text messages: `AT+CMGF`, `AT+CSMP` & `AT+CMGS`. Refer to the documentation for your hardware to see if these commands are supported. You can also run the AT command `AT+CLAC` to see which AT commands are supported by your hardware.
- Your GSM modem or phone does not have credit to send messages. Try to send an SMS on the phone itself to see if this is the problem.

## Thanks
The icons used within the SMS Gateway Server were created by:
  * [famfamfam icons](http://www.famfamfam.com/)
  * [dryicons](http://dryicons.com/)
