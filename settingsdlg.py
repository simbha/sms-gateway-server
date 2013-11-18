"""
Module containing the application settings dialog class.
"""

# Standard library modules
import os
import platform

# 3rd party modules
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import serial

class SettingsDlg(QDialog):
    """
    Defines the GUI and behaviour of the application settings dialog.
    """
    def __init__(self, user_settings, locked_com=None, locked_http=None, parent=None):
        QDialog.__init__(self, parent)

        # Save the parameters as instance variables
        self.user_settings = user_settings
        self.locked_com = locked_com
        self.locked_http = locked_http

        # Set the window title
        self.setWindowTitle(self.tr('Settings'))

        # Create the GUI widgets
        self.com_port_cb = QComboBox()
        self.server_port_sb = QSpinBox()
        self.server_port_sb.setMinimum(1)
        self.server_port_sb.setMaximum(65536)
        self.server_port_sb.setSingleStep(1)
        self.refresh_btn = QPushButton(QIcon(':/images/action_refresh.gif'), '')
        self.refresh_btn.setMaximumWidth(30)
        self.connect(self.refresh_btn, SIGNAL('clicked()'), self.populate_com_ports)

        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel(self.tr('COM Port:')), 0, 0)
        grid_layout.addWidget(self.com_port_cb, 0, 1)
        grid_layout.addWidget(self.refresh_btn, 0, 2)
        grid_layout.addWidget(QLabel(self.tr('HTTP Server Port:')), 1, 0)
        grid_layout.addWidget(self.server_port_sb, 1, 1)

        self.duration_sb = QSpinBox()
        self.duration_sb.setMinimum(1)
        self.duration_sb.setMaximum(20)
        self.duration_sb.setSingleStep(1)
        self.duration_sb.setSuffix(self.tr(' s'))
        self.message_gb = QGroupBox(self.tr('Show system tray messages'))
        self.message_gb.setCheckable(True)
        self.message_gb.setChecked(False)
        message_box = QHBoxLayout()
        message_box.addWidget(QLabel(self.tr('Duration:')))
        message_box.addWidget(self.duration_sb)
        self.message_gb.setLayout(message_box)

        self.sms_log_txt = QLineEdit()
        self.sms_log_btn = QPushButton(QIcon(':/images/folder_page.gif'), '')
        self.sms_log_gb = QGroupBox(self.tr('Log sent SMS messages'))
        self.sms_log_gb.setCheckable(True)
        self.sms_log_gb.setChecked(False)
        sms_log_box = QHBoxLayout()
        sms_log_box.addWidget(QLabel(self.tr('Log File Name:')))
        sms_log_box.addWidget(self.sms_log_txt)
        sms_log_box.addWidget(self.sms_log_btn)
        self.sms_log_gb.setLayout(sms_log_box)
        self.connect(self.sms_log_btn, SIGNAL('clicked()'), self.get_sms_log_filename)

        self.http_log_txt = QLineEdit()
        self.http_log_btn = QPushButton(QIcon(':/images/folder_page.gif'), '')
        self.http_log_gb = QGroupBox(self.tr('Log sent SMS messages'))
        self.http_log_gb.setCheckable(True)
        self.http_log_gb.setChecked(False)
        http_log_box = QHBoxLayout()
        http_log_box.addWidget(QLabel(self.tr('Log File Name:')))
        http_log_box.addWidget(self.http_log_txt)
        http_log_box.addWidget(self.http_log_btn)
        self.http_log_gb.setLayout(http_log_box)
        self.connect(self.http_log_btn, SIGNAL('clicked()'), self.get_http_log_filename)

        # Create the "accept" and "cancel" dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok |
                                      QDialogButtonBox.Cancel)
        self.connect(button_box, SIGNAL('accepted()'), self, SLOT('accept()'))
        self.connect(button_box, SIGNAL('rejected()'), self, SLOT('reject()'))

        # Create main layout
        container = QVBoxLayout()
        container.addLayout(grid_layout)
        container.addWidget(self.message_gb)
        container.addWidget(self.sms_log_gb)
        container.addWidget(self.http_log_gb)
        container.addWidget(button_box)
        self.setLayout(container)

        # Populate the COM port dialog box with the current availble ports
        self.populate_com_ports()

        # Populate the form with the users settings
        self.load_user_settings()

    def populate_com_ports(self):
        self.com_port_cb.clear()

        if self.locked_com:
            self.com_port_cb.addItem(str(self.locked_com))
            self.com_port_cb.setDisabled(True)
            self.refresh_btn.setDisabled(True)
        else:

            # Define a flag to check if any COM ports are available
            port_found = False

            # Attempt to connect to all available COM ports to see which are
            # available and populate the COM port combo box.
            for i in range(256):
                try:
                    serial_conn = serial.Serial(i)
                except serial.SerialException:
                    pass
                else:
                    serial_conn.close()
                    self.com_port_cb.addItem('%d' % (i + 1))
                    port_found = True

            if not port_found:
                self.com_port_cb.addItem(self.tr('[No COM ports available]'))

            self.com_port_cb.setEnabled(True)
            self.refresh_btn.setEnabled(True)

    def load_user_settings(self):

        # Load the COM port combo box
        index = self.com_port_cb.findText(str(self.user_settings['com_port']))
        if index != -1:
            self.com_port_cb.setCurrentIndex(index)

        # Try to cast the server port to an integer
        server_port = int(self.user_settings['server_port'])

        # Check that the server port is within the correct range
        if not 1 <= server_port <= 65536:
            raise ValueError('Server port must be between 1 and 65535')
        else:
            if self.locked_http:
                self.server_port_sb.setValue(self.locked_http)
                self.server_port_sb.setDisabled(True)
            else:
                self.server_port_sb.setValue(server_port)
                self.server_port_sb.setEnabled(True)

        # Check that the "show_message" option is either True or False
        if isinstance(self.user_settings['show_message'], bool):
            self.message_gb.setChecked(self.user_settings['show_message'])
        else:
            raise ValueError('"show_message" option must be either True or False')

        # Check that the "message_duration" option is within the correct range
        if 1 <= self.user_settings['message_duration'] <= 20:
            self.duration_sb.setValue(self.user_settings['message_duration'])
        else:
            raise ValueError('"message_duration" option must be between 1 and 20')

        # Check that the "log_sms" option is either True or False
        if isinstance(self.user_settings['log_sms'], bool):
            self.sms_log_gb.setChecked(self.user_settings['log_sms'])
        else:
            raise ValueError('"log_sms" option must be either True or False')

        # Check that the "sms_log_file" is a string
        if isinstance(self.user_settings['sms_log_file'], basestring):
            self.sms_log_txt.setText(self.user_settings['sms_log_file'])
        else:
            raise ValueError('"sms_log_file" is not a string')

        # Check that the "log_http" option is either True or False
        if isinstance(self.user_settings['log_http'], bool):
            self.http_log_gb.setChecked(self.user_settings['log_http'])
        else:
            raise ValueError('"log_http" option must be either True or False')

        # Check that the "http_log_file" is a string
        if isinstance(self.user_settings['http_log_file'], basestring):
            self.http_log_txt.setText(self.user_settings['http_log_file'])
        else:
            raise ValueError('"http_log_file" is not a string')

    def get_sms_log_filename(self):
        location = QFileDialog.getSaveFileName(self,
                                               self.tr('Choose SMS Log Location'),
                                               self.sms_log_txt.text(),
                                               'Text File (*.txt)')
        if not location.isEmpty():
            if platform.system() == 'Windows':
                location = location.replace('/','\\')
            self.sms_log_txt.setText(location)

    def get_http_log_filename(self):
        location = QFileDialog.getSaveFileName(self,
                                               self.tr('Choose HTTP Log Location'),
                                               self.http_log_txt.text(),
                                               'Text File (*.txt)')
        if not location.isEmpty():
            if platform.system() == 'Windows':
                location = location.replace('/','\\')
            self.http_log_txt.setText(location)

    def accept(self):

        # Get the COM port number. If there are no free COM ports then
        # currentText() will return a string which will fail when converting to
        # an integer, in which case use None.
        try:
            com_port = int(self.com_port_cb.currentText())
        except ValueError:
            com_port = None

        if self.sms_log_gb.isChecked():

            # Check that the SMS log file path is not empty
            sms_log_file = str(self.sms_log_txt.text())
            if len(sms_log_file) == 0:
                QMessageBox.critical(self, self.tr('Error'), self.tr('Please enter a value for the SMS log file path.'), QMessageBox.Ok)
                self.sms_log_txt.setFocus()
                return

            # Check that the SMS log file path is valid
            sms_log_dir = os.path.dirname(str(self.sms_log_txt.text()))
            if not os.path.isdir(sms_log_dir):
                QMessageBox.critical(self, self.tr('Error'), self.tr('The SMS log file path is not valid.'), QMessageBox.Ok)
                self.sms_log_txt.setFocus()
                self.sms_log_txt.selectAll()
                return
        else:
            sms_log_file = self.user_settings['sms_log_file']

        if self.http_log_gb.isChecked():

            # Check that the HTTP log file path is not empty
            http_log_file = str(self.http_log_txt.text())
            if len(http_log_file) == 0:
                QMessageBox.critical(self, self.tr('Error'), self.tr('Please enter a value for the HTTP log file path.'), QMessageBox.Ok)
                self.http_log_txt.setFocus()
                return

            # Check that the HTTP log file path is valid
            http_log_dir = os.path.dirname(str(self.http_log_txt.text()))
            if not os.path.isdir(http_log_dir):
                QMessageBox.critical(self, self.tr('Error'), self.tr('The HTTP log file path is not valid.'), QMessageBox.Ok)
                self.http_log_txt.setFocus()
                self.http_log_txt.selectAll()
                return
        else:
            http_log_file = self.user_settings['http_log_file']

        # Put the users settings into a new instance variable
        self.updated_settings = {'com_port': com_port,
                                 'server_port': self.server_port_sb.value(),
                                 'show_message': self.message_gb.isChecked(),
                                 'message_duration': self.duration_sb.value(),
                                 'log_sms': self.sms_log_gb.isChecked(),
                                 'sms_log_file': sms_log_file,
                                 'log_http': self.http_log_gb.isChecked(),
                                 'http_log_file': http_log_file}
        QDialog.accept(self)
