import pygame
from assets.damage_text import DamageTextManager

class SlimeCombatHandler:
    @staticmethod
    def process_slime_combat(slimes, player_rect, sword, player_stats, obstacles, player_controller=None):
        p_pos = (player_rect.centerx, player_rect.centery)
        is_attacking = getattr(sword, 'is_attacking', False)
        is_dashing = getattr(sword, 'is_dashing', False)
        is_parrying = getattr(sword, 'is_parrying', False)

        base_dmg = getattr(player_stats, 'base_damage', 3)
        p_dmg = base_dmg * 2 if is_dashing else base_dmg

        sword_rect = sword.get_hitbox() if is_attacking and hasattr(sword, 'get_hitbox') else None
        dmg_manager = DamageTextManager()

        for slime in slimes:
            slime.update(player_rect, obstacles)

            if not slime.is_dead:
                # 1. Player attacks Slime
                if is_attacking and sword_rect and slime.flash_timer <= 0:
                    slime_hurtbox = getattr(slime, 'hitbox', slime.rect)
                    if sword_rect.colliderect(slime_hurtbox):
                        slime.take_damage(p_dmg, knockback_source_pos=p_pos)
                        dmg_manager.add_text(
                            slime.rect.centerx, slime.rect.top - 4, 
                            p_dmg, color=(210, 215, 220)
                        )

                # 2. Slime attacks Player
                if player_rect.colliderect(slime.rect):
                    if is_parrying and getattr(sword, 'parry_charges', 0) > 0:
                        slime.trigger_parry_stun(p_pos)
                        sword.consume_parry_charge()
                    elif slime.state == "LUNGE":
                        if getattr(player_stats, 'i_frames', 0) <= 0:
                            if hasattr(player_stats, 'current_hp'):
                                player_stats.current_hp = max(0, player_stats.current_hp - 1)
                                player_stats.i_frames = 30  
                                player_stats.flash_timer = 12
                                
                                dmg_manager.add_text(
                                    player_rect.centerx, player_rect.top - 6, 
                                    1, color=(255, 75, 75), is_player=True
                                )

                                # Determine knockback force based on slime type
                                # Small slime = lighter knockback, Medium slime = further knockback
                                slime_name = getattr(slime, 'name', "Small Slime")
                                kb_force = 3.5 if slime_name == "Small Slime" else 6.5

                                if player_controller and hasattr(player_controller, 'apply_knockback'):
                                    s_center = pygame.Vector2(slime.rect.centerx, slime.rect.centery)
                                    p_center = pygame.Vector2(player_rect.centerx, player_rect.centery)
                                    kb_vec = p_center - s_center
                                    if kb_vec.length() > 0:
                                        player_controller.apply_knockback(kb_vec.normalize() * kb_force)