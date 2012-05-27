import os
import datetime
import logging
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import db
import time
import urllib
import cgi
import Cookie
from django.utils import simplejson as json
import hmac
import hashlib
import base64
import email.utils


FACEBOOK_APP_ID = "319087381501577"
FACEBOOK_APP_SECRET = "00a2e17f026aa9cd849184dea9cb2519"

def current_user(self):
    if not hasattr(self, "_current_user"):
        self._current_user = None
        user_id = parse_cookie(self.request.cookies.get("fb_user"))
        if user_id:
            self._current_user = User.get_by_key_name(user_id)
    return self._current_user
def parse_cookie(value):
    if not value: return None
    parts = value.split("|")
    if len(parts) != 3: return None
    if cookie_signature(parts[0], parts[1]) != parts[2]:
        logging.warning("Invalid cookie signature %r", value)
        return None
    timestamp = int(parts[1])
    if timestamp < time.time() - 30 * 86400:
        logging.warning("Expired cookie %r", value)
        return None
    try:
        return base64.b64decode(parts[0]).strip()
    except:
        return None
def cookie_signature(*parts):
    hash = hmac.new(FACEBOOK_APP_SECRET, digestmod=hashlib.sha1)
    for part in parts: hash.update(part)
    return hash.hexdigest()
def set_cookie(response, name, value, domain=None, path="/", expires=None):
    timestamp = str(int(time.time()))
    value = base64.b64encode(value)
    signature = cookie_signature(value, timestamp)
    cookie = Cookie.BaseCookie()
    cookie[name] = "|".join([value, timestamp, signature])
    cookie[name]["path"] = path
    if domain: cookie[name]["domain"] = domain
    if expires:
        cookie[name]["expires"] = email.utils.formatdate(expires, localtime=False, usegmt=True)
    response.headers._headers.append(("Set-Cookie", cookie.output()[12:]))
class User(db.Model):
    id=db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add = True)
    updated = db.DateTimeProperty(auto_now = True)
    name=db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)
class MyUser(db.Model):
    uid=db.StringProperty(required=True)
    name=db.StringProperty(required=True)
    email = db.StringProperty(required=True)
    team = db.StringProperty(required=True)

class StartPage(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'demo.html')
        if(users.get_current_user()):
            #user is logged in using Google
            #if user is logged in with fb too, log him out
            if(current_user(self)==None):
                #go on
                a=5
            else:
                #Log user out of FB
                set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
            #At this stage, the user is logged in to google
            query = db.GqlQuery("SELECT * FROM MyUser WHERE uid = 'GOOG" + users.get_current_user().email() + "'")
            response = query.fetch(limit=1)
            if(len(response)<1):
                #new user
                template_1 = {'uid':'GOOG'+users.get_current_user().email()}
                self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'example.html'), template_1))
            
            #Go to profile page
            else:
                self.redirect("http://www.myeur.org/registered/")
            
        else:
            #user not logged in with Google
            #Check if he is logged in with FB, if yes, send him to profile page
            if(current_user(self)==None):
                a=5
                #not logged in; Render landing page
                url=users.create_login_url('/')
                template_values = {'google_url': url}
                self.response.out.write(template.render(path, template_values))
            else:
                #logged in
                query = db.GqlQuery("SELECT * FROM MyUser WHERE uid = 'FACE" +current_user(self).id + "'")
                response = query.fetch(limit=1)
                if(len(response)<1):
                    template_2 = {'uid':'FACE'+current_user(self).id}
                    self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'example.html'), template_2))
                else:
                    self.redirect("http://www.myeur.org/registered/")
                #new user
                
        
class FBLogged(webapp.RequestHandler):
    def get(self):
        args = dict(client_id=FACEBOOK_APP_ID, redirect_uri='http://www.myeur.org/logged')
        args["client_secret"] = FACEBOOK_APP_SECRET
        args["code"] = self.request.get("code")
        response = cgi.parse_qs(urllib.urlopen("https://graph.facebook.com/oauth/access_token?" + urllib.urlencode(args)).read())
        access_token = response["access_token"][-1]
        profile = json.load(urllib.urlopen("https://graph.facebook.com/me?" + urllib.urlencode(dict(access_token=access_token))))
        user_id=(profile["id"])
        user = User(key_name=str(profile["id"]), id=str(profile["id"]),name=profile["name"], access_token=access_token,profile_url=profile["link"])
        user.put()
        set_cookie(self.response, "fb_user", str(profile["id"]), expires=time.time() + 30 * 86400)
        #access token is written if needed. Pack, go to main page?
        self.redirect('/')
        
class Registered(webapp.RequestHandler):
    def post(self):
        myuser = MyUser(email = self.request.get('email'), name = self.request.get('name'), uid = self.request.get('uid'), team = self.request.get('drop'))
        myuser.put()
        #name=self.request.get('name')
        #email = self.request.get('email')
        #uid=self.request.get('uid')
        #team=self.request.get('drop')
        template_3={}
        #strin = (name + ' ' + email + ' ' + uid + ' ' + team)
        self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'registered.html'), template_3))
        
        
    def get(self):
        template_7={}
        #strin = (name + ' ' + email + ' ' + uid + ' ' + team)
        self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'registered.html'), template_7))
    
        
application = webapp.WSGIApplication([('/', StartPage),('/logged.*',FBLogged),('/registered/',Registered)
                                      ],
                                     debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
