#------------------------------------------------
#
# enemies.py
#
# enemies class and controllers
# handles movement, ai
#
# Dustin Heyden
# April 01, 2024
#
#------------------------------------------------

from settings import *
from random import choice
from timer import Timer

class Tooth(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, collision_sprites):
        super().__init__(groups)
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(topleft = pos)
        self.z = Z_LAYERS['main']

        self.direction = choice((-1, 1))
        self.collision_rects = [sprite.rect for sprite in collision_sprites]
        self.speed = 200


    def update(self, dt):

        # animate
        self.frame_index += ANIMATION_SPEED * dt
        self.image = self.frames[int(self.frame_index % len(self.frames))]

        # change direction
        if self.direction < 0:
            self.image = pygame.transform.flip(self.image, True, False)

        # move
        self.rect.x += self.direction * self.speed * dt

        # reverse direction
        floor_rect_right = pygame.FRect(self.rect.bottomright, (1,1))
        floor_rect_left = pygame.FRect(self.rect.bottomleft, (-1,1))
        wall_rect = pygaem.FRect(
            topleft =self.rect.topleft + vector(-1, 0), 
            size = (self.rect.width + 2, 1))

        if floor_rect_right.collidelist(self.collision_rects) > 0 and\
                self.direction > 0 or\
                floor_rect_left.collidelist(self.collision_rects) < 0 and\
                self.direction < 0 or\
                wall_rect.collidelist(self.collision_rects) != -1:
            self.direction *= -1



class Shell(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, reverse, player, create_pearl):
        super().__init__(groups)

        self.frame_index = 0
        self.state = 'idle'
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()
        self.z = Z_LAYERS['main']
        self.player = player
        self.shoot_timer = Timer(3000)
        self.has_fired = False
        self.create_pearl = create_pearl

        if reverse:
            # flip all frames in frames
            self.frames = {}
            for key, surface in frames.items():
                self.frames[key] = [pygame.transform.flip(surf, True, False) for s in surfs]
            self.bullet_dir = -1
        else:
            self.frames = frames
            self.bullet_dir = 1


    def state_management(self):
        player_pos = vector(self.player.hitbox_rect.center)
        shell_pos = vector(self.rect.center)
        player_near = shell_pos.distance_to(player_pos) < 500
        
        if self.bullet_dir > 0:
            player_front = shell_pos.x < player_pos.x
        else:
            player_front = shell_pos.x > player_pos.x
        
        player_level = abs(shell_pos.y - player_pos.y) < 30

        if player_near and\
                player_front and\
                player_level and\
                not self.shoot_timer.active:
            self.state = 'fire'
            self.frame_index = 0
            self.shoot_timer.activate()


    def update(self, dt):
        self.shoot_timer.update()
        self.state_management()

        # animation/attack
        self.frame_index += ANIMATION_SPEED * dt

        if self.frame_index < len(self.frames[self.state]):
            self.image = self.frames[self.state][int(self.frame_index)]

            # fire
            if self.state == 'fire' and\
                    int(self.frame_index) == 3 and\
                    not self.has_fired:
                self.create_pearl(
                    pos = self.rect.center,
                    dir = self.bullet_dir)
                self.has_fired = True
        else:
            self.frame_index = 0

            if self.state == 'fire':
                self.state = 'idle'
                self.has_fired = False



class Pearl(pygame.sprite.Sprite):
    def __init__(self, pos, groups, surface, dir, speed):
        self.pearl = True

        super().__init__(groups)

        self.image = surface
        self.rect = self.image.get_frect(center = pos + vector(50*dir,0))
        self.direction = dir
        self.speed = speed
        self.z = Z_LAYERS['main']
        self.timers = {'lifetime': Timer(5000)}
        self.timers['lifetime'].activate()


    def update(self, dt):
        for timer in self.timers.values():
            timer.update()

        self.rect.x += self.direction * self.speed * dt

        if not self.timers['lifetime'].active:
            self.kill()
                print('shoot pearl')
