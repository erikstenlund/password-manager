"""
Simple class encapsulating access to dropbox
"""

__version__ = '0.1'
__author__ = 'Erik Stenlund'

import dropbox

class DropboxSync():
    def __init__(self, access_token):
        self.access_token = access_token
        self.client = dropbox.client.DropboxClient(access_token)

    def push(self, local_filename, cloud_filename=None):
        if cloud_filename is None:
            cloud_filename = local_filename

        with open(local_filename, 'rb') as f:
            meta = self.client.put_file(cloud_filename, f, True)

        return meta

    def pull(self, local_filename, cloud_filename=None):
        if cloud_filename is None:
            cloud_filename = local_filename

        with open(local_filename, 'wb') as f:
            response, meta = self.client.get_file_and_metadata(cloud_filename)
            f.write(response.read())

        return meta
