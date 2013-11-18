"""
Module containing classes that run in separate threads.
"""

# Standard library modules
import Queue
import threading
import time

# 3rd party modules
from PyQt4.QtCore import *
import serial

# Local application modules
import httpserver

class MsgSender(QThread):
    """
    Consumer thread for processing the SMS message queue.
    """
    def __init__(self, msg_queue, serial_conn, serial_conn_mutex, message_sent):
        """
        the "serial_conn" parameter is expected to be a serial.Serial object
        that is already connected to a handset. The "serial_conn_mutex" is a
        mutex used for regulating access to the serial port.

        The "message_sent" parameter is a function that is called once a
        message has been sent. This takes care of updating the GUI and logging
        to a file if neccessary.
        """

        # Store the parameters as instance variables
        self.msg_queue = msg_queue
        self.serial_conn = serial_conn
        self.serial_conn_mutex = serial_conn_mutex
        self.message_sent = message_sent

        self.keep_running = False
        self.conn_error = False
        QThread.__init__(self)

    def run(self):
        """
        Starts the thread which monitors and processes the message queue.
        """
        self.keep_running = True
        while self.keep_running:

            # Get a message from the queue
            try:
                message_data = self.msg_queue.get(timeout=2)
            except Queue.Empty:
                pass
            else:
                self.serial_conn_mutex.acquire()
                try:

                    # Write the message to the serial port
                    self.serial_conn.write('AT+CMGF=1\r')
                    self.serial_conn.write('AT+CSMP=17,169,0,24%d\r' % message_data['class'])
                    self.serial_conn.write('AT+CMGS="%s"\r' % message_data['recipient'])
                    self.serial_conn.write('%s\x1a' % message_data['message'])

                except serial.SerialException:

                    # Put the failed message back into the queue (at the front).
                    self.msg_queue.put(message_data, front=True)

                    # Stop the thread from running
                    self.stop(conn_error=True)
                else:

                    # Log the sent message
                    self.message_sent(message_data)
                finally:
                    self.serial_conn_mutex.release()

                # Sleep between sending messages (unless service is stopping)
                if self.keep_running:
                    time.sleep(2)

        # Close the connection to the handset before exiting the thread
        self.serial_conn_mutex.acquire()
        try:
            self.serial_conn.close()
        finally:
            self.serial_conn_mutex.release()

        self.emit(SIGNAL('threadExit()'))

    def stop(self, conn_error=False):
        """
        Stops the thread from processing any more messages, closes the COM port
        then ends the thread.
        """
        self.keep_running = False
        if conn_error:
            self.conn_error = True


class MsgReceiver(QThread):
    """
    Wrapper to run StoppableHTTPServer in a separate thread.
    """
    def __init__(self, log_http_data, message_received, port, hostname=''):
        """
        Creates and instance of StoppableHTTPServer and saves it as an instance
        variable.
        """
        self.http_server = httpserver.StoppableHTTPServer(log_http_data,
                                                          message_received,
                                                          (hostname, port),
                                                          httpserver.HTTPHandler)
        QThread.__init__(self)

    def run(self):
        """
        When the thread is started the server will begin accepting HTTP
        requests.

        To stop the server the "stop" method of this class should be called.
        """
        self.http_server.serve()
        self.emit(SIGNAL('threadExit()'))

    def stop(self):
        """
        Signals to the server to stop accepting requests. Once this has
        completed the thread will end.
        """
        self.http_server.stop()


class COMChecker(QThread):
    def __init__(self, parent):
        self.parent = parent
        self.keep_running = False
        QThread.__init__(self)

    def run(self):
        self.keep_running = True
        while self.keep_running:
            try:
                if self.parent.sender_thread.isRunning():
                    self.parent.serial_conn_mutex.acquire()
                    try:
                        self.parent.serial_conn.write('AT\r')
                    finally:
                        self.parent.serial_conn_mutex.release()
            except serial.SerialException:
                self.parent.sender_thread.stop(conn_error=True)
                self.parent.sender_thread.wait()

            if not self.parent.sender_thread.isRunning():
                self.parent.sender_thread.stop(conn_error=True)
                self.parent.sender_thread.wait()
                self.parent.tray_icon.showMessage('SMS Gateway Server',
                                                  'The connection to the COM port has been lost',
                                                  self.parent.tray_icon_critical,
                                                  10 * 1000)
                self.parent.log_activity('Connection to the COM port was lost.', error=True)

                # As the connection is now closed stop the thread from any future checking
                self.keep_running = False

            if self.keep_running:
                time.sleep(2)

        self.emit(SIGNAL('threadExit()'))

    def stop(self):
        self.keep_running = False
