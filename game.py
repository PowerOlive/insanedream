#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.ioloop, tornado.web, tornado.autoreload, tornado.options
from tornado.escape import utf8
import os, time
from modules import world, database
from modules.player import Player
from modules.world import World
from modules.database import DB
#@todo makesound for exits in location
current_date = time.strftime('%d-%m-%Y')
_world = World()
_db = DB()
_player = Player()


class BaseHandler(tornado.web.RequestHandler):
            
    def get_current_user(self):
        return self.get_secure_cookie('username')
    
    def get_current_account(self):
        return self.get_secure_cookie('account')
    
    def initialize(self):
        self.msg = []
        if not self.get_current_user():
            self.user = None
        else:
            self.user = tornado.escape.xhtml_escape(self.get_current_user())

        if not self.get_current_account():
            self.account = None
        else:
            self.account = tornado.escape.xhtml_escape(self.get_current_account())
class Index(BaseHandler):
    
    @tornado.web.asynchronous
    def get(self):
        self.async_callback(self._on_render())
    
    @tornado.web.asynchronous
    def post(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        if not username:
            self.msg.append('enter login')
        elif not password:
            self.msg.append('enter password')
        else:
            if _db.check_login(username,password):
                uname = _db.get_user(username)
                self.set_secure_cookie("username", uname['username'])
                #log.access('user logged in(username: %s, ip:%s)' % (uname['username'], self.request.remote_ip))
                self.redirect('/')
            else:
                self.msg.append('вы ввели неправильный пароль или такого пользователя не существует')
                #log.error('error auth(login:%s, password: %s, ip: %s)' % (username, password, self.request.remote_ip))
        self.async_callback(self._on_render())
                
    def _on_render(self):
        self.render('index.xhtml', message=self.msg, username=self.user, users_count=len(_world.online_who()))

class Registration(BaseHandler):
    
    @tornado.web.asynchronous
    def get(self):
        self.async_callback(self._on_render())
        
    @tornado.web.asynchronous
    def post(self):
        username = self.get_argument("username", None)
        password = self.get_argument("password", None)
        password_repeat = self.get_argument("password_repeat", None)
        email = self.get_argument("email", None)
        if not username:
            self.msg.append('enter login')
        else:
            if _db.user_exists(username):
                self.msg.append('user with this login alreasy exists')
            else:
                if not password:
                    self.msg.append('enter password')
                elif not password_repeat:
                    self.msg.append('repeat password')
                elif password != password_repeat:
                    self.msg.append('password is not identific')
                elif not email:
                    self.msg.append('enter e-mail')
                else:
                    _db.create_user(username,password, email, current_date, self.request.remote_ip)
                    self.set_secure_cookie("username", username)
                    self.redirect('/')
        self.async_callback(self._on_render())

    def _on_render(self):
        self.render('register.xhtml', message=self.msg, username=self.user)

class Logout(BaseHandler):
    
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        self.async_callback(self._on_logout())

    def _on_logout(self):
        self.clear_cookie('username')
        self.redirect('/')

class WhoOnline(BaseHandler):
    
    @tornado.web.asynchronous
    def get(self):
        self.async_callback(self._on_render())
    
    def _on_render(self):
        self.render('online.xhtml', message=self.msg, users=_world.online_who())

class About(BaseHandler):
    
    @tornado.web.asynchronous
    def get(self):
        self.async_callback(self._on_render())
    
    def _on_render(self):
        self.render('about.xhtml', message=self.msg)

class Contacts(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        self.async_callback(self._on_render())

    def _on_render(self):
        self.render('contacts.xhtml', message=self.msg)

class Rules(BaseHandler):
    
    @tornado.web.asynchronous
    def get(self):
        self.async_callback(self._on_render())
        
    def _on_render(self):
        self.render('rules.xhtml', message=self.msg)

class Profile(BaseHandler):
    
    @tornado.web.asynchronous
    def get(self, username):
        self.async_callback(self._on_render(username))
        
    def _on_render(self, username):
        self.render('profile.xhtml', message=self.msg, profile=username)

class GameAccounts(BaseHandler):

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        acc = _db.get_players(self.user)
        delete_name = self.get_argument('delete', '')
        select_name = self.get_argument('select', '')
        if select_name:
            self.redirect('/game/connect/%s' % select_name)
        if delete_name:
            _db.delete_player(delete_name,acc['user']['account_id'])
            self.redirect('/game/connect')
        self.async_callback(self._on_render(acc))

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self):
        acc = _db.get_players(self.user)
        name = utf8(self.get_argument('name_player', ''))
        if not name:
            self.msg.append('not name')
        elif _db.player_exists(name) > 0:
            self.msg.append('already exist in world')
        elif len(acc['accounts']) == 5:
            self.msg.append('maximum count characters')
        else:
            _db.create_player(acc['user']['account_id'],name)
            self.redirect('/game/connect')
        self.async_callback(self._on_render(acc))
        
    def _on_render(self, accs):
        self.render('accounts.xhtml', message=self.msg, username=self.user, accounts=accs['accounts'])

class GameAccount(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self, accountName):
        self.set_secure_cookie('account', accountName)
        if accountName not in _world.online_who():
            _player.load(accountName)
            location = _player.get_param('location')
            player = _player.get()
            _world.update_loc(location, player)
        self.async_callback(self._on_render(accountName))
        _world.online_add(self.get_current_account())

    def _on_render(self, accountName):
        self.render('account.xhtml', message=self.msg, username=self.user, account=accountName)
"""
class GameAccountSettings(BaseHandler):

@tornado.web.authenticated
@tornado.web.asynchronous
def get(self, account):
    self.async_callback(self.on_render())

def _on_render(self):
self.render('settings.xhtml', message=self.msg, username=self.user)
"""
class Game(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous

    def go(self, new_loc):
        loc = _player.get_param('location')
        c_loc = _world.get_loc(loc)['war']
        n_loc = _world.get_loc(new_loc)['war']
        if new_loc in _world.get_loc(_player.get_param('location'))['exits']:
            _player.set_param('location',new_loc)
            if (c_loc==2) and (n_loc==1):
                self.msg.append('you in peace territory')
            elif (c_loc==1) and (n_loc==2):
                self.msg.append('you in war territory')
            #elif c_loc==n_loc:
            #    _player.set_param('journal','')
            _world.move(_player.get(),loc,new_loc)
            return new_loc
        else:
            return False
        del c_loc,n_loc

    def to_offline(self,account):
            if _player.get_param('war') !='':
                return False
            else:
                _player.save(self.get_current_account())
                _world.to_offline(account)
                return True

    def get(self):
        path = self.get_argument('go',None)
        target = self.get_argument('target',None)
        action = self.get_argument('action',None)
        self.msg.append(_player.get_param('journal'))
        if path:
            self.go(path)
        if target:
            if target in _world.get_in_lock(_player.get_param('location')):
                self.async_callback(self._on_actions(target))
        if action:
            if action=='save':
                self.async_callback(self._on_save())
            if action=='profile':
                self.async_callback(self._on_profile())
            if action=='logout':
                self.async_callback(self._on_logout())

        self.async_callback(self._on_render())

    def post(self):
        pass

    def _on_render(self):
        location = _world.get_loc(_player.get_param('location'))
        stmp = _world.get_in_lock(_player.get_param('location'))
        self.render('game.html',
                    message = self.msg,
                    player = self.get_current_account(),
                    location = location,
                    stmp = stmp,
                    life = _player.get_param('life'),
                    life_max = _player.get_param('life_max'),
                    mana = _player.get_param('mana'),
                    mana_max = _player.get_param('mana_max'),
                    )

    def _on_profile(self):
        for name,val in _player.get().items():
            self.write('%s : %s<br/>' % (name,val))
        self.finish()
        
    def _on_actions(self,target):
        self.write('actions for %s' % target)
        self.finish()

    def _on_save(self):
        _player.save(self.get_current_account())
        self.msg.append('your charakter be saved')

    def _on_logout(self):
        account = _player.get()
        if self.to_offline(account):
            self.write('your char is saved, bye. <a href="/">Index page</a>')
        else:
            self.msg.append('error logout. you in fight')
        self.finish()

class GameServer(tornado.web.Application):
    def __init__(self):
        handlers = routes = [
            (r'/', Index),
            (r'/register', Registration),
            (r'/logout', Logout),
            (r'/online', WhoOnline),
            (r'/about', About),
            (r'/contacts', Contacts),
            (r'/rules', Rules),
            (r'/profile/(.*?)', Profile),
            (r'/game', Game),
            (r'/game/connect', GameAccounts),
            (r'/game/connect/(.*?)', GameAccount),
            #(r'/game/connect/settings/(.*?)', GameAccountSettings),
            
        ]
        settings = {
            'game_title': 'Insane Dream',
            'template_path': os.path.join(os.path.dirname(__file__), "data/templates"),
            'static_path': os.path.join(os.path.dirname(__file__), "data/static"),
            'xsrf_cookies': True,
            'cookie_secret': "11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            'login_url': "/",
            'port': 8080,
        }
        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    srv = GameServer()
    srv.listen(srv.settings['port'])
    #thread.start_new_thread(_system, ())
    tornado.options.parse_command_line()
    tornado.ioloop.IOLoop.instance().start()
    tornado.autoreload.start(io_loop=None, check_time=10)
    
if __name__ == "__main__":
    main()
