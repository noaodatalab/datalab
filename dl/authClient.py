#!/usr/bin/env python
#
# AUTHCLIENT -- Client methods for the Data Lab Authentication Service
#

from __future__ import print_function

__authors__ = 'Mike Fitzpatrick <fitz@noao.edu>, Data Lab <datalab@noao.edu>'
__version__ = '20180321'  # yyyymmdd


""" 
    Client methods for the Data Lab Authentication Service.

Import via

.. code-block:: python

    from dl import authClient
"""

import requests
import socket
import os
import sys
from time import gmtime, strftime

try:
    from urllib import urlencode                # Python 2
    from urllib2 import urlopen, Request        # Python 2
    import ConfigParser                         # Python 2
except ImportError:
    from urllib.parse import urlencode          # Python 3
    from urllib.request import urlopen, Request # Python 3
    import configparser as ConfigParser         # Python 3


# Turn off some annoying astropy warnings
import warnings
from astropy.utils.exceptions import AstropyWarning
warnings.simplefilter('ignore', AstropyWarning)   

is_py3 = sys.version_info.major == 3



# Pre-defined authentication tokens. These are fixed strings that provide
# limited access to Data Lab services, this access is controlled on the
# server-side so we don't need strict security here.

ANON_TOKEN = "anonymous.0.0.anon_access"
DEMO_TOKEN = "dldemo.99999.99999.demo_access"
TEST_TOKEN = "dltest.99998.99998.test_access"

# Set the default user accounts for the authentication service.  We don't
# include privileged users so that account can remain secure.

DEF_USERS = {'anonymous': ANON_TOKEN,
             'dldemo': DEMO_TOKEN,
             'dltest': TEST_TOKEN}


# The URL of the AuthManager service to contact.  This may be changed by
# passing a new URL into the set_svc_url() method before beginning.

DEF_SERVICE_URL = "https://datalab.noao.edu/auth"
SM_SERVICE_URL  = "https://datalab.noao.edu/storage"
QM_SERVICE_URL  = "https://datalab.noao.edu/query"

# Allow the service URL for dev/test systems to override the default.
THIS_HOST = socket.gethostname()
if THIS_HOST[:5] == 'dldev':
    DEF_SERVICE_URL = "http://dldev.datalab.noao.edu/auth"
    SM_SERVICE_URL  = "http://dldev.datalab.noao.edu/storage"
    QM_SERVICE_URL  = "http://dldev.datalab.noao.edu/query"
elif THIS_HOST[:6] == 'dltest':
    DEF_SERVICE_URL = "http://dltest.datalab.noao.edu/auth"
    SM_SERVICE_URL  = "http://dltest.datalab.noao.edu/storage"
    QM_SERVICE_URL  = "http://dltest.datalab.noao.edu/query"


# The requested authentication "profile".  A profile refers to the specific
# machines and services used by the AuthManager on the server. Note that 
# profiles are not currently used.

DEF_SERVICE_PROFILE = "default"

# Use a /tmp/AM_DEBUG file as a way to turn on debugging in the client code.
DEBUG 	= os.path.isfile ('/tmp/AM_DEBUG')


# ######################################################################
#
#  Authentication Client Interface
#
#  This API provides convenience methods that allow an application to
#  import the Client class without having to explicitly instantiate a
#  class object.  The parameter descriptions and example usage is given
#  in the comments for the class methods.
#
# ######################################################################


# User methods -- All methods except login() return either a 'True' string
# or an error of the form 'ERR <message>'.  On success, the login() method
# will return the user-id token.

def login(user, password=None, debug=False, verbose=False):
    if user in list(DEF_USERS.keys()):
        return DEF_USERS[user]
    else:
        try:
            response = ac_client.login(user, password, debug)
        except Exception as e:
            response = str(e)
    return response


def whoAmI():
    pass

def isAlive(svc_url=DEF_SERVICE_URL):
    try:
        response = ac_client.isAlive(svc_url)
    except Exception as e:
        response = str(e)
    return (True if response.lower() == 'true' else False)


def isValidToken(token):
    try:
        user, uid, gid, hash = token.strip().split('.', 3)
    except Exception as e:
        return False

    if user in list(DEF_USERS.keys()) and token in list(DEF_USERS.values()):
        return True
    else:
        try:
            response = ac_client.isValidToken(token)
        except Exception as e:
            print (str(e))
            return False
    return (True if response.lower() == 'true' else False)


def isValidUser(user):
    if user in list(DEF_USERS.keys()):
        return True
    else:
        try:
            response = ac_client.isValidUser(user)
        except Exception as e:
            response = str(e)
    return (True if response.lower() == 'true' else False)


def isValidPassword(user, password):
    if (user == password) and (user in list(DEF_USERS.keys())):
        return True
    else:
        try:
            response = ac_client.isValidPassword(user, password)
        except Exception as e:
            response = str(e)
    return (True if response.lower() == 'true' else False)


def hasAccess(user, resource):
    try:
        response = ac_client.hasAccess(user, resource)
    except Exception as e:
        response = str(e)
    return (True if response.lower() == 'true' else False)


def isUserLoggedIn(user):
    try:
        response = ac_client.isUserLoggedIn(user)
    except Exception as e:
        response = str(e)
    return (True if response.lower() == 'true' else False)


def isTokenLoggedIn(token):
    try:
        response = ac_client.isTokenLoggedIn(token)
    except Exception as e:
        response = str(e)
    return (True if response.lower() == 'true' else False)


def logout(token):
    try:
        response = ac_client.logout(token)
    except Exception as e:
        response = str(e)
    return response


def passwordReset(token, username, password):
    try:
        response = ac_client.passwordReset(token, username, password)
    except Exception as e:
        response = str(e)
    return response


# Standard Service Methods
def set_svc_url(svc_url):
    return ac_client.set_svc_url(svc_url)


def get_svc_url():
    return ac_client.get_svc_url()


def set_profile(profile):
    return ac_client.set_profile(profile)


def get_profile():
    return ac_client.get_profile()


#def list_profiles(token, profile=None, format='text'):
#    return ac_client.list_profiles(token, profile, format)


# ###################################
#  Authentication error class
# ###################################

class dlAuthError (Exception):
    """ A throwable error class.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self, message):
        return self.message


#####################################
#  Authentication client procedures
#####################################

class authClient (object):
    """  
         AUTHCLIENT -- Client-side methods to access the Data Lab 
                       Authentication Service.
    """

    def __init__(self):
        """ Initialize the authorization client. """

        self.svc_url = DEF_SERVICE_URL          # service URL
        self.svc_profile = DEF_SERVICE_PROFILE  # service prfile
        self.username = ""                      # default client logn user
        self.auth_token = None                  # default client logn token

        # Get the $HOME/.datalab directory.
        self.home = '%s/.datalab' % os.path.expanduser('~')
        if not os.path.exists('%s' % self.home):
            os.makedirs (self.home)
            
        self.loadConfig()                       # load config file

        self.debug = DEBUG                      # interface debug flag

    def loadConfig (self):
        # Read the $HOME/.datalab/dl.conf file
        self.config = ConfigParser.RawConfigParser(allow_no_value=True)

        # If the config file doesn't exist yet, create a default.
        if not os.path.exists('%s/dl.conf' % self.home):
            self.config.add_section('datalab')
            self.config.set('datalab', 'created', strftime(
                '%Y-%m-%d %H:%M:%S', gmtime()))
            self.config.add_section('login')
            self.config.set('login', 'status', 'loggedout')
            self.config.set('login', 'user', '')
            self.config.set('login', 'authtoken', '')

            self.config.add_section('auth')
            self.config.set('auth', 'profile', 'default')
            self.config.set('auth', 'svc_url', DEF_SERVICE_URL)

            self.config.add_section('query')
            self.config.set('query', 'profile', 'default')
            self.config.set('query', 'svc_url', QM_SERVICE_URL)

            self.config.add_section('storage')
            self.config.set('storage', 'profile', 'default')
            self.config.set('storage', 'svc_url', SM_SERVICE_URL)

            self.config.add_section('vospace')
            self.config.set('vospace', 'mount', '')

            self.writeConfig()

        # Read back the config file.
        self.config.read('%s/dl.conf' % self.home)


    def setConfig (self, section, param, value):
        ''' Set a value and save the configuration file.
        '''
        if not self.config.has_section (section):
            self.config.add_section (section)
        self.config.set (section, param, value)
        self.writeConfig ()

    def getConfig (self, section, param):
        ''' Get a value from the configuration file.
        '''
        return self.config.get (section, param)

    def writeConfig (self):
        ''' Write out the configuration file to disk.
        '''
        with open ('%s/dl.conf' % self.home, 'w') as configfile:
            self.config.write (configfile)



    def set_svc_url(self, svc_url):
        """ Set the URL of the Authentication Service to be used.

        Parameters
        ----------
        svc_url : str
            Authentication service base URL to call.

        Returns
        -------
        Nothing

        Example
        -------
        .. code-block:: python

            from dl import authClient
            authClient.set_svc_url ("http://localhost:7001/")
        """

        self.svc_url = acToString(svc_url)

    def get_svc_url(self):
        """ Return the currently-used Authentication Service URL.

        Parameters
        ----------
        None

        Returns
        -------
        service_url : str
            The currently-used Authentication Service URL.

        Example
        -------
        .. code-block:: python

            from dl import authClient
            service_url = authClient.get_svc_url ()
        """

        return acToString(self.svc_url)

    def set_profile(self, profile):
        """ Set the requested service profile.

        Parameters
        ----------
        profile : str
            Requested service profile string.

        Returns
        -------
        Nothing

        Example
        -------
        .. code-block:: python

            from dl import authClient
            token = authClient.client.set_profile ("dev")
        """

        self.svc_profile = acToString(profile)

    def get_profile(self):
        """ Get the requested service profile.

        Parameters
        ----------
        None

        Returns
        -------
        profile : str
            The currently requested service profile.

        Example
        -------
        .. code-block:: python

            from dl import authClient
            profile = authClient.client.get_profile ()
        """

        return acToString(self.svc_profile)

    def list_profiles(self, token, profile=None, format='text'):
        """ List the service profiles which can be accessed by the user.

        Parameters
        ----------
        token : str
            Valid auth service token.

        Returns
        -------
        profiles : JSON string

        Example
        -------
        .. code-block:: python

            from dl import authClient
            profiles = authClient.client.list_profiles (token, profile, format)
        """

        pass

    def isAlive(self, svc_url=DEF_SERVICE_URL):
        """ Check whether the AuthManager service at the given URL is
            alive and responding.  This is a simple call to the root 
            service URL or ping() method.

        Parameters
        ----------
        service_url : str
            The Query Service URL to ping.

        Returns
        -------
        result : bool
            True if service responds properly, False otherwise

        Example
        -------
        .. code-block:: python

            from dl import authClient
            if authClient.isAlive():
                print ("Auth Manager is alive")
        """
        url = svc_url
        try:
            r = requests.get(url, timeout=2)
            resp = r.text

            if r.status_code != 200:
                return False
            elif resp is not None and r.text.lower()[:11] != "hello world":
                return False
        except Exception:
            return False

        return True


    ###################################################
    #  SESSION MANAGEMENT
    ###################################################

    def login(self, username, password, debug=False, verbose=False):
        """ Authenticate the user with the Authentication Service.
            We first check for a valid login token in the user's
            $HOME/.datalab/ directory and simply return that rather
            than make a service call to get a new token.  If a token
            exists but is invalid, we remove it and get a new
            token.  In either case, we save the token for later use.

        Parameters
        ----------
        username : str
            User login name.

        password : str
            User password.  If not given, a valid ID token will be
            searched for in the $HOME/.datalab directory.

        debug : bool
            Method debug flag.
        verbose : bool
            Initialize session to print verbose output messages.

        Returns
        -------
        token : str
            One-time security token for valid user (identified via
            'username' and 'password').

        Example
        -------
        .. code-block:: python

            from dl import authClient
            token = authClient.login ('dldemo', 'dldemo')   # get security token
        """

        # Check the $HOME/.datalab directory for a valid token.  If that dir
        # doesn't already exist, create it so we can store the new token.
        if not os.path.exists(self.home):
            os.makedirs(self.home)

        # See if a datalab token file exists for the requested user.
        tok_file = ('%s/id_token.%s' % (self.home, username))
        if self.debug:
            print ("top of login: tok_file = '" + tok_file + "'")
            print ("top of login: self.auth_token = '%s'" %
                   str(self.auth_token))
            print ("top of login: token = ")
            os.system("cat " + tok_file)

        if password is None:
            if os.path.exists(tok_file):
                tok_fd = open(tok_file, "r")
                o_tok = acToString(tok_fd.read(128))  # read the old token
                tok_fd.close()

                # Return a valid token, otherwise remove the file and obtain a
                # new one.
                if o_tok.startswith(username+'.') and self.isValidToken(o_tok):
                    self.username = username
                    self.auth_token = o_tok
                    if self.debug:
                        print ("using old token for '%s'" % username)
                    print ('o_tok type = ' + str(type (o_tok)))
                    return acToString(o_tok)
                else:
                    if self.debug:
                        print ("removing invalid token file '%s'" % tok_file)
                    os.remove(tok_file)

        # Either the user is not logged in or the token is invalid, so
        # make a service call to get a new token.
        url = self.svc_url + "/login?"
        query_args = {"username": username,
                      "password": password,
                      "profile": self.svc_profile,
                      "debug": self.debug}

        response = 'None'
        try:
            r = requests.get(url, params=query_args)
            response = acToString(r.content)

            if self.debug:
                print ("%s:  resp = '%s'" % (str(r.status_code),response))
            if r.status_code != 200:
                raise Exception(response)

        except Exception as e:
            if self.debug:
                print ("Raw exception msg = '%s'" % acToString(r.content))
            if self.isAlive(self.svc_url) == False:
                raise dlAuthError("AuthManager Service not responding.")
            if self.isValidUser(username):
                if password is None:
                    if not os.path.exists(tok_file):
                        raise dlAuthError("No password or token supplied")
                    else:
                        raise dlAuthError("No password supplied")
                elif not self.isValidPassword(username, password):
                    raise dlAuthError("Invalid password in login()")
                else:
                    raise dlAuthError(str(e))
            else:
                raise dlAuthError("Invalid username in login()")

        else:
            self.auth_token = response
            self.username = username

        # Save the token and config file.
        if os.access(self.home, os.W_OK):
            tok_file = '%s/id_token.%s' % (self.home, username)
            with open(tok_file, 'wb') as tok_fd:
                if self.debug:
                    print ("login: writing new token for '%s'" % username)
                    print ("login: self.auth_token = '%s'" %
                           str(self.auth_token))
                    print ("login: token = ")
                    os.system('cat ' + tok_file)

                tok_fd.write(acToString(self.auth_token))
                tok_fd.close()

            self.config.set('login', 'status', 'loggedin')
            self.config.set('login', 'user', username)
            self.config.set('login', 'authtoken', self.auth_token)
            self.writeConfig ()

        return acToString(self.auth_token)

    def logout(self, token):
        """ Log the user out of the Data Lab.
        """
        url = self.svc_url + "/logout?"
        args = urlencode({"token": token,
                          "debug": self.debug})
        url = url + args

        if self.debug:
            print ("logout: token = '%s'" % token)
            print ("logout: auth_token = '%s'" % self.auth_token)
            print ("logout: url = '%s'" % url)

        if not self.isValidToken(token):
            return "Error: Invalid user token"

        try:
            # Add the auth token to the reauest header.
            headers = {'X-DL-AuthToken': token}

            r = requests.get(url, params=args, headers=headers)
            response = acToString(r.content)

            if r.status_code != 200:
                raise Exception(response)

        except Exception as e:
            raise dlAuthError(str(e))
        else:
            self.auth_token = None
            tok_file = self.home + '/id_token.' + self.username
            if os.path.exists(tok_file):
                os.remove(tok_file)

            # Update the config file.
            if os.access(self.home, os.W_OK):
                tok_file = '%s/id_token.%s' % (self.home, username)
                with open(tok_file, 'wb') as tok_fd:
                    tok_fd.write(acToString(self.auth_token))
                    tok_fd.close()

            self.config.set('login', 'status', 'loggedout')
            self.config.set('login', 'user', '')
            self.config.set('login', 'authtoken', '')
            self.writeConfig ()

        return response

    def passwordReset(self, token, username, password):
        """  Reset a user password reset.  We require that the user provide
             either a valid 'root' token or the token for the account being
             reset.
        """
        url = self.svc_url + "/passwordReset?"
        args = urlencode({"token": token,
                          "username": username,
                          "password": password,
                          "debug": self.debug})
        url = url + args

        if self.debug:
            print ("passwdReset: token = '%s'" % token)
            print ("passwdReset: auth_token = '%s'" % self.auth_token)
            print ("passwdReset: url = '%s'" % url)

        if not self.isValidToken(token):
            if self.debug:
                print ("passwdReset: Invalid user token")
            raise Exception("Error: Invalid user token")

        # Reset the auth_token to the one passed in by the service call.
        self.auth_token = token

        user, uid, gid, hash = self.auth_token.strip().split('.', 3)
        if user != 'root' and user != username:
            raise Exception("Error: Invalid user or non-root token")

        try:
            # Add the auth token to the reauest header.
            headers = {'X-DL-AuthToken': token}

            r = requests.get(url, params=args, headers=headers)
            response = acToString(r.content)

            if r.status_code != 200:
                #raise Exception(r.text)
                raise Exception(r.content)

        except Exception:
            #raise dlAuthError(r.text)
            raise dlAuthError(r.content)
        else:
            # Update the saved user token.
            print ("Updating saved user token ....")
            if response is not None:
                self.auth_token = response
                tok_file = self.home + '/id_token.' + self.username
                if os.path.exists(tok_file):
                    print ("pwreset: removing token file " + tok_file)
                    os.remove(tok_file)
                with open(tok_file, 'wb') as tok_fd:
                    if self.debug:
                        print ("pwreset: writing new token for '%s'" + username)
                        print ("pwreset: response = '%s'" + response)
                        print ("pwreset: token = '%s'" + self.auth_token)
                    tok_fd.write(acToString(self.auth_token))
                    tok_fd.close()
            else:
                print ('pwReset response is None')

        return response

    def hasAccess(self, token, resource):
        """  See whether the token has access to the named Resource.  Returns
             True if the user owns the Resource, or if the Resource grants
             group permissions to a Group to which the token belongs.
        """
        # Either the user is not logged in or the token is invalid, so
        # make a service call to get a new token.
        url = self.svc_url + "/hasAccess?"
        args = urlencode({"user": token,
                          "resource": resource,
                          "profile": self.svc_profile})
        url = url + args

        if self.debug:
            print ("hasAccess: url = '%s'" % url)

        return self.retBoolValue(url)

    def isValidToken(self, token):
        """ See whether the current token is valid.
        """
        url = self.svc_url + "/isValidToken?"
        args = urlencode({"token": token,
                          "profile": self.svc_profile})
        url = url + args

        if self.debug:
            print ("isValidToken: url = '%s'" % url)

        # Save the value before returning so we can print it in debug mode.
        isValid = self.retBoolValue(url)
        if self.debug:
            print ("isValidToken: valid = " + str(isValid))

        return isValid

    def isValidPassword(self, user, password):
        """ See whether the password is valid for the user.
        """
        url = self.svc_url + "/isValidPassword?"
        args = urlencode({"user": user,
                          "password": password,
                          "profile": self.svc_profile})
        url = url + args

        if self.debug:
            print ("isValidPassword: url = '%s'" % url)

        try:
            val = self.retBoolValue(url)
        except Exception:
            val = "False"

        return val

    def isValidUser(self, user):
        """ See whether the specified user is valid.
        """
        url = self.svc_url + "/isValidUser?"
        args = urlencode({"user": user,
                          "profile": self.svc_profile})
        url = url + args

        if self.debug:
            print ("isValidUser: url = '%s'" % url)

        try:
            val = self.retBoolValue(url)
        except Exception:
            val = "False"

        return val

    def isUserLoggedIn(self, user):
        """ See whether the user identified by the token is currently
            logged in.
        """
        url = self.svc_url + "/isUserLoggedIn?"
        args = urlencode({"user": user,
                          "profile": self.svc_profile})
        url = url + args

        if self.debug:
            print ("isUserLoggedIn: url = '%s'" % url)

        try:
            val = self.retBoolValue(url)
        except Exception:
            val = "False"

        return val

    def isTokenLoggedIn(self, token):
        """ See whether the user identified by the token is currently
            logged in.
        """
        url = self.svc_url + "/isTokenLoggedIn?"
        args = urlencode({"token": token,
                          "profile": self.svc_profile})
        url = url + args

        if self.debug:
            print ("isTokenLoggedIn: tok = '%s'" % token)
            print ("isTokenLoggedIn: url = '%s'" % url)

        try:
            val = self.retBoolValue(url)
        except Exception:
            val = "False"

        return val

    ###################################################
    #  PRIVATE UTILITY METHODS
    ###################################################

    def debug(self, debug_val):
        self.debug = debug_val

    def retBoolValue(self, url):
        """  Utility method to call a boolean service at the given URL.
        """
        response = ""
        try:
            # Add the auth token to the reauest header.
            if self.auth_token != None:
                headers = {'X-DL-AuthToken': self.auth_token}
                r = requests.get(url, headers=headers)
            else:
                r = requests.get(url)
            response = acToString(r.content)

            if r.status_code != 200:
                raise Exception(r.content)

        except Exception:
            return acToString(r.content)
        else:
            return response

    # Get default tracking headers,
    def getHeaders (self, token):
        tok = def_token(token)
        user, uid, gid, hash = tok.strip().split('.', 3)
        hdrs = {'Content-Type': 'text/ascii',
                'X-DL-ClientVersion': __version__,
                'X-DL-OriginIP': self.hostip,
                'X-DL-OriginHost': self.hostname,
                'X-DL-User': user,
                'X-DL-AuthToken': tok}                  # application/x-sql
        return hdrs

    # Get something from a URL.  Return a 'response' object
    def getFromURL (self, svc_url, path, token):
        try:
            hdrs = self.qc_getHeaders (token)
            resp = requests.get("%s%s" % (svc_url, path), headers=hdrs)

        except Exception as e:
            raise queryClientError(str(e))
        return resp



# ###################################
#  Authentication Client Handles
# ###################################

def getClient():
    return authClient()


ac_client = getClient()




# ####################################################################
#  Py2/Py3 Compatability Utilities
# ####################################################################

def acToString(s):
    """ acToString -- Force a return value to be type 'string' for all
                      Python versions.
    """
    if is_py3:
        if isinstance(s,bytes):
            strval = str(s.decode())
        elif isinstance(s,str):
            strval = s
    else:
        if isinstance(s,bytes) or isinstance(s,unicode):
            strval = str(s)
        else:
            strval = s

    return strval
