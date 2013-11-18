"""
Demonstration script to show usage of the SMS Gateway Server.
"""
import httplib
import urllib

# Define the message content
post_data = urllib.urlencode({'recipients': '07745896325; 07745856932',
                              'message': 'This is an SMS message!'})

# Create a connection to the server
conn = httplib.HTTPConnection('localhost')

# Send the messsage request to the server
conn.request('POST', '/send_message', post_data)

# Get the server response
response = conn.getresponse()

# Print the status received from the server
print '%s: %s' % (response.status, response.reason)

# Close the connection to the server
conn.close()
