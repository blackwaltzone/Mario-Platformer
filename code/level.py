# --------------------------------
#
# level.py
#
# Dustin Heyden
# Feb 12, 2024
#
# --------------------------------

# imports
from settings import *
from sprites import Sprite, AnimatedSprite, MovingSprite, Spike
from player import Player
from groups import AllSprites
from random import uniform
from enemies import Tooth, Shell, Pearl

class Level:
    def __init__(self, tmx_map, level_frames):
        self.display_surface = pygame.display.get_surface()

        # groups
        self.all_sprites = AllSprites() 
        self.collision_sprites = pygame.sprite.Group()
        self.semicollision_sprites = pygame.sprite.Group()
        self.damage_sprites = pygame.sprite.Group()
        self.tooth_sprites = pygame.sprite.Group()
        self.pearl_sprites = pygame.sprite.Group()
        
        self.setup(tmx_map, level_frames)

        # frames
        self.pearl_surface = level_frames['pearl']

        
    def setup(self, tmx_map, level_frames):
        # Terrain tiles
        # need .tiles() since they're tiles, not objects
        for layer in ['BG', 'Terrain', 'FG', 'Platforms']:
            for x, y, surface in tmx_map.get_layer_by_name(layer).tiles():
                groups = [self.all_sprites]
                
                if layer == 'Terrain': groups.append(self.collision_sprites)
                if layer == 'Platforms': groups.append(self.semicollision_sprites)

                match layer:
                    case 'BG': z = Z_LAYERS['bg tiles']
                    case 'FG': z = Z_LAYERS['fg']
                    case _: z = Z_LAYERS['main']

                Sprite((x*TILE_SIZE,y*TILE_SIZE), surface, groups, z)

        # bg details
        for obj in tmx_map.get_layer_by_name('BG details'):
            if obj.name == 'static':
                Sprite((obj.x, obj.y), obj.image, self.all_sprites, z = Z_LAYERS['bg tiles'])
            else:
                AnimatedSprite((obj.x, obj.y), level_frames[obj.name], self.all_sprites, Z_LAYERS['bg tiles'])
                if obj.name == 'candle':
                    AnimatedSprite((obj.x, obj.y) + vector(-20, 20), level_frames['candle_light'], self.all_sprites, Z_LAYERS['bg tiles'])


        # objects
        # don't need .tiles() since they're objects
        for obj in tmx_map.get_layer_by_name('Objects'):
            if obj.name == 'player':
                # obj already has pixel pos, don't need to multiply by tilesize
                self.player = Player(
                    pos = (obj.x, obj.y),
                    groups = self.all_sprites,
                    collision_sprites = self.collision_sprites,
                    semicollision_sprites = self.semicollision_sprites,
                    frames = level_frames['player'])
            else:
                if obj.name in ('barrel', 'crate'):
                    Sprite(
                        (obj.x, obj.y),
                        obj.image,
                        (self.all_sprites, self.collision_sprites))
                else:
                    # frames
                    if not 'palm' in obj.name:
                        frames = level_frames[obj.name]
                    else:
                        frames = level_frames['palms'][obj.name]

                    if obj.name == 'floor_spike' and obj.properties['inverted']:
                        # flip vertically (sprite, horizontal, vertical)
                        frames = [pygame.transform.flip(frame, False, True) for frame in frames]
                    
                    # groups
                    groups = [self.all_sprites]
                    if obj.name in('palm_small', 'palm_large'):
                        groups.append(self.semicollision_sprites)
                    if obj.name in ('saw', 'floor_spike'):
                        groups.append(self.damage_sprites)

                    # z index
                    if not 'bg' in obj.name:
                        z = Z_LAYERS['main']
                    else:
                        z = Z_LAYERS['bg details']

                    # animation speed
                    if not 'palm' in obj.name:
                        animation_speed = ANIMATION_SPEED
                    else:
                        animation_speed = ANIMATION_SPEED + uniform(-1, 1) 

                    AnimatedSprite((obj.x, obj.y), frames, groups, z, animation_speed)

        # moving objects
        for obj in tmx_map.get_layer_by_name("Moving Objects"):
            if obj.name == 'spike':
                Spike(
                    pos = (obj.x + obj.width / 2, obj.y + obj.height / 2),
                    surface = level_frames['spike'],
                    radius = obj.properties['radius'],
                    speed = obj.properties['speed'],
                    start = obj.properties['start_angle'],
                    end = obj.properties['end_angle'],
                    groups = (self.all_sprites, self.damage_sprites))

                for radius in range(0, obj.properties['radius'], 20):
                    Spike(
                        pos = (obj.x + obj.width / 2, obj.y + obj.height / 2),
                        surface = level_frames['spike_chain'],
                        radius = radius,
                        speed = obj.properties['speed'],
                        start = obj.properties['start_angle'],
                        end = obj.properties['end_angle'],
                        groups = self.all_sprites,
                        z = Z_LAYERS['bg details'])
                
            else:
                frames = level_frames[obj.name]
                if obj.properties['platform']:
                    groups = (self.all_sprites, self.semicollision_sprites)
                else:
                    groups = (self.all_sprites, self.damage_sprites)

                # horizontal movement
                if obj.width > obj.height:  
                    move_dir = 'x'
                    start_pos = (obj.x, obj.y + obj.height / 2)
                    end_pos = (obj.x + obj.width, obj.y + obj.height / 2)
                # vertical movement
                else:
                    move_dir = 'y'
                    start_pos = (obj.x + obj.width / 2, obj.y)
                    end_pos = (obj.x + obj.width / 2, obj.y + obj.height)
                speed = obj.properties['speed']

                MovingSprite(
                    frames,
                    groups, 
                    start_pos, 
                    end_pos, 
                    move_dir, 
                    speed,
                    obj.properties['flip'])

                # draw lines for saw paths
                if obj.name == 'saw':
                    if move_dir == 'x':
                        y = start_pos[1] - level_frames['saw_chain'].get_height() / 2
                        left, right = int(start_pos[0]), int(end_pos[0])
                        for x in range(left, right, 20):     # 20 = pixels
                            Sprite(
                                (x, y),
                                level_frames['saw_chain'],
                                self.all_sprites,
                                Z_LAYERS['bg details'])
                    else:
                        x = start_pos[0] - level_frames['saw_chain'].get_width() / 2
                        top, bottom = int(start_pos[1]), int(end_pos[1])
                        for y in range(top, bottom, 20):
                            Sprite(
                                (x, y),
                                level_frames['saw_chain'],
                                self.all_sprites,
                                Z_LAYERS['bg details'])

        # enemies
        for obj in tmx_map.get_layer_by_name('Enemies'):
            if obj.name == 'tooth':
                Tooth(
                    pos = (obj.x, obj.y),
                    frames = level_frames['tooth'],
                    groups = (self.all_sprites, self.damage_sprites, self.tooth_sprites),
                    collision_sprites = self.collision_sprites)
            if obj.name == 'shell':
                Shell(
                    pos = (obj.x, obj.y),
                    frames = level_frames['shell'],
                    groups = (self.all_sprites, self.collision_sprites),
                    reverse = obj.properties['reverse'],
                    player = self.player,)

    
    def create_pearl(self, pos, direction):
        Pearl(
            pos = pos,
            groups = (self.all_sprites, self.damage_sprites, self.pearl_sprites),
            frames = self.pearl_surface,
            dir = direction,
            speed = 150)


    def pearl_collision(self):

        # hit a piece of the level
        for sprite in self.collision_sprites:
            pygame.sprite.spritecollide(sprite, self.pearl_sprites, True)

    def hit_collision(self):
        for sprite in self.damage_sprites:
            if sprite.rect.colliderect(self.player.hitbox):
                if hasattr(sprite, 'pearl'):
                    sprite.kill()                


    def run(self, dt):
        self.display_surface.fill('black')

        self.all_sprites.update(dt)
        self.pearl_collision()
        self.hit_collision()

        self.all_sprites.draw(self.player.hitbox.center)
