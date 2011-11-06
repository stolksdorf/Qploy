import wsgiref.handlers
import operator
import datetime
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp \
  import template
from google.appengine.ext.webapp.util import run_wsgi_app

class Players(db.Model):
  name = db.StringProperty(required=True)
  
class Kills(db.Model):
  assassin = db.StringProperty(required=True)
  target = db.StringProperty(required=True)
  method = db.StringProperty()
  when = db.DateTimeProperty(auto_now_add=True)
  
class Ranking:
        def __init__(self,tname, score, tkills, tlives):
            self.name = tname
            self.score = score
            self.kills = tkills
            self.lives = tlives

class MainPage(webapp.RequestHandler):
    def get(self):
        players = db.GqlQuery('SELECT * FROM Players')
        ranks=[]
        for player in players:
          kill_temp = db.GqlQuery("SELECT * FROM Kills WHERE assassin = :1", player.name)
          death_temp = db.GqlQuery("SELECT * FROM Kills WHERE target = :1", player.name)
          temp = Ranking(player.name, kill_temp.count() - death_temp.count(), kill_temp.count(), death_temp.count())
          ranks.append(temp)
          ranks.sort(key=operator.attrgetter('score'))
          ranks.reverse()       
        
        kills = db.GqlQuery('SELECT * FROM Kills ORDER BY when DESC')
        #correct the time zone difference 
        new_kills=[]
        t = datetime.timedelta(hours=4)
        for kill in kills:             
          kill.when = kill.when - t
          new_kills.append(kill) 
                
        values = {'players':players, 'kills':new_kills, 'ranks':ranks }          
        self.response.out.write(template.render('main.html', values))
  
    def post(self):
        process = self.request.get('process') 
        if process == 'save_player':
          temp_name = self.request.get('signup')          
          if temp_name != "": 
            if not "<" in temp_name:              
              player = Players(name=temp_name)
              player.put()
        elif process == 'save_kill':
          hacks = "<" in self.request.get('assassin') or "<" in self.request.get('target') or "<" in self.request.get('method')
          if self.request.get('method') != "How did you deliver the poison?" and self.request.get('assassin') != self.request.get('target') and not hacks:
            kill = Kills(assassin=self.request.get('assassin'),
                         target=self.request.get('target'),
                         method=self.request.get('method'))
            kill.put()
        elif process == 'send_email':
          mail.send_mail(to="Scott Tolksdorf <scott.tolksdorf@gmail.com>",
                         subject="Feedback from QPLOY",
                         body=self.request.get('feedback'))
            
        
        
        self.redirect('/')

application = webapp.WSGIApplication(
                                     [('/', MainPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()