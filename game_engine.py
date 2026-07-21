import os
import pygame
import sys

# Globals package imports
from globals.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, ZOOM, MAP_WIDTH, MAP_HEIGHT,
    FLOOR_COLOR, CHEST_COLOR, PLAYER_COLOR, TEXT_COLOR
)
from globals.camera import Camera
from globals.player_controller import PlayerController
from globals.player import PlayerStats
from globals.minimap import draw_minimap
from globals.cursor import CustomCursor
from globals.fog import FogOfWar

# Events package imports
from events.map_loader import load_map, draw_dungeon, TILE_SIZE
from events.main_menu import MainMenu
from events.level_select import LevelSelectMenu
from events.loading import LoadingScreen
from events.tab_menu import TabMenu
from events.level_title import LevelTitleBanner
from events.controls_info import ControlsInfoOverlay
from events.combat.slime_combat import SlimeCombatHandler

# Weapons directory imports
from weapons.sword.sword import Sword

# Assets package imports
from assets.sign import DialogModal
from assets.damage_text import DamageTextManager


class GameEngine:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()

        self.game_state = "MAIN_MENU"

        # UI & Camera Systems
        self.main_menu = MainMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.level_select = LevelSelectMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.loading_screen = LoadingScreen(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.tab_menu = TabMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.title_banner = LevelTitleBanner(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.controls_overlay = ControlsInfoOverlay(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.custom_cursor = CustomCursor()
        self.camera = Camera()
        self.damage_text_mgr = DamageTextManager()

        # Gameplay Entities
        self.walls, self.torches, self.signs, self.doors, self.keys, self.floor_tiles = [], [], [], [], [], []
        self.slimes = []
        self.player_rect = None
        self.chest_rect = None
        self.map_name = ""
        self.selected_map_file = None
        self.map_w = MAP_WIDTH
        self.map_h = MAP_HEIGHT
        self.world_surface = pygame.Surface((self.map_w, self.map_h))
        self.controller = None

        self.sword = Sword()
        self.player_stats = PlayerStats()
        self.fog = FogOfWar(vision_radius=180)
        self.modal = DialogModal()

        self.font = pygame.font.SysFont("Arial", 20)
        self.small_font = pygame.font.SysFont("Arial", 12)

        self.game_won = False
        self.show_minimap = True
        self.minimap_alpha = 220.0
        self.target_alpha = 220.0

        self.reset_game()

    def reset_game(self, map_file=None):
        (
            walls, torches, signs, doors, keys, slimes, floor_tiles,
            player_start, exit_start, file_name,
            map_w, map_h
        ) = load_map("maps", target_file=map_file)

        self.map_w = map_w
        self.map_h = map_h
        self.selected_map_file = file_name + ".txt"

        self.world_surface = pygame.Surface((self.map_w, self.map_h))

        player_size = 12
        offset = (TILE_SIZE - player_size) // 2
        start_x = player_start[0] * TILE_SIZE + offset
        start_y = player_start[1] * TILE_SIZE + offset

        self.player_rect = pygame.Rect(start_x, start_y, player_size, player_size)
        self.controller = PlayerController(start_x, start_y)

        exit_x = exit_start[0] * TILE_SIZE + 6
        exit_y = exit_start[1] * TILE_SIZE + 6
        self.chest_rect = pygame.Rect(exit_x, exit_y, 28, 28)

        self.walls, self.torches, self.signs, self.doors, self.keys, self.slimes, self.floor_tiles = (
            walls, torches, signs, doors, keys, slimes, floor_tiles
        )
        self.map_name = file_name
        self.damage_text_mgr.clear()

    def get_next_level_file(self):
        if not os.path.exists("maps"):
            return None
        maps = sorted([f for f in os.listdir("maps") if f.endswith(".txt")])
        if self.selected_map_file in maps:
            idx = maps.index(self.selected_map_file)
            if idx + 1 < len(maps):
                return maps[idx + 1]
        return None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.game_state == "MAIN_MENU":
                menu_action = self.main_menu.handle_event(event)
                if menu_action == "PLAY":
                    self.level_select.refresh_maps("maps")
                    self.game_state = "LEVEL_SELECT"
                elif menu_action == "QUIT":
                    return False

            elif self.game_state == "LEVEL_SELECT":
                selected = self.level_select.handle_event(event)
                if selected == "MAIN_MENU":
                    self.game_state = "MAIN_MENU"
                elif selected:
                    self.selected_map_file = selected
                    self.loading_screen.start("GENERATE")
                    self.game_state = "LOADING"

            elif self.game_state == "GAMEPLAY":
                if self.tab_menu.active:
                    action = self.tab_menu.handle_event(event)
                    if action == "RESET":
                        self.loading_screen.start("REGENERATE")
                        self.game_state = "LOADING"
                    elif action == "MAIN_MENU":
                        self.game_state = "MAIN_MENU"

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.modal.active:
                        mouse_world = self.camera.get_mouse_world()
                        if event.button == 1:
                            self.sword.start_press()
                        elif event.button == 3:
                            p_vec = pygame.Vector2(self.player_rect.centerx, self.player_rect.centery)
                            self.sword.trigger_parry(p_vec, mouse_world)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if not self.modal.active:
                        mouse_world = self.camera.get_mouse_world()
                        if event.button == 1:
                            p_vec = pygame.Vector2(self.player_rect.centerx, self.player_rect.centery)
                            self.sword.release_attack(p_vec, mouse_world, self.player_stats)
                        elif event.button == 3:
                            self.sword.release_parry()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        if self.modal.active:
                            self.modal.hide()
                        self.tab_menu.show() if not self.tab_menu.active else self.tab_menu.hide()

                    elif event.key == pygame.K_i:
                        self.controls_overlay.toggle()

                    elif event.key == pygame.K_e:
                        if self.modal.active:
                            self.modal.hide()
                        else:
                            p_pos = (self.player_rect.centerx, self.player_rect.centery)
                            
                            door_opened = False
                            for door in self.doors:
                                if door.check_proximity(p_pos):
                                    if door.try_open(self.player_stats.keys):
                                        door_opened = True
                                        break
                                    else:
                                        self.modal.show("This door is locked! You need a Key.")
                                        door_opened = True
                                        break
                            
                            if not door_opened:
                                for sign in self.signs:
                                    if sign.check_proximity(p_pos):
                                        self.modal.show(sign.text)
                                        break

                    elif event.key == pygame.K_ESCAPE:
                        if self.modal.active:
                            self.modal.hide()
                        elif self.tab_menu.active:
                            self.tab_menu.hide()
                        else:
                            self.tab_menu.show()

                    elif event.key == pygame.K_r:
                        if self.game_won:
                            next_lvl = self.get_next_level_file()
                            if next_lvl:
                                self.selected_map_file = next_lvl
                                self.loading_screen.start("GENERATE")
                                self.game_state = "LOADING"
                            else:
                                self.game_state = "MAIN_MENU"
                        else:
                            self.loading_screen.start("REGENERATE")
                            self.game_state = "LOADING"

                    elif event.key == pygame.K_m:
                        self.show_minimap = not self.show_minimap
                        self.target_alpha = 220.0 if self.show_minimap else 0.0

        return True

    def update(self):
        if self.game_state == "LOADING":
            self.loading_screen.update()
            if self.loading_screen.is_finished:
                self.reset_game(map_file=self.selected_map_file)
                self.sword = Sword()
                self.player_stats = PlayerStats()
                self.modal.hide()
                self.tab_menu.hide()
                self.game_won = False
                
                self.title_banner.trigger(area_name="Grimstone Fortress", level_name=self.map_name)
                self.game_state = "GAMEPLAY"

        elif self.game_state == "GAMEPLAY":
            self.camera.update(self.player_rect)
            mouse_world = self.camera.get_mouse_world()

            self.title_banner.update()
            self.controls_overlay.update()
            self.damage_text_mgr.update()
            self.minimap_alpha += (self.target_alpha - self.minimap_alpha) * 0.15
            self.player_stats.update()

            if not self.game_won and not self.modal.active and not self.tab_menu.active:
                for key in self.keys:
                    if not key.collected and self.player_rect.colliderect(key.rect):
                        key.collected = True
                        self.player_stats.add_key(key.key_id)

                closed_door_rects = [door.rect for door in self.doors if not door.is_open]
                active_obstacles = self.walls + closed_door_rects

                # Combat Handling with Player Knockback Support
                SlimeCombatHandler.process_slime_combat(
                    self.slimes, self.player_rect, self.sword, self.player_stats, active_obstacles, player_controller=self.controller
                )

                # Player Movement with Uniform Vector Normalization (Balanced WASD/Diagonals)
                if not self.sword.is_dashing:
                    keys = pygame.key.get_pressed()
                    raw_dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
                    raw_dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

                    move_dir = pygame.Vector2(raw_dx, raw_dy)
                    if move_dir.length() > 0:
                        move_dir = move_dir.normalize()

                    speed = self.player_stats.get_speed(self.sword.is_parrying)
                    self.controller.move_player_exact(
                        self.player_rect, 
                        move_dir.x * speed, 
                        move_dir.y * speed, 
                        active_obstacles
                    )

                self.sword.update(self.player_rect, mouse_world, self.controller.move_player_exact, active_obstacles)

                if self.player_rect.colliderect(self.chest_rect):
                    self.game_won = True

    def draw(self):
        if self.game_state == "MAIN_MENU":
            self.main_menu.draw(self.screen)

        elif self.game_state == "LEVEL_SELECT":
            self.level_select.draw(self.screen)

        elif self.game_state == "LOADING":
            self.loading_screen.draw(self.screen)

        elif self.game_state == "GAMEPLAY":
            mouse_world = self.camera.get_mouse_world()

            # Render World
            self.world_surface.fill(FLOOR_COLOR)
            draw_dungeon(
                self.world_surface, self.walls, self.torches, self.signs, 
                self.doors, self.keys, self.floor_tiles
            )
            pygame.draw.rect(self.world_surface, CHEST_COLOR, self.chest_rect, border_radius=4)
            
            # Render Slimes & Particles on World Surface (Line-of-Sight Gated)
            for slime in self.slimes:
                slime_center = (slime.rect.centerx, slime.rect.centery)
                
                is_visible = True
                if hasattr(self.fog, 'is_lit'):
                    is_visible = self.fog.is_lit(slime_center)
                elif hasattr(self.fog, 'is_visible'):
                    is_visible = self.fog.is_visible(slime_center)

                if is_visible:
                    slime.draw(self.world_surface)

            # Draw Player (Flash Red on Damage)
            player_flash = getattr(self.player_stats, 'flash_timer', 0) > 0
            player_color = (255, 60, 60) if player_flash else PLAYER_COLOR
            pygame.draw.rect(self.world_surface, player_color, self.player_rect, border_radius=2)

            self.sword.draw(self.world_surface, self.player_rect, mouse_world)
            self.fog.draw(self.world_surface, self.player_rect, self.walls, self.torches)

            # Camera Pass
            self.camera.render(self.screen, self.world_surface, self.map_w, self.map_h)

            # Crisp Overhead Enemy Text Pass
            cam_offset = (self.camera.cam_x, self.camera.cam_y)
            for slime in self.slimes:
                slime.draw_overhead_ui(
                    self.screen, 
                    camera_offset=cam_offset, 
                    zoom=ZOOM, 
                    fog=self.fog, 
                    player_rect=self.player_rect
                )

            # Crisp Animated Damage Numbers Pass
            self.damage_text_mgr.draw(self.screen, camera_offset=cam_offset, zoom=ZOOM)

            # Floating Prompts
            p_pos = (self.player_rect.centerx, self.player_rect.centery)
            if not self.modal.active and not self.tab_menu.active:
                prompt_drawn = False
                for door in self.doors:
                    if door.check_proximity(p_pos):
                        door.draw_prompt(self.screen, self.small_font, camera_offset=cam_offset, zoom=ZOOM)
                        prompt_drawn = True
                        break
                
                if not prompt_drawn:
                    for sign in self.signs:
                        if sign.check_proximity(p_pos):
                            sign.draw_prompt(self.screen, self.small_font, camera_offset=cam_offset, zoom=ZOOM)
                            break

            # HUD Header Text
            info_text = self.font.render(f"Map: {self.map_name} | [TAB] Pause Menu | [E] Interact", True, TEXT_COLOR)
            self.screen.blit(info_text, (20, 15))

            self.player_stats.draw_hud(self.screen, self.font)
            draw_minimap(self.screen, self.walls, self.player_rect, self.chest_rect, self.minimap_alpha, self.font)
            
            # Location Title Banner & Overlays
            self.title_banner.draw(self.screen)
            self.controls_overlay.draw(self.screen)
            
            # Middle-Right Animated Parry Cooldown Widget
            self.sword.draw_middle_right_cooldown(self.screen)

            self.modal.draw(self.screen, self.font)
            self.tab_menu.draw(self.screen)

            fps_text = self.small_font.render(f"FPS: {int(self.clock.get_fps())}", True, (150, 255, 150))
            self.screen.blit(fps_text, (SCREEN_WIDTH - fps_text.get_width() - 15, SCREEN_HEIGHT - fps_text.get_height() - 10))

            if self.game_won:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))

                next_lvl = self.get_next_level_file()
                msg = "LEVEL COMPLETE! Press 'R' for Next Level" if next_lvl else "ALL LEVELS COMPLETED! Press 'R' for Main Menu"
                win_text = self.font.render(msg, True, CHEST_COLOR)
                self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        # Custom Cursor
        self.custom_cursor.draw(self.screen)
        pygame.display.flip()
        self.clock.tick(60)