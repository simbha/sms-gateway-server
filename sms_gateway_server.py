#!/usr/bin/env python

"""
Top level application file for the "SMS Gateway Server" application.
"""
__version__ = '1.1'
APP_NAME = 'SMS Gateway Server'
AUTHOR = 'Craig Dodd'
ORGANIZATION = 'Shelltoad Computing'
COPYRIGHT = 'GNU General Public License v3'

# Try to import required modules
try:
    # Standard library modules
    import sys
    import threading
    import webbrowser

    # 3rd party modules
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    import serial

    # Local application modules
    import httpserver
    import resources
    import settingsdlg
    import threads
    import time
    import util

# Display a Tkinter messagebox if a module failed to import (assumes that the
# Tkinter modules are available, which they should be)
except ImportError, e:
    import Tkinter, tkMessageBox
    root = Tkinter.Tk()
    root.withdraw()

    # Get the name of the module that could not be imported and display an
    # error dialog.
    module_name = e.message.split()[-1]
    tkMessageBox.showerror('Error: Module Not Found',
                           'The module "%s" is not installed. This is required for the %s to run.' % (module_name, APP_NAME))
    sys.exit(1)

class MainWindow(QMainWindow):
    """
    This class defines the GUI and behaviour of the main application window.
    """
    def __init__(self, parent=None):
        """
        Create the layout of the form and register widgets with their
        associated methods.
        """
        QMainWindow.__init__(self, parent)

        # Setup the window settings
        self.setWindowTitle(self.tr(APP_NAME))
        self.setMinimumSize(600, 400)

        # Create the COM port & server status labels
        self.server_status_lbl = QLabel(self.tr('<font size="+1" color="grey">Not running</font>'))
        self.com_status_lbl = QLabel(self.tr('<font size="+1" color="grey">Not connected</font>'))
        status_layout = QGridLayout()
        status_layout.addWidget(QLabel(self.tr('<font size="+1">HTTP Server:</font>')), 0, 0)
        status_layout.addWidget(self.server_status_lbl, 0, 1)
        status_layout.addWidget(QLabel(self.tr('<font size="+1">COM Port:</font>')), 1, 0)
        status_layout.addWidget(self.com_status_lbl, 1, 1)
        status_container = QHBoxLayout()
        status_container.addLayout(status_layout)
        status_container.addStretch()

        # Create the main tab widgets
        self.activity_log_lst = QListWidget()
        self.sent_message_lst = QListWidget()
        self.message_queue_lst = QListWidget()
        self.http_log_lst = QListWidget()

        # Add the listboxes as tabs
        tabs = QTabWidget()
        tabs.addTab(self.activity_log_lst, self.tr('Activity Log'))
        tabs.addTab(self.sent_message_lst, self.tr('Sent Messages'))
        tabs.addTab(self.message_queue_lst, self.tr('Queued Messages'))
        tabs.addTab(self.http_log_lst, self.tr('HTTP Log'))

        # Create the main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(status_container)
        main_layout.addWidget(tabs)
        w = QWidget()
        w.setLayout(main_layout)
        self.setCentralWidget(w)

        # Create actions
        file_exit_action = QAction('Exit', self)
        file_exit_action.setToolTip('Exit the Application')
        file_exit_action.setIcon(QIcon(':/images/door_open.png'))
        self.connect(file_exit_action, SIGNAL('triggered()'), self.manual_close)

        self.start_server_action = QAction('Start Server', self)
        self.start_server_action.setToolTip('Start Server')
        self.start_server_action.setIcon(QIcon(':/images/action_go.gif'))
        self.connect(self.start_server_action, SIGNAL('triggered()'), self.start_server)

        self.stop_server_action = QAction('Stop Server', self)
        self.stop_server_action.setToolTip('Stop Server')
        self.stop_server_action.setIcon(QIcon(':/images/action_stop.gif'))
        self.stop_server_action.setDisabled(True)
        self.connect(self.stop_server_action, SIGNAL('triggered()'), self.stop_server)

        self.launch_browser_action = QAction('Launch Browser', self)
        self.launch_browser_action.setToolTip('Launch Browser')
        self.launch_browser_action.setIcon(QIcon(':/images/page_url.gif'))
        self.launch_browser_action.setDisabled(True)
        self.connect(self.launch_browser_action, SIGNAL('triggered()'), self.launch_browser)

        self.connect_com_action = QAction('Connect COM Port', self)
        self.connect_com_action.setToolTip('Connect COM Port')
        self.connect_com_action.setIcon(QIcon(':/images/connect.png'))
        self.connect(self.connect_com_action, SIGNAL('triggered()'), self.connect_com_port)

        self.disconnect_com_action = QAction('Disconnect COM Port', self)
        self.disconnect_com_action.setToolTip('Disconnect COM Port')
        self.disconnect_com_action.setIcon(QIcon(':/images/disconnect.png'))
        self.disconnect_com_action.setDisabled(True)
        self.connect(self.disconnect_com_action, SIGNAL('triggered()'), self.disconnect_com_port)

        about_action = QAction('About', self)
        about_action.setToolTip('About')
        about_action.setIcon(QIcon(':/images/icon_info.gif'))
        self.connect(about_action, SIGNAL('triggered()'), self.show_about)

        self.restore_action = QAction('Restore', self)
        self.restore_action.setToolTip('Restore')
        self.restore_action.setIcon(QIcon(':/images/application.png'))
        self.restore_action.setVisible(False)
        self.connect(self.restore_action, SIGNAL('triggered()'), self.restore_window)

        self.edit_settings_action = QAction('Settings', self)
        self.edit_settings_action.setToolTip('Settings')
        self.edit_settings_action.setIcon(QIcon(':/images/icon_settings.gif'))
        self.connect(self.edit_settings_action, SIGNAL('triggered()'), self.edit_settings)

        # Create the tool bar
        tool_bar = QToolBar()
        tool_bar.setFloatable(False)
        tool_bar.setMovable(False)
        tool_bar.addAction(self.edit_settings_action)
        tool_bar.addSeparator()
        tool_bar.addAction(self.start_server_action)
        tool_bar.addAction(self.stop_server_action)
        tool_bar.addAction(self.launch_browser_action)
        tool_bar.addSeparator()
        tool_bar.addAction(self.connect_com_action)
        tool_bar.addAction(self.disconnect_com_action)
        self.addToolBar(tool_bar)

        # Create the menubar
        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction(self.edit_settings_action)
        file_menu.addAction(file_exit_action)

        server_menu = self.menuBar().addMenu('&Server')
        server_menu.addAction(self.start_server_action)
        server_menu.addAction(self.stop_server_action)
        server_menu.addAction(self.launch_browser_action)

        com_port_menu = self.menuBar().addMenu('&COM Port')
        com_port_menu.addAction(self.connect_com_action)
        com_port_menu.addAction(self.disconnect_com_action)

        help_menu = self.menuBar().addMenu('&Help')
        help_menu.addAction(about_action)

        # Create the system tray icon menu
        tray_icon_menu = QMenu(self)
        tray_icon_menu.addAction(self.start_server_action)
        tray_icon_menu.addAction(self.stop_server_action)
        tray_icon_menu.addAction(self.launch_browser_action)
        tray_icon_menu.addSeparator()
        tray_icon_menu.addAction(self.connect_com_action)
        tray_icon_menu.addAction(self.disconnect_com_action)
        tray_icon_menu.addSeparator()
        tray_icon_menu.addAction(self.edit_settings_action)
        tray_icon_menu.addSeparator()
        tray_icon_menu.addAction(self.restore_action)
        tray_icon_menu.addAction(file_exit_action)

        # Create the system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(':/images/mail.png'))
        self.tray_icon.setContextMenu(tray_icon_menu)
        self.tray_icon.setToolTip(self.tr(APP_NAME))
        self.tray_icon.show()

        self.log_activity('Application started')

        # Load saved settings
        self.load_settings()

        # Create a queue to store SMS messages
        self.msg_queue = util.CustomQueue()

        # Create a serial object & a mutex to access it
        self.serial_conn = serial.Serial()
        self.serial_conn_mutex = threading.Lock()

        # Connect the COM port & server if necessary
        if self.auto_com_connect:
            self.connect_com_port(silent_fail=False)
        if self.auto_server:
            self.start_server()

        # Create a mutex for accessing log files. A user could potentially use
        # the same filename for the SMS and HTTP logs. A mutex makes sure
        # there are no access conflicts.
        self.log_file_lock = threading.Lock()

        # Store the Qt system tray icons in the class instance for external
        # access by other modules (so they don't need to import the Qt modules)
        self.tray_icon_critical = QSystemTrayIcon.MessageIcon(QSystemTrayIcon.Critical)
        self.tray_icon_information = QSystemTrayIcon.MessageIcon(QSystemTrayIcon.Information)

    def launch_browser(self):
        if self.settings['server_port'] == 80:
            address = 'http://localhost/sms_sender.html'
        else:
            address = 'http://localhost:%d/sms_sender.html' % self.settings['server_port']

        webbrowser.open(address)

    def connect_com_port(self, silent_fail=False):
        """
        Connects to the COM port chosen in the settings dialog.
        """

        # Check if a COM port has been defined
        if self.settings['com_port'] is None:

            # Display a message box if necessary & return
            if not silent_fail:
                QMessageBox.critical(self, 'SMS Gateway Server - Error', 'No COM port selected. Please choose a COM port in the settings menu.', QMessageBox.Ok)
            return

        # Set the serial port in the serial object
        self.serial_conn.port = 'COM%s' % self.settings['com_port']

        try:

            # Attempt to connect to the selected COM port
            self.serial_conn.open()
        except serial.SerialException:

            # Display a failure message box if necessary
            if not silent_fail:
                QMessageBox.critical(self,
                                     self.tr('SMS Gateway Server - Error'),
                                     self.tr('Could not connect to COM port (COM%s). Please check the COM port settings.' % self.settings['com_port']),
                                     QMessageBox.Ok)

            # Update the GUI
            self.connect_com_action.setEnabled(True)
            self.disconnect_com_action.setDisabled(True)
            self.com_status_lbl.setText(self.tr('<font size="+1" color="grey">Not connected</font>'))
        else:

            # Create & start a thread to process the message queue
            self.sender_thread = threads.MsgSender(self.msg_queue,
                                                   self.serial_conn,
                                                   self.serial_conn_mutex,
                                                   self.message_sent)
            self.connect(self.sender_thread, SIGNAL('threadExit()'), self.com_disconnected)
            self.sender_thread.start()

            # Create & start a thread to monitor the connection status
            self.com_checker = threads.COMChecker(self)
            self.com_checker.start()

            # Update the GUI
            self.connect_com_action.setDisabled(True)
            self.disconnect_com_action.setEnabled(True)
            self.com_status_lbl.setText(self.tr('<font size="+1" color="green"><b>Connected (COM%d)</b></font>' % self.settings['com_port']))
            self.log_activity('COM port connected (COM%d)' % self.settings['com_port'])

    def disconnect_com_port(self, block=False):

        # Update the GUI
        self.disconnect_com_action.setDisabled(True)

        # Stop the thread that monitors the COM port connection.
        try:
            if self.com_checker.isRunning():
                self.com_checker.stop()
                if block:
                    self.com_checker.wait()
        except AttributeError:
            pass

        # Stop the sender thread (this will also close the COM port connection
        # if it is currently open)
        try:
            if self.sender_thread.isRunning():
                self.sender_thread.stop()
                if block:
                    self.sender_thread.wait()
        except AttributeError:
            pass

    def com_disconnected(self):
        """
        When the SMS sender thread terminates (and the COM port is
        disconnected) this method is called.
        """
        self.connect_com_action.setEnabled(True)
        self.com_status_lbl.setText(self.tr('<font size="+1" color="grey">Not connected</font>'))

        try:
            if not self.sender_thread.conn_error:
                self.log_activity('COM port disconnected')
        except AttributeError:
            pass

    def log_activity(self, message, error=False):
        timestamp = time.strftime('%d/%m/%y %H:%M:%S')
        list_item = QListWidgetItem('%s: %s' % (timestamp, message))
        if error:
            list_item.setTextColor(QColor(Qt.red))
            font = QFont()
            font.setWeight(QFont.Bold)
            list_item.setFont(font)
        self.activity_log_lst.addItem(list_item)
        self.activity_log_lst.setCurrentItem(list_item)

    def load_settings(self):
        self.settings = {}
        saved_settings = QSettings()

        # Get the COM port setting
        com_port = saved_settings.value('com_port')
        if com_port.isNull():
            self.settings['com_port'] = None
            self.auto_com_connect = False
        else:
            self.settings['com_port'] = com_port.toInt()[0]
            self.auto_com_connect = True

        # Get the server port setting
        server_port = saved_settings.value('server_port')
        if server_port.isNull():
            self.settings['server_port'] = 80
            self.auto_server = False
        else:
            self.settings['server_port'] = server_port.toInt()[0]
            self.auto_server = True

        # Get the "show message" setting
        show_message = saved_settings.value('show_message')
        if show_message.isNull():
            self.settings['show_message'] = False
        else:
            self.settings['show_message'] = show_message.toBool()

        # Get the "message duration" setting
        message_duration = saved_settings.value('message_duration')
        if message_duration.isNull():
            self.settings['message_duration'] = 5
        else:
            self.settings['message_duration'] = message_duration.toInt()[0]

        # Get the "Log SMS" setting
        log_sms = saved_settings.value('log_sms')
        if log_sms.isNull():
            self.settings['log_sms'] = False
        else:
            self.settings['log_sms'] = log_sms.toBool()

        # Get the "Log SMS File" setting
        sms_log_file = saved_settings.value('sms_log_file')
        if sms_log_file.isNull():
            self.settings['sms_log_file'] = ''
        else:
            self.settings['sms_log_file'] = str(sms_log_file.toString())

        # Get the "Log HTTP" setting
        log_http = saved_settings.value('log_http')
        if log_http.isNull():
            self.settings['log_http'] = False
        else:
            self.settings['log_http'] = log_http.toBool()

        # Get the "Log HTTP File" setting
        http_log_file = saved_settings.value('http_log_file')
        if http_log_file.isNull():
            self.settings['http_log_file'] = ''
        else:
            self.settings['http_log_file'] = str(http_log_file.toString())

    def edit_settings(self):

        # Detect if the HTTP server is running and if so get the port number
        try:
            serv_port = self.settings['server_port'] if self.server_thread.isRunning() else None
        except AttributeError:
            serv_port = None

        # Detect if the COM port is connected and if so get the port number
        try:
            com_port = self.settings['com_port'] if self.sender_thread.isRunning() else None
        except AttributeError:
            com_port = None

        settings_dlg = settingsdlg.SettingsDlg(self.settings,
                                               locked_http=serv_port,
                                               locked_com=com_port,
                                               parent=self)
        if settings_dlg.exec_():

            # Get the updated settings from the dialog window
            self.settings = settings_dlg.updated_settings

            # Save the settings using a QSettings object
            saved_settings = QSettings()
            saved_settings.setValue('com_port', QVariant(self.settings['com_port']))
            saved_settings.setValue('server_port', QVariant(self.settings['server_port']))
            saved_settings.setValue('show_message', QVariant(self.settings['show_message']))
            saved_settings.setValue('message_duration', QVariant(self.settings['message_duration']))
            saved_settings.setValue('log_sms', QVariant(self.settings['log_sms']))
            saved_settings.setValue('sms_log_file', QVariant(self.settings['sms_log_file']))
            saved_settings.setValue('log_http', QVariant(self.settings['log_http']))
            saved_settings.setValue('http_log_file', QVariant(self.settings['http_log_file']))

        # For some reason if the main window is not currently visible (i.e. the
        # program is running from the system tray) the program will crash when
        # the settings dialog is closed (it is initially launched from the
        # system tray context menu). To hack around this the form is displayed
        # then hidden again.
        if not self.isVisible():
            self.setVisible(True)
            self.setVisible(False)

    def closeEvent(self, event):
        """
        Overrides the application close event to minimise the application to
        the system tray instead of exiting.
        """

        # Hide the main window form
        self.hide()

        # Make the "Restore" option available in the system tray
        self.restore_action.setVisible(True)

        # Ignore the close event action so that the application stays running.
        event.ignore()

    def restore_window(self):
        """
        Restores the main window from running in the system tray.
        """

        # Hide the "Restore" option in the system tray
        self.restore_action.setVisible(False)

        # Restore the main window
        self.showNormal()

    def manual_close(self):
        """
        Exits the application.
        """

        # Hide the window
        self.hide()

        # The system tray icon doesn't always disappear automatically so hide
        # it manually before exit.
        self.tray_icon.setVisible(False)

        # Stop the HTTP server & disconnect the COM port
        self.stop_server(block=True)
        self.disconnect_com_port(block=True)

        # Exit the application
        QApplication.exit()

    def start_server(self):
        """
        Creates a new server thread & starts it.
        """

        # Create & start the HTTP server
        self.server_thread = threads.MsgReceiver(self.log_http_data, self.message_received, self.settings['server_port'])
        self.connect(self.server_thread, SIGNAL('threadExit()'), self.server_stopped)
        self.server_thread.start()

        # Update the GUI
        self.start_server_action.setDisabled(True)
        self.stop_server_action.setEnabled(True)
        self.launch_browser_action.setEnabled(True)
        self.server_status_lbl.setText(self.tr('<font size="+1" color="green"><b>Running (Port %d)</b></font>' % self.settings['server_port']))
        self.log_activity('Server started on port %d' % self.settings['server_port'])

    def stop_server(self, block=False):
        """
        Signals to the server thread to stop then blocks until it has finished.
        """

        # Update the GUI
        self.stop_server_action.setDisabled(True)
        self.launch_browser_action.setDisabled(True)

        # Stop the server if it is currently running
        try:
            if self.server_thread.isRunning():
                self.server_thread.stop()
                if block:
                    self.server_thread.wait()
        except AttributeError:
            pass

    def server_stopped(self):
        """
        This method is called when the server thread terminates.
        """
        self.start_server_action.setEnabled(True)
        self.server_status_lbl.setText(self.tr('<font size="+1" color="grey">Not running</font>'))
        self.log_activity('Server stopped')

    def message_sent(self, message_data):

        # Get the message data & remove the line breaks
        message_text = message_data['message']
        message_text = message_text.replace('\r\n', ' ')
        message_text = message_text.replace('\n', ' ')

        # Make a truncated version for GUI display
        truncated_text = message_text[:57] + '...' if len(message_text) > 60 else message_text

        # Update the SMS log list box
        list_item = QListWidgetItem('%s - %s - %s - C%d: %s' % (message_data['timestamp'],
                                                               message_data['sender_ip'],
                                                               message_data['recipient'],
                                                               message_data['class'],
                                                               truncated_text))
        self.sent_message_lst.addItem(list_item)
        self.sent_message_lst.setCurrentItem(list_item)

        # Remove the message from the queue list box
        row = self.message_queue_lst.row(message_data['widget'])
        self.message_queue_lst.takeItem(row)

        # Write to the log text file
        if self.settings['log_sms']:
            self.log_file_lock.acquire()
            try:
                open(self.settings['sms_log_file'], 'a').write('%s - %s - %s - C%d: %s\n' % (message_data['timestamp'],
                                                                                             message_data['sender_ip'],
                                                                                             message_data['recipient'],
                                                                                             message_data['class'],
                                                                                             message_text))
            except IOError:
                self.log_activity('Error when writing to the SMS log file.', error=True)
            finally:
                self.log_file_lock.release()

        # Display a tray icon message if necessary
        if self.settings['show_message']:
            self.tray_icon.showMessage(self.tr('SMS Message Sent'),
                                       self.tr('To: %s\n%s' % (message_data['recipient'], truncated_text)),
                                       self.tray_icon_information,
                                       self.settings['message_duration'] * 1000)

    def message_received(self, message_data):

        # Get the message data & remove the line breaks
        message_text = message_data['message']
        message_text = message_text.replace('\r\n', ' ')
        message_text = message_text.replace('\n', ' ')

        # Make a truncated version for GUI display
        truncated_text = message_text[:47] + '...' if len(message_text) > 50 else message_text

        # Create a list widget
        message_data['widget'] = QListWidgetItem('%s - %s - %s - C%d: %s' % (message_data['timestamp'],
                                                                             message_data['sender_ip'],
                                                                             message_data['recipient'],
                                                                             message_data['class'],
                                                                             truncated_text))

        # Add the message widget to the GUI queue list box
        self.message_queue_lst.addItem(message_data['widget'])

        # Add the message to the queue to be sent
        self.msg_queue.put(message_data)

    def log_http_data(self, log_text):
        """
        This function is called by the HTTP server when a HTTP request is
        received. A string is provided with log information which is used to
        update the GUI and is written to a file if necessary.
        """

        # Update the HTTP log listbox
        list_item = QListWidgetItem(log_text)
        self.http_log_lst.addItem(list_item)
        self.http_log_lst.setCurrentItem(list_item)

        # Write to the HTTP log text file
        if self.settings['log_http']:
            self.log_file_lock.acquire()
            try:
                open(self.settings['http_log_file'], 'a').write(log_text + '\n')
            except IOError:
                self.log_activity('Error when writing to the HTTP log file.', error=True)
            finally:
                self.log_file_lock.release()

    def show_about(self):
        """
        Display the "about" dialog box.
        """
        message = '''<font size="+2">%s</font> v%s
                     <p>Web based SMS gateway server.
                     <p>Written by %s
                     <br>&copy; %s
                     <p>Icons by <a href="http://www.famfamfam.com/">famfamfam</a> and
                     <a href="http://dryicons.com/">dryicons</a>.''' % (APP_NAME,
                                                                        __version__,
                                                                        AUTHOR,
                                                                        COPYRIGHT)

        QMessageBox.about(self, 'About ' + APP_NAME, message)

if __name__ == '__main__':

    # Create a QApplication instance
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/images/mail.png'))
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION)

    # Create an instance of the main window
    form = MainWindow()

    # Start the application in the system tray if necessary
    if form.auto_com_connect and form.auto_server:
        form.restore_action.setVisible(True)
    else:
        form.show()

    # Start the main event loop
    sys.exit(app.exec_())
