import pygame

class SlimeCombatHandler:
    @staticmethod
    def process_slime_combat(slimes, player_rect, sword, player_stats, obstacles):
        p_pos = (player_rect.centerx, player_rect.centery)
        is_attacking = getattr(sword, 'is_attacking', False)
        is_dashing = getattr(sword, 'is_dashing', False)
        is_parrying = getattr(sword, 'is_parrying', False)

        base_dmg = getattr(player_stats, 'base_damage', 3)
        p_dmg = base_dmg * 2 if is_dashing else base_dmg

        sword_rect = sword.get_hitbox() if is_attacking and hasattr(sword, 'get_hitbox') else None

        for slime in slimes:
            slime.update(player_rect, obstacles)

            if not slime.is_dead:
                # 1. Player Sword Attack Hitting Slime
                if is_attacking and sword_rect and slime.flash_timer <= 0:
                    slime_hurtbox = getattr(slime, 'hitbox', slime.rect)
                    if sword_rect.colliderect(slime_hurtbox):
                        slime.take_damage(p_dmg, knockback_source_pos=p_pos)

                # 2. Slime Collision with Player (NO PASSIVE CONTACT DAMAGE)
                if player_rect.colliderect(slime.rect):
                    if is_parrying and getattr(sword, 'parry_charges', 0) > 0:
                        slime.trigger_parry_stun(p_pos)
                        sword.consume_parry_charge()  # Consumes 1 parry charge
                    elif slime.state == "LUNGE":
                        # ONLY deals 1 damage during active lunge attack
                        if getattr(player_stats, 'i_frames', 0) <= 0:
                            if hasattr(player_stats, 'current_hp'):
                                player_stats.current_hp = max(0, player_stats.current_hp - 1)
                                player_stats.i_frames = 30  # 0.5s invincibility