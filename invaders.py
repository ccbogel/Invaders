#!/usr/bin/env python3
# -*- coding: utf-8 -*-


""" Game inspired from pyqt5 code snippet from Roger Allen
https://gist.github.com/rogerallen/f06ba704ce3befb5459239e3fdf842c7
"""

from PyQt6.QtCore import (Qt, QBasicTimer)
from PyQt6.QtGui import (QBrush, QColor, QPainter, QPixmap, QImage, QFontDatabase, QFont, QPen)
from PyQt6.QtWidgets import (QMainWindow, QApplication, QGraphicsItem, QGraphicsScene,
                             QGraphicsView, QGraphicsPixmapItem, QGraphicsTextItem)
from GUI.main import Ui_MainWindow
import random
import subprocess
import sys
import time

PLAYER_SPEED = 5  # pix/frame
PLAYER_BULLET_X_OFFSET = 15  # half width of bullet
PLAYER_BULLET_Y = 5
BULLET_SPEED = 10  # pix/frame
BULLET_FRAMES = 70
ENEMY_BULLET_X_OFFSET = 15  # half width of bullet
EXPLOSION_FRAMES = 2
FRAME_TIME_MS = 16  # ms/frame
TEST = True


class Scene(QGraphicsScene):

    def __init__(self, width, height, parent=None):
        QGraphicsScene.__init__(self, parent)

        if TEST: print("Scene init  - start")
        self.setSceneRect(0, 0, width, height)
        self.player_hit = False
        self.score_item = None
        self.wave = 0
        self.score = 0
        self.game_over = False
        self.lost = False
        self.lost_counter = 0
        self.bullets = []
        self.explosions = []
        self.keys_pressed = None
        self.player = None
        self.enemies = []
        self.enbullets = []
        self.bonuses = []
        self.msg = None

        # Use timer to get 60Hz refresh for scene
        self.timer = QBasicTimer()
        self.timer.start(FRAME_TIME_MS, self)
        self.new_game()
        if TEST: print("Scene init done")

    def new_game(self):
        """ Set variables, clear score. """

        if TEST: print("scene.new_game start")

        # Hold the set of keys that are being pressed
        self.keys_pressed = set()
        self.clear()
        self.game_over = False
        self.lost = False
        self.player_hit = False
        self.wave = 0
        self.score = 0
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
        self.enemy_wave_setup()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_N and self.game_over:
            self.new_game()
            return
        self.keys_pressed.add(event.key())

    def keyReleaseEvent(self, event):
        try:
            self.keys_pressed.remove(event.key())
        except:  # TODO fix bare exept
            pass

    def timerEvent(self, event):
        self.game_update()
        self.update()

    def game_update(self):

        if self.game_over:
            if self.msg is not None:
                self.msg.game_update()
            return

        # Update player moves and bullets
        self.player.game_update(self.keys_pressed)
        for bullet in self.bullets:
            bullet.game_update(self.keys_pressed, self.player)

        # Check for enemy collides with player
        for enemy in self.enemies:
            hits = self.collidingItems(enemy)
            if hits:
                for hit in hits:
                    if type(hit).__name__ == "Player":
                        self.lost = True
                        time.sleep(2)
        # Update enemies and explosions
        for enemy in self.enemies:
            enemy.game_update()
            if enemy.y() > self.height():
                self.lost = True
        for explosion in self.explosions:
            explosion.game_update()

        # Bonuses
        if random.randint(0, 500) == 0 and len(self.bonuses) < 2:
            bonus = BonusItem(self.width(), self.height())
            self.bonuses.append(bonus)
            self.addItem(bonus)
        for bonus in self.bonuses:
            bonus.game_update()

        # Check for enemy bullet collisions
        for bullet in self.enbullets:
            hits = self.collidingItems(bullet)
            if hits:
                for hit in hits:
                    # Enemy bullet collides with ring shield
                    if type(hit).__name__ == "BonusItem" and hit.effect is True and hit.name == "shield":
                        bullet.setVisible(False)
                    # Enemy bullet collides with player
                    if type(hit).__name__ == "Player":
                        self.lost = True
                    if self.lost:
                        for bonus in self.bonuses:
                            if bonus.effect is True and bonus.name == "shield":
                                self.lost = False
                    if self.lost:
                        self.player.setPixmap(QPixmap("Images/Explosion2.png"))

        for bullet in self.enbullets:
            bullet.game_update()

        # Check for player bullet collision with Enemy or BonusItem
        for bullet in self.bullets:
            hits = self.collidingItems(bullet)
            # Enemy is hit
            if hits and type(hits[0]).__name__ == "Enemy":
                # subprocess.Popen(["aplay", "Sounds/NFF-robo-hit.wav"])  # windows replace aplay with start
                # TODO subprocess.Popen(["aplay", "Sounds/NFF-bump.wav"])  # windows replace aplay with start
                bullet.hit_enemy(hits[0])
                if hits[0].hp == 0:
                    self.score += hits[0].score
                en_pos = (hits[0].pos())
                explode = Explosion(en_pos.x(), en_pos.y())
                self.explosions.append(explode)
                self.addItem(explode)
            # Hit enemy through Effects or Dreams or Flare
            if len(hits) > 1 and type(hits[0]).__name__ == "BonusItem" and \
                    hits[0].effect is True and hits[0].name in ("flare", "dreams") and \
                    type(hits[1]).__name__ == "Enemy":
                if TEST: print("Hit bonus item (flare or dreams) ", hits[0].name)
                bullet.hit_enemy(hits[1])
                if hits[1].hp == 0:
                    self.score += hits[1].score
                en_pos = (hits[1].pos())
                explode = Explosion(en_pos.x(), en_pos.y())
                self.explosions.append(explode)
                self.addItem(explode)
            # Hit bonus and activate item
            if hits != [] and type(hits[0]).__name__ == "BonusItem" and \
                    hits[0].effect is False:
                if TEST: print("Hit bonus item, activate item: ", hits[0].name)
                hits[0].effect = True
                hits[0].game_update()
                # An anti-bonus item if Alien transport hit
                if hits[0].name == "Alien transport" and self.msg is None:
                    if TEST: print("Alien transport")
                    for i in range(0, 5):
                        enemy = Enemy(self.width(), self.height(), 24, hits[0].x(), hits[0].y())
                        self.enemies.append(enemy)
                        self.addItem(enemy)

        # BonusItem
        for bonus in self.bonuses:
            # Check if Flare collides with Enemies
            if TEST: print("bonus", bonus.effect, bonus.name)
            if bonus.effect and b.name == "flare":
                print("flare")
                hits = self.collidingItems(bonus)
                for hit in hits:
                    if type(hit).__name__ == "Enemy":
                        hit.hp = 0
                        if hit.hp == 0:
                            self.score += hit.score
                        en_pos = (hit.pos())
                        explode = Explosion(en_pos.x(), en_pos.y())
                        self.explosions.append(explode)
                        self.addItem(explode)
            # Check if Slowed collides with Enemies
            if bonus.effect and bonus.name == "slowed":
                if TEST:print("Scene.game_update. if bonus.effect and bonus.name=slowed")
                hits = self.collidingItems(bonus)
                for hit in hits:
                    if type(hit).__name__ == "Enemy" and hit.pos().y() > 0:
                        hit.dy = 0.12
                        # hit.dx = 1.2

            # If a shield, position it over player
            if bonus.effect and bonus.name == "shield":
                if TEST: print("Scene.game_update shield - position over player")
                bonus.update_to_player_pos(self.player)

        self.score_item.game_update(self.wave, self.score)
        self.cleanup_items()
        self.maybe_add_enbullets()

        # Check for game end
        if self.lost:
            self.game_over = True
            self.end_of_game()

        # Update message
        if self.msg is not None:
            self.msg.game_update()

        # Begin new wave, after msg fade out
        if self.msg is not None and self.msg.frames <= 0:
            self.enemy_wave_setup()

        # Check for new wave, countdown Msg frames til new wave
        if len(self.enemies) == 0 and self.msg is None:
            self.msg = FadeMessage()
            self.msg.setPlainText(f"Wave {self.wave + 1}")
            self.addItem(self.msg)

    def enemy_wave_setup(self):
        """ All enemies defeated, new wave created.
        Add two extra enemies at each higher wave. """

        # TODO p = subprocess.Popen(["aplay", "Sounds/NFF-alert.wav"])
        # p.communicate()
        print("sound1")
        self.wave += 1
        items = self.items()
        for item in items:
            if type(item).__name__ not in ('Player', 'Score', 'Bullet'):
                self.removeItem(item)
        self.msg = None
        self.explosions = []
        self.enemies = []
        self.bonuses = []
        self.enbullets = []
        for new_enemy in range(3 + int(self.wave * 1.5)):
            enemy = Enemy(self.width(), self.height())
            self.enemies.append(enemy)
            self.addItem(enemy)
        # time.sleep(1)

    def maybe_add_enbullets(self):
        """ Small chance to fire a bullet from each enemy """

        for enemy in self.enemies:
            if random.randint(0, 1000) < 5:
                self.add_enbullet(enemy)
            # Was 15 but too many bullets
            if enemy.name == "Mother UFO" and random.randint(0, 1000) < 10:
                self.add_enbullet(enemy)

    def add_enbullet(self, enemy):
        """ Non-directional bullet fired from most enemies. """

        color = "2"
        if enemy.name == "Big mother":
            color = "3"
        if enemy.name != "Mother UFO":
            bullet = EnemyBullet(enemy.x() + enemy.pixmap().width() / 2, enemy.y(), color)
            self.enbullets.append(bullet)
            self.addItem(bullet)
        else:
            bullet = EnemyDirectedBullet(enemy.x() + enemy.pixmap().width() / 2, enemy.y(), self.player.x(),
                                         self.player.y())
            self.enbullets.append(bullet)
            self.addItem(bullet)

    def end_of_game(self):
        """ Finish game. Show end credit. """

        time.sleep(1)
        msg = "GAME OVER\n"
        if len(self.enemies) == 0:
            msg += "You Won"
        else:
            msg += "You Lost"
        msg += "\nPress n for new game"
        self.msg = FadeMessage()
        self.msg.setPlainText(msg)
        self.addItem(self.msg)

    def cleanup_items(self):
        """ Remove expired enBullets, Enemies and Explosions from the scene and lists. """

        items = self.items()
        # TODO use isinstance
        for item in items:
            if type(item).__name__ == "Explosion" and item.counter == 0:
                self.removeItem(item)
            if type(item).__name__ == "Enemy" and item.hp == 0:
                self.removeItem(item)
            if type(item).__name__ == "EnemyBullet" and item.active is False:
                self.removeItem(item)
            if type(item).__name__ == "BonusItem" and item.active is False:
                self.removeItem(item)
            if type(item).__name__ == "Message" and item.frames < 0:
                self.removeItem(item)
                self.msg = None
        tmp = []
        for explosion in self.explosions:
            if explosion.counter > 0:
                tmp.append(explosion)
        self.explosions = tmp
        tmp = []
        for enemy in self.enemies:
            if enemy.hp > 0:
                tmp.append(enemy)
        self.enemies = tmp
        tmp = []
        for bonus in self.bonuses:
            if bonus.active:
                tmp.append(bonus)
        self.bonuses = tmp
        tmp = []
        for bullet in self.enbullets:
            if bullet.active:
                tmp.append(bullet)
        self.enbullets = tmp


class FadeMessage(QGraphicsTextItem):
    """ Text is set using setPlainText method. """

    frames = 255

    def init(self, parent=None):
        super(QGraphicsTextItem).__init__(parent)

        self.setPlainText("")
        self.setFont(QFont("Robotica", 40))
        self.setDefaultTextColor(QColor(255, 255, 0))
        self.setPos(200, 300)
        self.frames = 255

    def game_update(self):
        self.frames -= 1
        alpha = self.frames
        if alpha < 0:
            alpha = 0
        self.setFont(QFont("Robotica", 40))
        self.setDefaultTextColor(QColor(255, 255, 0, alpha))
        self.setPos(200, 300)


class Score(QGraphicsTextItem):

    def init(self, parent=None):
        QGraphicsTextItem.__init__(self, parent)

        print("Score 0")
        self.setPlainText("Wave: 0 Score: 0")
        self.setFont(QFont("Robotica", 15))
        self.setDefaultTextColor(QColor(255, 255, 0))
        self.setPos(10, 670)
        print("Score 1")

    def game_update(self, wave, score):
        self.setPlainText(f"Wave: {wave} Score: {score}")
        self.setFont(QFont("Robotica", 20))
        self.setDefaultTextColor(QColor(255, 255, 0))
        self.setPos(10, 670)


class Explosion(QGraphicsPixmapItem):
    """ Uses explosions images. """

    def __init__(self, x, y, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        # Load image frames
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

        self.frames = EXPLOSION_FRAMES
        if self.counter > 0:
            self.counter += 0.4
        if self.counter > 15:
            self.counter = 0
            return
        self.setPixmap(self.explosion_pics[int(self.counter)])


class Enemy(QGraphicsPixmapItem):
    """ Currently four different types. """

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
        if 30 <= entype < 55:
            self.name = "Lots a tentacles"
            self.dy = 0.15
            self.dx = 1.9 + random.randint(0, 4) / 10
            self.hp = 2
            self.score = 20
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir5.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir7a.png"))
        if 55 <= entype < 60:
            self.name = "Big mother"
            self.hp = 3
            self.dy = 0.19
            self.dx = 1
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir4.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir3.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir5.png"))
            self.pic.append(QPixmap("Images/Spaceships-Drakir2/Spaceship-Drakir3.png"))
            self.score = 30
        if 60 <= entype < 90:
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

        # Randomise dx direction
        d = random.randint(0, 1)
        if d == 0:
            self.dx = -1 * self.dx

        x = en_x
        if x < 0:
            x = random.randint(10, self.scr_w - self.pixmap().width() - 10)
        self.setPos(x, y)

    def game_update(self):

        if self.x() + self.dx < 0:
            self.dx = -1 * self.dx
        if self.x() + self.dx + self.pixmap().width() + 10 > self.scr_w:
            self.dx = -1 * self.dx
        self.counter += 0.05
        if self.counter >= len(self.pic):
            self.counter = 0
        self.setPixmap(self.pic[int(self.counter)])
        self.setPos(self.x() + self.dx, self.y() + self.dy)


class EnemyDirectedBullet(QGraphicsPixmapItem):
    """ Used by Mother UFO. """

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
        if -30 <= x_diff <= 50:
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
        self.frames = 180  # Enemy_bullet_frames

    def game_update(self):
        """ Could not get QSound or QSoundEffect to work, using subprocess. """

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
        self.setPixmap(QPixmap(f"Images/bolt{color}.png"))
        self.frames = 0
        self.x = x - ENEMY_BULLET_X_OFFSET
        self.y = y
        self.setVisible(True)
        self.active = True
        self.setPos(self.x, self.y)
        self.frames = 180  # Enemy_bullet_frames
        self.bullet_speed = 4

    def game_update(self):
        """ Could not get QSound or QSoundEffect to work, using subprocess. """

        if self.active:
            self.y += self.bullet_speed
            self.setPos(self.x, self.y)
            self.frames -= 1
            if self.frames <= 0:
                self.active = False
                self.setVisible(False)
                self.setPos(0, -100)


class BonusItem(QGraphicsPixmapItem):
    """ Various types of Item. """

    def __init__(self, scr_w, scr_h, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)

        self.pen = QPen(Qt.GlobalColor.blue, 3, Qt.PenStyle.SolidLine)
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
        self.frames = 900  # For ring protection and others
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
            self.pic.append(
                QPixmap("Images/PunkRobot/punkrobot0.png").scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio,
                                                                  Qt.TransformationMode.FastTransformation))
            self.pic.append(
                QPixmap("Images/PunkRobot/punkrobot1.png").scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio,
                                                                  Qt.TransformationMode.FastTransformation))
        if i == 3:
            self.name = "Alien transport"
            self.hp = 1
            self.score = 0
            self.pic.append(QPixmap("Images/UFO2a.png"))
            self.pic.append(QPixmap("Images/UFO2b.png"))
            self.pic.append(QPixmap("Images/UFO2c.png"))

        self.setPixmap(self.pic[0])
        # x = -50  # random.randint(10, self.scr_w - self.pixmap().width())
        y = random.randint(60, 250)
        self.setPos(x, y)

        # Flare
        self.flare = QPixmap("Images/flare_1.png")
        self.flareoffsets = [self.flare.width() / 2, self.flare.height() / 2]
        self.flarereducer = 0.9  # Percent reduction per frame of original pixmap
        self.flarereduction = 100  # Percentage of original pixmap

        self.shield0 = QPixmap("Images/ring0.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                                          Qt.TransformationMode.FastTransformation)
        self.shield1 = QPixmap("Images/ring1.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                                          Qt.TransformationMode.FastTransformation)
        self.shield2 = QPixmap("Images/ring2.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                                          Qt.TransformationMode.FastTransformation)

        self.slowed = []
        for i in range(1, 10):
            self.slowed.append(QPixmap("Images/slowed/slow" + str(i) + ".png"))
        for i in range(9, 0, -1):
            self.slowed.append(QPixmap("Images/slowed/slow" + str(i) + ".png"))

    def game_update(self):

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
            # windows replace aplay with start
            # TODO subprocess.Popen(["aplay", "Sounds/NFF-alien-02.wav"])

        if self.name == "flare":
            if self.effect_pic_set is False:
                self.setPixmap(self.flare)
                self.effect_pic_set = True
                # windows replace aplay with start
                # TODO subprocess.Popen(["aplay", "Sounds/NFF-glittering.wav"])
            self.setPos(self.x() - self.flareoffsets[0], self.y() - self.flareoffsets[1])
            self.flareoffsets = [0, 0]  # Initial offset to position flare over original pixmap
            # Resize gradually
            self.flarereduction -= self.flarereducer
            if self.flarereduction < 5:
                self.active = False
                return

            w = self.flarereduction / 100 * self.flare.width()
            h = self.flarereduction / 100 * self.flare.height()
            self.flareoffsets[0] = self.flare.width() - w
            self.flareoffsets[1] = self.flare.height() - h
            self.setPixmap(self.flare.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
            self.setPos(self.x() + self.flareoffsets[0], self.y() + self.flareoffsets[1])

        if self.name == "shield":
            if TEST: print("BonusItem. game_update shield item")
            if self.effect_pic_set is False:
                self.setPixmap(self.shield0)
                self.effect_pic_set = True
                # Windows replace aplay with start
                # TODO subprocess.Popen(["aplay", "Sounds/NFF-ufo.wav"])
            if TEST: print("BonusItem. game_update shield effects enacted")


        if self.name == "slowed":
            if self.effect_pic_set is False:
                self.effect_pic_set = True
                self.setPixmap(self.slowed[0])
                self.setPos(self.x() - self.slowed[0].width() / 2, self.y() - self.slowed[0].height() / 2)
                self.counter = 0
                # Windows replace aplay with start
                # TODO subprocess.Popen(["aplay", "Sounds/NFF-shooting-star-02.wav"])
                return
            self.counter += 1
            if self.counter >= len(self.slowed):
                self.active = False
                return
            self.setPixmap(self.slowed[int(self.counter)])

    def update_to_player_pos(self, player):
        """ Only for shield effect. """

        self.frames -= 1
        # print(self.frames)
        if self.frames < 1:
            self.active = False
        self.setPos(player.x() - 25, player.y() - 25)  # magic number offsets
        if 500 > self.frames >= 200:
            self.setPixmap(self.shield1)
        if self.frames < 200:
            self.setPixmap(self.shield2)


class Player(QGraphicsPixmapItem):
    """ Set up player half way across and almost on bottom of scene. """

    def __init__(self, scr_w, scr_h, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        self.setPixmap(QPixmap("Images/DurrrSpaceShip_50.png"))
        self.scr_w = scr_w
        self.scr_h = scr_h
        self.setPos((self.scr_w - self.pixmap().width()) / 2,
                    self.scr_h - self.pixmap().height() - 10)

    def game_update(self, keys_pressed):
        """ Left is A or Left arrow, Right is D or Right Arrow, Space to fire. """

        dx = 0
        dy = 0
        if Qt.Key.Key_A in keys_pressed or Qt.Key.Key_Left in keys_pressed:
            dx -= PLAYER_SPEED
            if self.x() - dx < 0:
                dx = 0
        if Qt.Key.Key_D in keys_pressed or Qt.Key.Key_Right in keys_pressed:
            dx += PLAYER_SPEED
            if self.x() + dx > self.scr_w - self.pixmap().width():
                dx = 0
        if Qt.Key.Key_W in keys_pressed or Qt.Key.Key_Up in keys_pressed:
            dy -= PLAYER_SPEED
            if self.y() + dy < 1:
                dy = 0
        if Qt.Key.Key_S in keys_pressed or Qt.Key.Key_Down in keys_pressed:
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
        """ Could not get QSound or QSoundEffect to work, using subprocess. """

        if not self.active:
            if Qt.Key.Key_Space in keys_pressed:
                # Windows replace aplay with start
                # TODO subprocess.Popen(["aplay", "Sounds/tir.wav"])
                self.setVisible(True)
                self.active = True
                self.setPos(player.x() + player.pixmap().width() / 2 - self.offset_x, player.y() + self.offset_y)
                self.frames = BULLET_FRAMES
        else:
            self.setPos(self.x(), self.y() - BULLET_SPEED)
            self.frames -= 1
            if self.frames <= 0 or self.y() < -30:
                self.active = False
                self.setVisible(False)
                self.setPos(self.scr_w, self.scr_h)

    def hit_enemy(self, enemy):
        """ Called on collision detect.
        :param: enemy : Class """

        self.active = False
        self.setVisible(False)
        self.setPos(self.scr_w, self.scr_h)
        enemy.hp -= 1


class MainWindow(QMainWindow):
    """ Main app window. """

    def __init__(self, screenwidth, screenheight):

        self.screenwidth = screenwidth
        self.screenheight = screenheight
        self.scene = None
        self.view_w = 0
        self.view_h = 0
        self.game_started = False

        # Set up user interface from ui_main.py file
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setStyleSheet('background-image:url(Images/prestige-COD.jpg); background-position: tiled;')
        size = self.ui.graphicsView.size()
        self.view_w = size.width()
        self.view_h = size.height()
        self.ui.graphicsView.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.ui.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ui.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        bg = QPixmap('Images/bg1.jpg')
        bg = bg.scaled(size.width(), size.height())
        self.ui.graphicsView.setBackgroundBrush(QBrush(bg))
        self.ui.graphicsView.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.ui.graphicsView.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.ui.graphicsView.hide()
        # self.ui.label.setText("")
        self.show()
        if TEST: print("Main window init")

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_N:
            self.new_game()
        if event.key() == Qt.Key.Key_Q:
            self.exit_app()

    def new_game(self):

        self.ui.graphicsView.show()
        self.ui.label.hide()
        self.ui.graphicsView.setFocus()
        self.game_started = True
        # Add scene after window is displayed to get graphics view size
        self.scene = Scene(self.view_w, self.view_h)
        if self.scene.game_over is True:
            print("Game over")
        # self.scene.setSceneRect(0, 0, self.view_w, self.view_h)
        self.ui.graphicsView.setScene(self.scene)
        self.ui.graphicsView.show()
        if TEST: print("MainWindow.new_game")

    def exit_app(self):

        QApplication.quit()
        sys.exit(0)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont("GUI/Robotica.ttf")
    with open("GUI/stylesheet", "r") as fh:
        app.setStyleSheet(fh.read())
    screen_resolution = app.primaryScreen().geometry()
    width, height = screen_resolution.width(), screen_resolution.height()
    if TEST: print("Main 1")
    window = MainWindow(width, height)
    if TEST: print("Main 2")
    sys.exit(app.exec())
