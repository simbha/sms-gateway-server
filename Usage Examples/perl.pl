# Demonstration script to show usage of the SMS Gateway Server.

use strict;
use warnings;
use LWP::UserAgent;

# Create a UserAgent instance
my $ua = new LWP::UserAgent;

# Define the message content
my $post_data = {
    recipients => '07745896325; 07745856932',
    message => 'Hello!!',
};

# Send the messsage request to the server
my $response = $ua->post('http://localhost/send_message', $post_data);

# Print the status received from the server
print $response->status_line();
