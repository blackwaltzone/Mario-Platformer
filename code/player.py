# ---------------------------------------------
# 
# player.py
# 
# contains the player class
#
# Dustin Heyden
# Feb 13, 2024
#
# ---------------------------------------------

# imports
from settings import *
from timer import Timer
from os.path import join


# player class
class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, semicollision_sprites, frames):
        # general setup
        super().__init__(groups)
        self.z = Z_LAYERS['main']

        # image
        self.frames, self.frame_index = frames, 0
        self.state, self.facing_right = 'idle', True
        self.image = self.frames[self.state][self.frame_index]

        # rects
        self.rect = self.image.get_frect(topleft=pos)
        self.hitbox = self.rect.inflate(-76, -36)
        self.old_rect = self.hitbox.copy()

        # movement
        self.direction = vector()
        self.speed = 200
        self.gravity = 1300
        self.jump = False
        self.jump_height = 900
        self.attacking = False

        # collision
        self.collision_sprites = collision_sprites
        self.semicollision_sprites = semicollision_sprites
        self.on_surface = {'floor': False, 'left': False, 'right': False}
        
        self.platform = None

        # Timer
        self.timers = {
                'wall jump': Timer(400),
                'wall slide block': Timer(250),
                'platform skip': Timer(100),
                'attack block': Timer(500),
        }


    def attack(self):
        if not self.timers['attack block'].active:
            self.attacking = True
            self.frame_index = 0
            self.timers['attack block'].activate()


    # handle player input
    def input(self):
        keys = pygame.key.get_pressed()
        input_vector = vector(0,0)

        if not self.timers['wall jump'].active:

            if keys[pygame.K_RIGHT]:
                input_vector.x += 1
                self.facing_right = True
            
            if keys[pygame.K_LEFT]:
                input_vector.x -= 1
                self.facing_right = False
            
            if keys[pygame.K_DOWN]:
                self.timers['platform skip'].activate()

            if keys[pygame.K_x ]:
                self.attack()

            self.direction.x = input_vector.normalize().x if input_vector else 0

        # jumping
        if keys[pygame.K_SPACE]:
            self.jump = True
            self.timers['wall jump'].activate()


    # movement logic
    def move(self, dt):
        # horizontal
        self.hitbox.x += self.direction.x * self.speed * dt
        self.collision('horizontal')

        # vertical
        if not self.on_surface['floor'] \
            and any((self.on_surface['left'], self.on_surface['right'])) \
            and not self.timers['wall slide block'].active:
            self.direction.y = 0
            self.hitbox.y += self.gravity / 10 * dt
        else:
            self.direction.y += self.gravity / 2 * dt
            self.hitbox.y += self.direction.y * dt
            self.direction.y += self.gravity / 2 * dt

        # jump
        if self.jump:
            if self.on_surface['floor']:
                self.direction.y = -self.jump_height
                self.timers['wall slide block'].activate()
                # fix jumping glitch (player won't jump on a vertical platform)
                self.hitbox.bottom -= 1
            elif any((self.on_surface['left'], self.on_surface['right'])) \
                and not self.timers['wall slide block'].active:
                self.direction.y = -self.jump_height
                self.direction.x = 1 if self.on_surface['left'] else -1
            self.jump = False

        self.collision('vertical')
        self.semi_collision()

        # set center of image to center of hitbox
        self.rect.center = self.hitbox.center


    def platform_move(self, dt):
        if self.platform:
            self.hitbox.topleft += self.platform.direction * self.platform.speed * dt


    def check_contact(self):
        floor_rect = pygame.Rect(self.hitbox.bottomleft, (self.hitbox.width, 2))
        right_rect = pygame.Rect(self.hitbox.topright +
            vector(0, self.hitbox.height/4), (2, self.hitbox.height / 2))
        left_rect  = pygame.Rect(self.hitbox.topleft +
            vector(-2, self.hitbox.height/4), (2, self.hitbox.height / 2))

        collide_rects = [sprite.rect for sprite in self.collision_sprites]
        semicollide_rects = [sprite.rect for sprite in self.semicollision_sprites]

        # collisions
        self.on_surface['floor'] = True if floor_rect.collidelist(collide_rects) >= 0 \
            or floor_rect.collidelist(semicollide_rects) >= 0 \
            and self.direction.y >= 0 else False
        self.on_surface['right'] = True if right_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['left'] = True if left_rect.collidelist(collide_rects) >= 0 else False

        # standing on platform
        self.platform = None
        sprites = self.collision_sprites.sprites() + self.semicollision_sprites.sprites()
        for sprite in [sprite for sprite in sprites if hasattr(sprite, 'moving')]:
            if sprite.rect.colliderect(floor_rect):
                self.platform = sprite


    # handle collisions
    def collision(self, axis):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox):
                if axis == 'horizontal':
                    # left
                    if self.hitbox.left <= sprite.rect.right and \
                        int(self.old_rect.left) >= int(sprite.old_rect.right):
                        self.hitbox.left = sprite.rect.right
                    # right
                    if self.hitbox.right >= sprite.rect.left and \
                        int(self.old_rect.right) <= int(sprite.old_rect.left):
                        self.hitbox.right = sprite.rect.left
                elif axis == 'vertical':
                    # top
                    if self.hitbox.top <= sprite.rect.bottom and \
                        int(self.old_rect.top) >= int(sprite.old_rect.bottom):
                        self.hitbox.top = sprite.rect.bottom
                        # don't want player to get stuck in moving platform when
                        # jumping underneath
                        if hasattr(sprite, 'moving'):
                            self.hitbox.top += 6
                    # bottom
                    if self.hitbox.bottom >= sprite.rect.top and \
                        int(self.old_rect.bottom) <= int(sprite.old_rect.top):
                        self.hitbox.bottom = sprite.rect.top
                    self.direction.y = 0

    
    # handle semi-permiable platforms
    def semi_collision(self):
        if not self.timers['platform skip'].active:
            for sprite in self.semicollision_sprites:
                if sprite.rect.colliderect(self.hitbox):
                    # only care about bottom collision
                    if self.hitbox.bottom >= sprite.rect.top and \
                        int(self.old_rect.bottom) <= sprite.old_rect.top:
                        self.hitbox.bottom = sprite.rect.top
                        if self.direction.y >= 0:
                            self.direction.y = 0


    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt

        if self.state == 'attack' and self.frame_index >= len(self.frames[self.state]):
            self.state = 'idle'

        self.image = self.frames[self.state][int(self.frame_index % len(self.frames[self.state]))]
        self.image = self.image if self.facing_right else pygame.transform.flip(self.image, True, False)

        if self.attacking and self.frame_index > len(self.frames[self.state]):
            self.attacking = False


    def get_state(self):
        if self.on_surface['floor']:
            if self.attacking:
                self.state= 'attack'
            else:
                self.state = 'idle' if self.direction.x == 0 else 'run'
        else:
            if self.attacking:
                self.state = 'air_attack'
            else:
                if any((self.on_surface['left'], self.on_surface['right'])):
                    self.state = 'wall'
                else:
                    self.state = 'jump' if self.direction.y < 0 else 'fall'


    def update_timers(self):
        for timer in self.timers.values():
            timer.update()


    def update(self, dt):
        self.old_rect = self.hitbox.copy()
        self.update_timers()
        self.input()
        self.move(dt)
        self.platform_move(dt)
        self.check_contact()

        self.get_state()
        self.animate(dt)
