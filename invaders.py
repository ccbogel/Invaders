#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A shoot em up space invaders type game.
Uses space and arrow keys to move the spacecraft.
Game inspired from pyqt5 code snippet from Roger Allen
https://gist.github.com/rogerallen/f06ba704ce3befb5459239e3fdf842c7
'''

from PyQt5.QtCore import (Qt, QBasicTimer)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QImage, QFontDatabase, QFont, QPen)
from PyQt5.QtWidgets import (QMainWindow, qApp, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QGraphicsPixmapItem,  QGraphicsTextItem, QInputDialog, QLineEdit)
from GUI.main import Ui_MainWindow
import random
import subprocess
import time

#SCREEN_WIDTH            = 800
#SCREEN_HEIGHT           = 600
PLAYER_SPEED = 5   # pix/frame
PLAYER_BULLET_X_OFFSET = 15  # half width of bullet
PLAYER_BULLET_Y = 5
BULLET_SPEED = 10  # pix/frame
BULLET_FRAMES = 70
ENEMY_BULLET_X_OFFSET = 15  # half width of bullet
EXPLOSION_FRAMES = 2
FRAME_TIME_MS = 16  # ms/frame
MAIN_TEXT = "Alien Invaders\n\nN for new game\n\nSpace to Shoot\n\nLeft Right Up Down arrows to move\n\nBonus Items: Shield, Slow Alien Descent, Instant Destruct\n\nTry and avoid the Alien Transports\n\nBeware of the UFOs\n\nDo not let the Aliens land\n"


class Scene(QGraphicsScene):

    game_over = False
    game_over_part_2 = False
    score = 0
    lost = False
    lost_counter = 0
    bullets = []
    explosions = None
    keys_pressed = None
    player = None
    enemies = []
    bullets = []
    enbullets = []
    explosions = []
    wave = 1
    msg = None  # major game messages: game over, new wave
    bonuses = []
    ui = None
    w = 0
    h = 0

    def __init__(self, w, h, ui, parent=None):
        QGraphicsScene.__init__(self, parent)

        self.w = w
        self.h = h
        self.setSceneRect(0, 0, w, h)
        self.ui = ui
        self.new_game()

    def new_game(self):

        self.ui.graphicsView.show()
        self.ui.label.hide()
        # hold the set of keys that are being pressed
        self.keys_pressed = set()
        self.clear()
        self.game_over = False
        self.lost = False
        self.player_hit = False
        self.wave = 0
        self.score = 0
        self.ui.label.hide()
        self.score_item = Score()
        self.addItem(self.score_item)
        self.player = Player(self.width(), self.height())
        self.enemies = []
        self.enbullets = []
        self.msg = None
        self.bonuses = []
        self.bullets = [Bullet(PLAYER_BULLET_X_OFFSET, PLAYER_BULLET_Y, self.width(), self.height())]
        for b in self.bullets:
            b.setPos(self.width(), self.height())
            self.addItem(b)
        self.addItem(self.player)
        #time.sleep(3)
        self.enemy_wave_setup()
        # use a timer to get 60Hz refresh for scene
        self.timer = QBasicTimer()
        self.timer.start(FRAME_TIME_MS, self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_N and self.game_over:
            self.new_game()
            return
        self.keys_pressed.add(event.key())

    def keyReleaseEvent(self, event):
        try:
            self.keys_pressed.remove(event.key())
        except:
            pass

    def timerEvent(self, event):
        self.game_update()
        self.update()

    def game_update(self):

        if self.game_over:
            if self.msg.frames > 0:
                self.msg.game_update()
            else:
              self.end_of_game_part_2()
            return

        # update player moves and bullets
        self.player.game_update(self.keys_pressed)
        for b in self.bullets:
            b.game_update(self.keys_pressed, self.player)

        # check for enemy collides with player
        for e in self.enemies:
            hits = self.collidingItems(e)
            if hits != []:
                for hit in hits:
                    if type(hit).__name__ == "Player":
                        self.lost = True
                        time.sleep(2)
        # update enemies and explosions
        for e in self.enemies:
            e.game_update()
            if e.y() > self.height():
                self.lost = True
        for ex in self.explosions:
            ex.game_update()

        # bonuses
        if random.randint(0, 500) == 0 and len(self.bonuses) < 2:
            bonus = BonusItem(self.width(), self.height())
            self.bonuses.append(bonus)
            self.addItem(bonus)
        for bonus in self.bonuses:
            bonus.game_update()

        # check for enemy bullet collisions
        for eb in self.enbullets:
            hits = self.collidingItems(eb)
            if hits != []:
                for hit in hits:
                    # enemy bullet collides with ring shield
                    if type(hit).__name__ == "BonusItem" and hit.effect is True and hit.name == "shield":
                        eb.setVisible(False)
                    # enemy bullet collides with player
                    if type(hit).__name__ == "Player":
                        self.lost = True
                    if self.lost:
                        for b in self.bonuses:
                            if b.effect is True and b.name == "shield":
                                self.lost = False
                    if self.lost:
                        self.player.setPixmap(QPixmap("Images/Explosion2.png"))

        for eb in self.enbullets:
            eb.game_update()

        # check for player bullet collision with Enemy or BonusItem
        for b in self.bullets:
            hits = self.collidingItems(b)
            # direct enemy hit
            if hits != [] and type(hits[0]).__name__ == "Enemy":
                #subprocess.Popen(["aplay", "Sounds/NFF-robo-hit.wav"])  # windows replace aplay with start
                subprocess.Popen(["aplay", "Sounds/NFF-bump.wav"])  # windows replace aplay with start
                b.hit_enemy(hits[0])
                if hits[0].hp == 0:
                    self.score += hits[0].score
                en_pos = (hits[0].pos())
                explode = Explosion(en_pos.x(), en_pos.y())
                self.explosions.append(explode)
                self.addItem(explode)
            # hit enemy through Effects of Dreams or Flare
            if len(hits) > 1 and type(hits[0]).__name__ == "BonusItem" and \
            hits[0].effect is True and hits[0].name in ("flare", "dreams") and \
            type(hits[1]).__name__ == "Enemy":
                b.hit_enemy(hits[1])
                if hits[1].hp == 0:
                    self.score += hits[1].score
                en_pos = (hits[1].pos())
                explode = Explosion(en_pos.x(), en_pos.y())
                self.explosions.append(explode)
                self.addItem(explode)
            # hit bonus and activate item
            if hits != [] and type(hits[0]).__name__ == "BonusItem" and \
            hits[0].effect is False:
                hits[0].effect = True
                hits[0].game_update()
                # an anti-bonus item if Alien transport hit
                if hits[0].name == "Alien transport" and self.msg is None:
                    for i in range(0, 5):
                        e = Enemy(self.width(), self.height(), 24, hits[0].x(), hits[0].y())
                        self.enemies.append(e)
                        self.addItem(e)

        # BonusItem
        for b in self.bonuses:
            # check if Flare collides with Enemies
            if b.effect and b.name == "flare":
                hits = self.collidingItems(b)
                for hit in hits:
                    if type(hit).__name__ == "Enemy":
                        hit.hp = 0
                        if hit.hp == 0:
                            self.score += hit.score
                        en_pos = (hit.pos())
                        explode = Explosion(en_pos.x(), en_pos.y())
                        self.explosions.append(explode)
                        self.addItem(explode)
            # check if SLowed collides with Enemies
            if b.effect and b.name == "slowed":
                hits = self.collidingItems(b)
                for hit in hits:
                    if type(hit).__name__ == "Enemy" and hit.pos().y() > 0:
                        hit.dy = 0.12
                        #hit.dx = 1.2

            # If a shield, position it over player
            if b.effect and b.name == "shield":
                b.update_to_player_pos(self.player)

        self.score_item.game_update(self.wave, self.score)
        self.cleanup_items()
        self.maybe_add_enbullets()

        # check for game end
        if self.lost:
            self.game_over = True
            self.end_of_game()

        # update message
        if self.msg is not None:
            self.msg.game_update()

        # begin new wave, after msg fade out
        if self.msg is not None and self.msg.frames <= 0:
            self.enemy_wave_setup()

        # check for new wave, countdown Msg frames til new wave
        if len(self.enemies) == 0 and self.msg is None:
            self.msg = FadeMessage()
            self.msg.setPlainText("Wave " + str(self.wave + 1))
            self.addItem(self.msg)

    def enemy_wave_setup(self):
        ''' All enemies defeated, new wave created.
        Add two extra enemies at each higher wave '''

        p = subprocess.Popen(["aplay", "Sounds/NFF-alert.wav"])
        p.communicate()
        self.wave += 1
        items = self.items()
        for i in items:
            if type(i).__name__ not in ('Player', 'Score', 'Bullet'):
                self.removeItem(i)
        self.msg = None
        self.explosions = []
        self.enemies = []
        self.bonuses = []
        self.enbullets = []
        for i in range(3 + int(self.wave * 1.5)):
            e = Enemy(self.width(), self.height())
            self.enemies.append(e)
            self.addItem(e)
        #time.sleep(1)

    def maybe_add_enbullets(self):
        ''' small chance to fire a bullet from each enemy '''

        for e in self.enemies:
            if random.randint(0, 1000) < 5:
                self.add_enbullet(e)
            if e.name == "Mother UFO" and random.randint(0, 1000) < 10:  # was 15 but too many bullets
                self.add_enbullet(e)

    def add_enbullet(self, enemy):
        ''' Non-directional bullet fired from most enemies '''

        color = "2"
        if enemy.name == "Big mother":
            color = "3"
        if enemy.name != "Mother UFO":
            eb = EnemyBullet(enemy.x() + enemy.pixmap().width() / 2, enemy.y(), color)
            self.enbullets.append(eb)
            self.addItem(eb)
        else:
            eb = EnemyDirectedBullet(enemy.x() + enemy.pixmap().width() / 2, enemy.y(), self.player.x(), self.player.y())
            self.enbullets.append(eb)
            self.addItem(eb)

    def end_of_game(self):
        '''  '''

        time.sleep(1)
        msg = "GAME OVER\n"
        if len(self.enemies) == 0:
            msg += "You Won"
        else:
            msg += "Too bad\nYou died"
        self.msg = FadeMessage()
        self.msg.setPlainText(msg)
        self.addItem(self.msg)

    def end_of_game_part_2(self):
        ''' Need to wait until msg has played through.
        Add high scores.
        Called from game_update via timer event. '''

        self.game_over_part_2 = True
        self.timer.stop()
        with open('scores') as f:
            high_scores = []
            for line in f:
                try:
                    high_scores.append([line.split()[0], line.split()[1], line.split()[2]])
                except:
                    pass
        if len(high_scores) > 5:
            high_scores = high_scores[0:5]
        hs_text = ""
        new_high_score = False
        for hs in high_scores:
            if self.score > int(hs[1]):
                new_high_score = True
        if len(high_scores) == 0:
            new_high_score = True
        if new_high_score:
            name = QInputDialog.getText(None, "High score","Congratulations\nEnter your name:", QLineEdit.Normal, "")
            name = name[0].replace(" ", "")
            for i in range(0, len(high_scores)):
                if self.score > int(high_scores[i][1]):
                    high_scores.insert(i, [name, str(self.score), str(self.wave)])
                    break
            if len(high_scores) == 0:
                high_scores.append([name, str(self.score), str(self.wave)])
        if len(high_scores) > 5:
            high_scores = high_scores[0:5]
        with open('scores', "w") as f:
            for hs in high_scores:
                hs_text += "\n\n" + hs[0] + "  score: " + hs[1] + "  wave: " + hs[2]
                f.write(hs[0] + " " + hs[1] + " " + hs[2] + "\n")
        txt = MAIN_TEXT + "\n\nHIGH SCORES:\n" + hs_text
        self.ui.label.setText(txt)
        self.ui.label.show()
        self.ui.graphicsView.hide()
        self.explosions = []
        self.enemies = []
        self.bonuses = []
        self.enbullets = []

    def cleanup_items(self):
        ''' Remove expired enBullets, Enemies and Explosions from the scene and lists.
        '''

        items = self.items()
        for i in items:
            if type(i).__name__ == "Explosion" and i.counter == 0:
                self.removeItem(i)
            if type(i).__name__ == "Enemy" and i.hp == 0:
                self.removeItem(i)
            if type(i).__name__ == "EnemyBullet" and i.active is False:
                self.removeItem(i)
            if type(i).__name__ == "BonusItem" and i.active is False:
                self.removeItem(i)
            if type(i).__name__ == "Message" and i.frames < 0:
                self.removeItem(i)
                self.msg = None

        tmp = []
        for e in self.explosions:
            if e.counter > 0:
                tmp.append(e)
        self.explosions = tmp
        tmp = []
        for e in self.enemies:
            if e.hp > 0:
                tmp.append(e)
        self.enemies = tmp
        tmp = []
        for b in self.bonuses:
            if b.active:
                tmp.append(b)
        self.bonuses = tmp
        tmp = []
        for eb in self.enbullets:
            if eb.active:
                tmp.append(eb)
        self.enbullets = tmp


class FadeMessage(QGraphicsTextItem):
    ''' Text is set using setPlainText method '''

    frames = 255

    def init(self, parent=None):
        super(QGraphicsTextItem).__init__(parent)

        self.setPlainText("")
        self.setFont(QFont("Robotica", 40))
        self.setDefaultTextColor(QColor(255, 255, 0))
        self.setPos(200, 300)
        self.frames = 255

    def game_update(self):
        ''' '''

        self.frames -= 1
        alpha = self.frames
        if alpha < 0:
            alpha = 0
        self.setFont(QFont("Robotica", 40))
        self.setDefaultTextColor(QColor(255, 255, 0, alpha))
        self.setPos(200, 300)


class Score(QGraphicsTextItem):
    '''  '''

    def init(self, parent=None):
        QGraphicsTextItem.__init__(self, parent)

        self.setPlainText("Wave: 0 Score: 0")
        self.setFont(QFont("Robotica", 15))
        self.setDefaultTextColor(QColor(255, 255, 0))
        self.setPos(10, 670)

    def game_update(self, wave, score):
        ''' '''

        self.setPlainText("Wave: " + str(wave) + " Score: " + str(score))
        self.setFont(QFont("Robotica", 20))
        self.setDefaultTextColor(QColor(255, 255, 0))
        self.setPos(10, 670)


class Explosion(QGraphicsPixmapItem):
    ''' uses explosions images '''

    def __init__(self, x, y, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        # load image frames
        explosion_grid = QImage("Images/explosion_16x64x64.png")
        self.explosion_pics = []
        for col in range(0, 4):
            for row in range(0, 4):
                self.explosion_pics.append(QPixmap.fromImage(explosion_grid.copy(row * 64, col * 64, 64, 64)))
        self.counter = 0.1
        self.setPixmap(self.explosion_pics[int(self.counter)])
        self.x = x
        self.y = y
        self.setPos(x, y)
        self.frames = 0

    def game_update(self):
        ''' '''

        self.frames = EXPLOSION_FRAMES
        if self.counter > 0:
            self.counter += 0.4
        if self.counter > 15:
            self.counter = 0
            return
        self.setPixmap(self.explosion_pics[int(self.counter)])


class Enemy(QGraphicsPixmapItem):
    ''' Curently four different types '''

    def __init__(self, scr_w, scr_h, en_type=-1, en_x=-1, en_y=-1, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)

        entype = en_type
        if entype == -1:
            entype = random.randint(0, 100)
        self.pic = []
        self.counter = 0
        self.dx = 0.4
        self.dy = 0.3
        self.hp = 1
        self.score = 10
        self.name = ""
        self.scr_w = scr_w
        self.scr_h = scr_h
        y = en_y
        if y < 0:
            y = random.randint(-100, 0)
        if entype < 30:
            self.dy = 0.15 + random.randint(0, 4) / 20
            self.dx = 0.35 + random.randint(0, 8) / 10
            self.name = "Dangly tentacles"
            self.hp = 2
            self.score = 20
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir1.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir2.png"))
        if entype >= 30 and entype < 55:
            self.name = "Lots a tentacles"
            self.dy = 0.15
            self.dx = 1.9 + random.randint(0, 4) / 10
            self.hp = 2
            self.score = 20
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir5.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir7a.png"))
        if entype >= 55 and entype < 60:
            self.name = "Big mother"
            self.hp = 3
            self.dy = 0.19
            self.dx = 1
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir4.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir3.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir5.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir3.png"))
            self.score = 30
        if entype >= 60 and entype < 90:
            self.name = "Space mine"
            self.dx = 1 + random.randint(0, 6) / 10
            self.dy = 0.45
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir6.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir6a.png"))
        if entype >= 90:
            self.score = 50
            self.name = "Mother UFO"
            y = -80
            self.dx = 0.9 + random.randint(0, 4) / 10
            self.dy = 0.2
            self.hp = 5
            self.pic.append(QPixmap("Images/UFO1c.png"))
            self.pic.append(QPixmap("Images/UFO1d.png"))
        self.setPixmap(self.pic[0])

        # randomise dx direction
        d = random.randint(0, 1)
        if d == 0:
            self.dx = -1 * self.dx

        x = en_x
        if x < 0:
            x = random.randint(10, self.scr_w - self.pixmap().width() - 10)
        self.setPos(x, y)

    def game_update(self):
        '''  '''

        if self.x() + self.dx < 0:
            self.dx = -1 * self.dx
        if self.x() + self.dx + self.pixmap().width()+ 10 > self.scr_w:
            self.dx = -1 * self.dx
        self.counter += 0.05
        if self.counter >= len(self.pic):
            self.counter = 0
        self.setPixmap(self.pic[int(self.counter)])
        self.setPos(self.x() + self.dx, self.y() + self.dy)


class EnemyDirectedBullet(QGraphicsPixmapItem):
    ''' Used by Mother UFO '''

    bullet_speed = 3.5

    def __init__(self, x, y, player_x, player_y, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        self.setPixmap(QPixmap("Images/bolt4.png"))
        self.frames = 0
        self.bullet_speed = 3.5
        self.x = x - ENEMY_BULLET_X_OFFSET
        self.y = y
        self.dx = 0
        x_diff = self.x - player_x
        if x_diff >= -30 and x_diff <= 50:
            self.dx = random.randint(0, 5) - 3
        if x_diff < -30:
            self.dx = random.randint(0, 5)
        if x_diff > 50:
            self.dx = random.randint(0, 5) * -1

        if self.y > player_y:
            self.bullet_speed = -3.5
        self.setVisible(True)
        self.active = True
        self.setPos(self.x, self.y)
        self.frames = 180  # enemy_bullet_frames

    def game_update(self):
        ''' Could not get QSound or QSoundEffect to work, using subprocess '''
        if self.active:
            self.y += self.bullet_speed
            self.x += self.dx
            self.setPos(self.x, self.y)
            self.frames -= 1
            if self.frames <= 0:
                self.active = False
                self.setVisible(False)
                self.setPos(0, -100)


class EnemyBullet(QGraphicsPixmapItem):

    bullet_speed = 4

    def __init__(self, x, y, color="2", parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        self.setPixmap(QPixmap("Images/bolt" + color + ".png"))
        self.frames = 0
        self.x = x - ENEMY_BULLET_X_OFFSET
        self.y = y
        self.setVisible(True)
        self.active = True
        self.setPos(self.x, self.y)
        self.frames = 180  # enemy_bullet_frames
        self.bullet_speed = 4

    def game_update(self):
        ''' Could not get QSound or QSoundEffect to work, using subprocess '''
        if self.active:
            self.y += self.bullet_speed
            self.setPos(self.x, self.y)
            self.frames -= 1
            if self.frames <= 0:
                self.active = False
                self.setVisible(False)
                self.setPos(0, -100)


class BonusItem(QGraphicsPixmapItem):
    ''' Curently 1 different type of Item '''

    def __init__(self, scr_w, scr_h, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)

        self.pen = QPen(Qt.blue, 3, Qt.SolidLine)
        self.scr_w = scr_w
        self.scr_h = scr_h
        self.pic = []
        self.counter = 0
        self.dx = 1.2
        direction = random.randint(0, 1)
        if direction == 0:
            self.dx = -1 * self.dx
        self.dy = 0
        self.hp = 1
        self.score = 60
        self.active = True
        self.effect = False
        self.effect_pic_set = False
        self.name = "default"
        self.frames = 900  # for ring protection and other?
        x = -40
        if self.dx < 0:
            x = self.scr_w + 40
        i = random.randint(0, 3)
        if i == 0:
            self.name = "flare"
            self.hp = 1
            self.score = 60
            self.pic.append(QPixmap("Images/Spybot/1.png"))
            self.pic.append(QPixmap("Images/Spybot/2.png"))
            self.pic.append(QPixmap("Images/Spybot/3.png"))
            self.pic.append(QPixmap("Images/Spybot/3.png"))
            self.pic.append(QPixmap("Images/Spybot/2.png"))
            self.pic.append(QPixmap("Images/Spybot/1.png"))
        if i == 1:
            self.name = "shield"
            self.hp = 1
            self.score = 60
            self.pic.append(QPixmap("Images/Spybot/10.png"))
        if i == 2:
            self.name = "slowed"
            self.hp = 1
            self.score = 60
            self.pic.append(QPixmap("Images/PunkRobot/punkrobot0.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.FastTransformation))
            self.pic.append(QPixmap("Images/PunkRobot/punkrobot1.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.FastTransformation))
        if i == 3:
            self.name = "Alien transport"
            self.hp = 1
            self.score = 0
            self.pic.append(QPixmap("Images/UFO2a.png"))
            self.pic.append(QPixmap("Images/UFO2b.png"))
            self.pic.append(QPixmap("Images/UFO2c.png"))

        self.setPixmap(self.pic[0])
        #x = -50  # random.randint(10, self.scr_w - self.pixmap().width())
        y = random.randint(60, 250)
        self.setPos(x, y)

        # flare
        self.flare = QPixmap("Images/flare_1.png")
        self.flareoffsets = [self.flare.width() / 2, self.flare.height() / 2]
        self.flarereducer = 0.9  # percent reduction per frame of original pixmap
        self.flarereduction = 100  # percentage of original pixmap

        self.shield0 = QPixmap("Images/ring0.png").scaled(100, 100, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.shield1 = QPixmap("Images/ring1.png").scaled(100, 100, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.shield2 = QPixmap("Images/ring2.png").scaled(100, 100, Qt.KeepAspectRatio, Qt.FastTransformation)

        self.slowed = []
        for i in range(1, 10):
            self.slowed.append(QPixmap("Images/slowed/slow" + str(i) + ".png"))
        for i in range(9, 0, -1):
            self.slowed.append(QPixmap("Images/slowed/slow" + str(i) + ".png"))

    def game_update(self):
        '''  '''

        if self.effect is False:
            self.counter += 0.05
            if self.counter >= len(self.pic):
                self.counter = 0
            self.setPixmap(self.pic[int(self.counter)])
            self.setPos(self.x() + self.dx, self.y() + self.dy)

            if self.dx > 0 and self.x() > self.scr_w:
                self.active = False
            if self.dx < 0 and self.x() < 0:
                self.active = False
            return

        if self.name == "Alien transport":
            self.active = False
            subprocess.Popen(["aplay", "Sounds/NFF-alien-02.wav"])  # windows replace aplay with start

        if self.name == "flare":
            if self.effect_pic_set is False:
                self.setPixmap(self.flare)
                self.effect_pic_set = True
                subprocess.Popen(["aplay", "Sounds/NFF-glittering.wav"])  # windows replace aplay with start
            self.setPos(self.x() - self.flareoffsets[0], self.y() - self.flareoffsets[1])
            self.flareoffsets = [0, 0]  # initial offset to position flare over original pixmap
            # resize gradually
            self.flarereduction -= self.flarereducer
            if self.flarereduction < 5:
                self.active = False
                return

            w = self.flarereduction / 100 * self.flare.width()
            h = self.flarereduction / 100 * self.flare.height()
            self.flareoffsets[0] = self.flare.width() - w
            self.flareoffsets[1] = self.flare.height() - h
            self.setPixmap(self.flare.scaled(w, h, Qt.KeepAspectRatio, Qt.FastTransformation))
            self.setPos(self.x() + self.flareoffsets[0], self.y() + self.flareoffsets[1])

        if self.name == "shield":
            if self.effect_pic_set is False:
                self.setPixmap(self.shield0)
                self.effect_pic_set = True
                subprocess.Popen(["aplay", "Sounds/NFF-ufo.wav"])  # windows replace aplay with start

        if self.name == "slowed":
            if self.effect_pic_set is False:
                self.effect_pic_set = True
                self.setPixmap(self.slowed[0])
                self.setPos(self.x() - self.slowed[0].width() / 2, self.y() - self.slowed[0].height() / 2)
                self.counter = 0
                subprocess.Popen(["aplay", "Sounds/NFF-shooting-star-02.wav"])  # windows replace aplay with start
                return
            self.counter += 1
            if self.counter >= len(self.slowed):
                self.active = False
                return
            self.setPixmap(self.slowed[int(self.counter)])

    def update_to_player_pos(self, player):
        ''' Only for shield effect '''
        self.frames -= 1
        #print(self.frames)
        if self.frames < 1:
            self.active = False
        self.setPos(player.x() - 25, player.y() - 25)  # magic number offsets
        if self.frames < 500 and self.frames >= 200:
            self.setPixmap(self.shield1)
        if self.frames < 200:
            self.setPixmap(self.shield2)


class Player(QGraphicsPixmapItem):
    ''' Set up player half way across and almost on bottom of scene '''

    def __init__(self, scr_w, scr_h, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        self.setPixmap(QPixmap("Images/DurrrSpaceShip_50.png"))
        self.scr_w = scr_w
        self.scr_h = scr_h
        self.setPos((self.scr_w - self.pixmap().width()) / 2,
            self.scr_h - self.pixmap().height() - 10)

    def game_update(self, keys_pressed):
        ''' Left is A or Left arrow, Right is D or Right Arrow, Space to fire '''
        dx = 0
        dy = 0
        if Qt.Key_A in keys_pressed or Qt.Key_Left in keys_pressed:
            dx -= PLAYER_SPEED
            if self.x() - dx < 0:
                dx = 0
        if Qt.Key_D in keys_pressed or Qt.Key_Right in keys_pressed:
            dx += PLAYER_SPEED
            if self.x() + dx > self.scr_w - self.pixmap().width():
                dx = 0
        if Qt.Key_W in keys_pressed or Qt.Key_Up in keys_pressed:
            dy -= PLAYER_SPEED
            if self.y() + dy < 1:
                dy = 0
        if Qt.Key_S in keys_pressed or Qt.Key_Down in keys_pressed:
            dy += PLAYER_SPEED
            if self.y() + dy > 670:
                dy = 0
        self.setPos(self.x() + dx, self.y() + dy)


class Bullet(QGraphicsPixmapItem):

    def __init__(self, offset_x, offset_y, scr_w, scr_h, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        self.setPixmap(QPixmap("Images/bolt1.png"))
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scr_w = scr_w
        self.scr_h = scr_h
        self.active = False
        self.frames = 0

    def game_update(self, keys_pressed, player):
        ''' Could not get QSound or QSoundEffect to work, using subprocess '''
        if not self.active:
            if Qt.Key_Space in keys_pressed:
                subprocess.Popen(["aplay", "Sounds/tir.wav"])  # windows replace aplay with start
                self.setVisible(True)
                self.active = True
                self.setPos(player.x() + player.pixmap().width()/2 - self.offset_x, player.y() + self.offset_y)
                self.frames = BULLET_FRAMES
        else:
            self.setPos(self.x(), self.y() - BULLET_SPEED)
            self.frames -= 1
            if self.frames <= 0 or self.y() < -30:
                self.active = False
                self.setVisible(False)
                self.setPos(self.scr_w, self.scr_h)

    def hit_enemy(self, enemy):
        ''' Called on collision detect '''
        self.active = False
        self.setVisible(False)
        self.setPos(self.scr_w, self.scr_h)
        enemy.hp -= 1


class MainWindow(QMainWindow):
    '''  '''

    screenwidth = 0
    screenheight = 0
    view_w = 0
    view_h = 0
    gane_started = False

    def __init__(self, screenwidth, screenheight):
        ''' Get log in detail before using app '''

        self.screenwidth = screenwidth
        self.screenheight = screenheight

        # Set up user interface from ui_main.py file
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.label_high_scores.hide()

        self.setStyleSheet('background-image:url(Images/prestige-COD.jpg); background-position: tiled;')
        #self.ui.actionNew.triggered.connect(self.new_game)
        self.ui.actionQuit.triggered.connect(self.exit_app)
        size = self.ui.graphicsView.size()
        self.view_w = size.width()
        self.view_h = size.height()

        self.ui.graphicsView.setRenderHint(QPainter.Antialiasing)
        self.ui.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        bg = QPixmap('Images/bg1.jpg')
        bg = bg.scaled(size.width(), size.height())
        self.ui.graphicsView.setBackgroundBrush(QBrush(bg))
        self.ui.graphicsView.setCacheMode(QGraphicsView.CacheBackground)
        self.ui.graphicsView.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.ui.graphicsView.hide()
        #self.ui.label.setText("")

        self.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_N:
            self.new_game()
        if event.key() == Qt.Key_Q:
            self.exit_app()

    def new_game(self):
        '''  '''
        self.ui.graphicsView.show()
        self.ui.graphicsView.setFocus(True)
        self.gane_started = True
        # add scene after window is displayed to get graphics view size
        self.scene = Scene(self.view_w, self.view_h, self.ui)
        #self.scene.setSceneRect(0, 0, self.view_w, self.view_h)
        self.ui.graphicsView.setScene(self.scene)
        self.ui.graphicsView.show()

    def exit_app(self):

        qApp.quit()
        sys.exit(0)

if __name__ == '__main__':

    import sys
    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont("GUI/Robotica.ttf")
    with open("GUI/stylesheet", "r") as fh:
        app.setStyleSheet(fh.read())
    screen_resolution = app.desktop().screenGeometry()
    width, height = screen_resolution.width(), screen_resolution.height()
    window = MainWindow(width, height)

sys.exit(app.exec_())
