# 
# Copyright (C) 2018 Jonathon Ogden <jeog.dev@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
# 

"""tdma_api/auth.py - authentication and credential management interface 

The auth module provides basic authentication and credential management 
methods and objects for the TDAmeritrade API.

https://github.com/jeog/TDAmeritradeAPI#authentication

"""

from ctypes import Structure as _Structure, c_char_p, c_longlong, \
                    c_ulonglong, byref as _REF

from . import clib
from .common import *
from .clib import PCHAR

class Credentials(_Structure):
    """Object that represents the underlying access Credentials.

    An instance will be returned from 'load_credentials' or
    'request_access_token'. It will be passed to various API methods
    and objects, being (automatically) updated with new tokens.

    DO NOT assign to these fields directly as this will cause a 
    memory leak! In the(unlikely) event you need to change fields 
    create a new instance  with the 'Create()' class method.
    """
    _fields_ = [
        ("access_token", c_char_p),
        ("refresh_token", c_char_p),
        ("epoch_sec_token_expiration", c_longlong),
        ("client_id", c_char_p)
        ]
    def __del__(self):
        if hasattr(self,'access_token') and self.access_token:           
            try:
                try:                                  
                    clib.call("CloseCredentials_ABI", _REF(self))                   
                except clib.CLibException as e:
                    print("CLibException in", self.__del__, ":", str(e))                                   
            except:
                pass

    @classmethod
    def Create(cls, access_token, refresh_token, 
               epoch_sec_token_expiration, client_id):
        """Create a new Credential instance."""
        creds = Credentials()
        clib.call('CreateCredentials_ABI', PCHAR(access_token), 
                  PCHAR(refresh_token), c_ulonglong(epoch_sec_token_expiration),
                  PCHAR(client_id), _REF(creds))
        return creds

    
def load_credentials(path, password):
    """Load a credentials object from an encrypted credentials file.
    
    def load_credentials(path, password):      
      
        path     :: str :: path of credentials file
        password :: str :: password for decrypting credentials file
        
        returns  ->  Credentials object
        throws   ->  LibraryNotLoaded, CLibException
    """
    creds = Credentials()
    clib.call('LoadCredentials_ABI', PCHAR(path), PCHAR(password), 
              _REF(creds))
    return creds
    

def store_credentials(path, password, creds):
    """Store a credentials object to an encrypted credentials file.
    
    def store_credentials(path, password, creds):   
         
        path     :: str         :: path of credentials file
        password :: str         :: password for decrypting credentials file
        creds    :: Credentials :: credentials object to store
        
        returns  ->  None
        throws   ->  LibraryNotLoaded, CLibException
    """
    clib.call('StoreCredentials_ABI', PCHAR(path), PCHAR(password),  
              _REF(creds))


def request_access_token(code, client_id, redirect_uri="https://127.0.0.1"):
    """Returns 'Credentials' intance for accessing API.
    
    Uses an access code, and the fields set during developer/app registration, 
    to request access and refresh tokens. The tokens are used to create a 
    'Credentials' instance which allows access to the API until the refresh 
    token expires in 90 days.

    https://github.com/jeog/TDAmeritradeAPI#manual-approach
        
    def request_access_token(code, 
                             client_id, 
                             redirect_uri="https://127.0.0.1"):    
                                
        code          ::  str  ::  access code retrieve from TDAmeritrade
        client_id     ::  str  ::  unique id from setting up developer account
        redirect_uri  ::  str  ::  uri used in getting access code
        
        returns      ->  Credentials object 
        throws       ->  LibraryNotLoaded, CLibException
    """    
    creds = Credentials()
    clib.call('RequestAccessToken_ABI', PCHAR(code), PCHAR(client_id), 
              PCHAR(redirect_uri), _REF(creds))
    return creds


def refresh_access_token(creds):
    """Refresh an expired access token. THIS IS DONE AUTOMATICALLY.
    
    def refresh_access_token(creds):
    
         creds    :: Credentials :: credentials object with token to refresh
         
         returns  ->  None
         throws   ->  LibraryNotLoaded, CLibException               
    """
    clib.call('RefreshAccessToken_ABI', _REF(creds))


def set_certificate_bundle_path(path):
    """Set certificate bundle file(.pem) path for ssl/tls host authentication.
    
    If library is built against default ssl/tls library the default certificate
    store should be used. If not(a connection error is returned) you'll have to 
    provide a certificate bundle to the connection libraries. 
    
    def set_certificate_bundle_path(path);
    
        path    ::  str  ::  path to the certificate bundle file(.pem)
        
        returns -> None
        throws  -> LibraryNotLoaded, CLibException
    """

    clib.set_str('SetCertificateBundlePath_ABI', path)


def get_certificate_bundle_path():
    """Get certificate bundle file(.pem) path for ssl/tls host authentication.
    
    If library requires a user supplied certificate bundle this method returns
    its path. 
    
    def get_certificate_bundle_path();       
     
        returns -> str of certificate bundle path
        throws  -> LibraryNotLoaded, CLibException
    """
    return clib.get_str('GetCertificateBundlePath_ABI')


class CredentialsManager:    
    """Context Manager for handling load and store of Credentials Object.
    
    Use this object to automatically load and store your Credentials object
    from the encrypted file. 
    
    def __init__(self, path, password, verbose=False):   
             
        path     :: str  :: path of credentials file
        password :: str  :: password for decrypting credentials file
        verbose  :: bool :: send status messages to stdout
        
        returns  ->  CredentialsManager instance
        throws   ->  LibraryNotLoaded, CLibException    
    """
    def __init__(self, path, password, verbose=False):
        self._verbose = verbose
        self.path = path
        self.password = password
        self.credentials = None
        
    def __enter__(self):
        if self._verbose:
            print("+ Load credentials from ", self.path)
        try:           
            self.credentials = load_credentials(self.path, self.password)
            if self._verbose:
                print("+ Successfully loaded credentials")
            return self
        except:
            if self._verbose:
                print("- Failed to load credentials")             
            raise                
      
    def __exit__(self, _1, _2, _3):        
        if self._verbose:
            print("+ Store credentials to ", self.path)
        if not self.credentials:
            if self._verbose:
                print("- No credentials to store")
            return
        try:           
            store_credentials(self.path, self.password, self.credentials)
            if self._verbose:
                print("+ Successfully stored credentials")
        except BaseException as e:
            if self._verbose:
                print("- Failed to store credentials")
                print("-", e.__class__.__name__ + ':', str(e))
