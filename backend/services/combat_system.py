from typing import Dict, Any, List, Optional, Tuple
from models.game_state import GameState, AttributeType
from models.enemy import Enemy, EnemyAbility
from utils.dice_roller import roll_dice
from utils.logger import get_logger
import random

combat_logger = get_logger("combat")

class CombatAction:
    """Represents a combat action that can be taken"""
    def __init__(self, name: str, action_type: str, **kwargs):
        self.name = name
        self.action_type = action_type  # "attack", "defend", "spell", "item", "flee"
        self.properties = kwargs

class CombatLog:
    """Stores combat events for display"""
    def __init__(self):
        self.events: List[str] = []
        self.turn_number: int = 0
    
    def add_event(self, event: str):
        self.events.append(event)
    
    def get_last_n_events(self, n: int = 10) -> List[str]:
        return self.events[-n:] if len(self.events) > n else self.events
    
    def clear(self):
        self.events = []
        self.turn_number = 0
    
    def increment_turn(self):
        self.turn_number += 1
        self.events.append(f"\n--- Turn {self.turn_number} ---")

class CombatSystem:
    """Manages turn-based combat encounters"""
    
    def __init__(self):
        self.active_combat: bool = False
        self.enemies: List[Enemy] = []
        self.combat_log = CombatLog()
        self.player_turn: bool = True
        self.turn_order: List[str] = []  # Order of actions in combat
        
    def start_combat(self, game_state: GameState, enemies: List[Enemy]) -> Dict[str, Any]:
        """Initialize combat encounter"""
        self.active_combat = True
        self.enemies = enemies
        self.combat_log.clear()
        
        combat_logger.info(
            "Combat started",
            extra={
                "enemy_count": len(enemies),
                "enemy_types": [e.name for e in enemies],
                "player_hp": game_state.character_stats.health_points,
                "event": "combat_start"
            }
        )
        
        # Determine turn order based on speed
        player_speed = game_state.attributes.dexterity + 10  # Base speed
        
        self.turn_order = []
        for enemy in enemies:
            if enemy.speed > player_speed:
                self.turn_order.append(enemy.name)
        
        self.turn_order.append("Player")
        
        for enemy in enemies:
            if enemy.speed <= player_speed:
                self.turn_order.append(enemy.name)
        
        # Add intro to combat log
        enemy_names = ", ".join([e.name for e in enemies])
        self.combat_log.add_event(f"⚔️ Combat begins against: {enemy_names}!")
        self.combat_log.add_event(f"Turn order: {' → '.join(self.turn_order)}")
        
        # Check if boss battle
        is_boss_battle = any(e.is_boss for e in enemies)
        
        return {
            "combat_started": True,
            "enemies": [self._enemy_to_dict(e) for e in enemies],
            "turn_order": self.turn_order,
            "is_boss_battle": is_boss_battle,
            "combat_log": self.combat_log.get_last_n_events()
        }
    
    def player_attack(self, game_state: GameState, target_index: int = 0) -> Dict[str, Any]:
        """Player performs a basic attack"""
        if target_index >= len(self.enemies):
            return {"error": "Invalid target"}
        
        target = self.enemies[target_index]
        if not target.is_alive:
            return {"error": "Target is already dead"}
        
        # Calculate damage
        base_damage = game_state.attributes.strength + 10
        roll = roll_dice(20)
        
        # Critical hit on 20
        if roll == 20:
            damage = base_damage * 2
            self.combat_log.add_event(f"🎯 CRITICAL HIT! You strike {target.name} for {damage} damage!")
        elif roll == 1:
            self.combat_log.add_event(f"💥 CRITICAL MISS! Your attack against {target.name} fails completely!")
            return self._process_turn_end(game_state)
        else:
            # Normal attack
            modifier = game_state.attributes.get_modifier(AttributeType.STRENGTH)
            damage = base_damage + modifier + (roll // 2)
        
        # Apply damage
        damage_result = target.take_damage(damage)
        
        self.combat_log.add_event(
            f"⚔️ You attack {target.name} for {damage_result['damage_dealt']} damage! "
            f"({target.health_points}/{target.max_health_points} HP remaining)"
        )
        
        if not target.is_alive:
            self.combat_log.add_event(f"💀 {target.name} has been defeated!")
        
        return self._process_turn_end(game_state)
    
    def player_use_ability(self, game_state: GameState, ability_name: str, target_index: int = 0) -> Dict[str, Any]:
        """Player uses a special ability"""
        # For now, we'll implement a few basic abilities
        # Later you can expand this with a proper ability system
        
        abilities = {
            "Power Strike": {
                "damage": game_state.attributes.strength * 2,
                "stamina_cost": 15,
                "description": "A powerful melee attack"
            },
            "Fireball": {
                "damage": game_state.attributes.intelligence * 2 + 20,
                "mana_cost": 20,
                "description": "A blazing ball of fire",
                "element": "fire"
            },
            "Heal": {
                "healing": 30 + game_state.attributes.wisdom * 2,
                "mana_cost": 25,
                "description": "Restore health",
                "targeting": "self"
            }
        }
        
        if ability_name not in abilities:
            return {"error": f"Unknown ability: {ability_name}"}
        
        ability = abilities[ability_name]
        
        # Check resource costs
        if "mana_cost" in ability:
            if not game_state.use_mana(ability["mana_cost"]):
                return {"error": "Not enough mana"}
        
        if "stamina_cost" in ability:
            if not game_state.use_stamina(ability["stamina_cost"]):
                return {"error": "Not enough stamina"}
        
        # Apply ability effect
        if ability.get("targeting") == "self":
            healing = ability.get("healing", 0)
            actual_healing = game_state.heal(healing)
            self.combat_log.add_event(f"✨ You use {ability_name} and heal for {actual_healing} HP!")
        else:
            if target_index >= len(self.enemies):
                return {"error": "Invalid target"}
            
            target = self.enemies[target_index]
            if not target.is_alive:
                return {"error": "Target is already dead"}
            
            damage = ability.get("damage", 0)
            roll = roll_dice(20)
            
            # Add roll variance
            final_damage = damage + (roll // 2)
            
            damage_result = target.take_damage(final_damage)
            
            self.combat_log.add_event(
                f"✨ You use {ability_name} on {target.name} for {damage_result['damage_dealt']} damage! "
                f"({target.health_points}/{target.max_health_points} HP remaining)"
            )
            
            if not target.is_alive:
                self.combat_log.add_event(f"💀 {target.name} has been defeated!")
        
        return self._process_turn_end(game_state)
    
    def player_defend(self, game_state: GameState) -> Dict[str, Any]:
        """Player takes a defensive stance"""
        # Add temporary defense buff
        game_state.add_status_effect("defending", 1, defense_bonus=5)
        self.combat_log.add_event("🛡️ You take a defensive stance, increasing your defense!")
        
        return self._process_turn_end(game_state)
    
    def player_use_item(self, game_state: GameState, item_name: str) -> Dict[str, Any]:
        """Player uses an item from inventory"""
        if item_name not in game_state.inventory:
            return {"error": f"You don't have {item_name}"}
        
        # Item effects
        item_effects = {
            "Health Potion": {"heal": 50},
            "Mana Potion": {"mana": 30},
            "Antidote": {"remove_status": "poisoned"},
            "Strength Elixir": {"buff": "strength", "duration": 3, "bonus": 3},
        }
        
        if item_name not in item_effects:
            return {"error": f"Cannot use {item_name} in combat"}
        
        effect = item_effects[item_name]
        
        # Apply effect
        if "heal" in effect:
            healing = game_state.heal(effect["heal"])
            self.combat_log.add_event(f"🧪 You use {item_name} and heal for {healing} HP!")
        
        if "mana" in effect:
            old_mana = game_state.character_stats.mana_points
            game_state.character_stats.mana_points = min(
                game_state.character_stats.max_mana_points,
                game_state.character_stats.mana_points + effect["mana"]
            )
            restored = game_state.character_stats.mana_points - old_mana
            self.combat_log.add_event(f"🧪 You use {item_name} and restore {restored} mana!")
        
        if "remove_status" in effect:
            # Remove status effect
            game_state.status_effects = [
                e for e in game_state.status_effects 
                if e["name"] != effect["remove_status"]
            ]
            self.combat_log.add_event(f"🧪 You use {item_name} and cure {effect['remove_status']}!")
        
        # Remove item from inventory
        game_state.inventory.remove(item_name)
        
        return self._process_turn_end(game_state)
    
    def player_flee(self, game_state: GameState) -> Dict[str, Any]:
        """Player attempts to flee from combat"""
        # Flee chance based on dexterity
        flee_roll = roll_dice(20) + game_state.attributes.get_modifier(AttributeType.DEXTERITY)
        
        # Higher chance to flee if no bosses
        has_boss = any(e.is_boss for e in self.enemies)
        flee_dc = 15 if has_boss else 10
        
        if flee_roll >= flee_dc:
            self.combat_log.add_event("🏃 You successfully flee from combat!")
            self.end_combat(game_state, fled=True)
            return {
                "fled": True,
                "combat_ended": True,
                "combat_log": self.combat_log.get_last_n_events()
            }
        else:
            self.combat_log.add_event("🏃 You attempt to flee but fail!")
            return self._process_turn_end(game_state)
    
    def _process_enemy_turns(self, game_state: GameState) -> List[Dict[str, Any]]:
        """Process all enemy turns"""
        enemy_actions = []
        
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
            
            # Update status effects
            status_results = enemy.update_status_effects()
            for result in status_results:
                if "damage" in result:
                    self.combat_log.add_event(
                        f"💀 {enemy.name} takes {result['damage']} damage from {result['effect']}!"
                    )
            
            # Check if stunned
            if enemy.has_status_effect("stunned"):
                self.combat_log.add_event(f"💫 {enemy.name} is stunned and cannot act!")
                continue
            
            # Check for phase change (boss)
            if enemy.check_phase_change():
                self.combat_log.add_event(
                    f"🔥 {enemy.name} enters Phase {enemy.current_phase}! "
                    f"The battle intensifies!"
                )
            
            # Choose action based on AI
            player_hp_pct = game_state.character_stats.get_health_percentage()
            chosen_ability = enemy.choose_action(player_hp_pct)
            
            # Execute ability
            action_result = self._execute_enemy_ability(game_state, enemy, chosen_ability)
            enemy_actions.append(action_result)
            
            # Update cooldowns
            if chosen_ability.cooldown > 0:
                enemy.ability_cooldowns[chosen_ability.name] = chosen_ability.cooldown
            
            enemy.update_cooldowns()
        
        return enemy_actions
    
    def _execute_enemy_ability(self, game_state: GameState, enemy: Enemy, ability: EnemyAbility) -> Dict[str, Any]:
        """Execute an enemy ability"""
        result = {
            "enemy": enemy.name,
            "ability": ability.name,
            "description": ability.description
        }
        
        if ability.targeting == "self" and ability.healing > 0:
            # Enemy heals itself
            healing = enemy.heal(ability.healing)
            self.combat_log.add_event(
                f"💚 {enemy.name} uses {ability.name} and heals for {healing} HP!"
            )
            result["healing"] = healing
        else:
            # Attack player
            damage = ability.damage
            
            # Apply weakness status effect
            if enemy.has_status_effect("weakened"):
                damage = int(damage * 0.75)
            
            # Roll for hit
            hit_roll = roll_dice(20)
            
            if hit_roll == 1:
                self.combat_log.add_event(f"💥 {enemy.name}'s {ability.name} misses completely!")
                result["missed"] = True
                return result
            
            # Check if player is defending
            if game_state.has_status_effect("defending"):
                damage = int(damage * 0.6)
                self.combat_log.add_event("🛡️ Your defensive stance reduces incoming damage!")
            
            # Apply damage
            damage_info = game_state.take_damage(damage)
            
            self.combat_log.add_event(
                f"💢 {enemy.name} uses {ability.name}! "
                f"You take {damage_info['damage_dealt']} damage! "
                f"({game_state.character_stats.health_points}/{game_state.character_stats.max_health_points} HP remaining)"
            )
            
            result["damage"] = damage_info["damage_dealt"]
            
            # Apply status effect
            if ability.status_effect:
                game_state.add_status_effect(
                    ability.status_effect,
                    ability.status_duration
                )
                self.combat_log.add_event(
                    f"💀 You are afflicted with {ability.status_effect}!"
                )
                result["status_applied"] = ability.status_effect
        
        return result
    
    def _process_turn_end(self, game_state: GameState) -> Dict[str, Any]:
        """Process end of turn: enemy actions, status effects, check victory/defeat"""
        # Update player status effects
        status_results = game_state.update_status_effects()
        for result in status_results:
            if "damage" in result:
                self.combat_log.add_event(
                    f"💀 You take {result['damage']} damage from {result['effect']}!"
                )
        
        # Check if player died from status
        if game_state.character_stats.health_points <= 0:
            return self._check_combat_end(game_state)
        
        # Enemy turns
        enemy_actions = self._process_enemy_turns(game_state)
        
        # Check combat end
        result = self._check_combat_end(game_state)
        
        if not result.get("combat_ended"):
            self.combat_log.increment_turn()
        
        return result
    
    def _check_combat_end(self, game_state: GameState) -> Dict[str, Any]:
        """Check if combat has ended (victory or defeat)"""
        # Check if all enemies dead
        all_enemies_dead = all(not e.is_alive for e in self.enemies)
        
        if all_enemies_dead:
            return self._handle_victory(game_state)
        
        # Check if player dead
        if game_state.character_stats.health_points <= 0:
            return self._handle_defeat(game_state)
        
        # Combat continues
        return {
            "combat_ended": False,
            "player_turn": True,
            "enemies": [self._enemy_to_dict(e) for e in self.enemies if e.is_alive],
            "player_stats": self._player_stats_dict(game_state),
            "combat_log": self.combat_log.get_last_n_events(15)
        }
    
    def _handle_victory(self, game_state: GameState) -> Dict[str, Any]:
        """Handle combat victory"""
        self.combat_log.add_event("🎉 Victory! All enemies have been defeated!")
        
        # Calculate rewards
        total_xp = sum(e.experience_reward for e in self.enemies)
        total_gold = sum(e.gold_reward for e in self.enemies)
        
        # Collect loot
        loot = []
        for enemy in self.enemies:
            if enemy.loot_table and random.random() < 0.6:  # 60% chance
                item = random.choice(enemy.loot_table)
                loot.append(item)
                game_state.inventory.append(item)
        
        # Award XP
        leveled_up = game_state.add_experience(total_xp)
        
        self.combat_log.add_event(f"💰 Gained {total_xp} XP and {total_gold} gold!")
        if loot:
            self.combat_log.add_event(f"🎁 Loot found: {', '.join(loot)}")
        if leveled_up:
            self.combat_log.add_event(
                f"⭐ LEVEL UP! You are now level {game_state.character_stats.level}!"
            )
        
        self.end_combat(game_state, victory=True)
        
        combat_logger.info(
            "Combat victory",
            extra={
                "xp_gained": total_xp,
                "gold_gained": total_gold,
                "loot": loot,
                "leveled_up": leveled_up,
                "event": "combat_victory"
            }
        )
        
        return {
            "combat_ended": True,
            "victory": True,
            "rewards": {
                "xp": total_xp,
                "gold": total_gold,
                "loot": loot,
                "leveled_up": leveled_up,
                "new_level": game_state.character_stats.level if leveled_up else None
            },
            "combat_log": self.combat_log.get_last_n_events()
        }
    
    def _handle_defeat(self, game_state: GameState) -> Dict[str, Any]:
        """Handle combat defeat"""
        self.combat_log.add_event("💀 You have been defeated...")
        
        self.end_combat(game_state, defeat=True)
        
        combat_logger.info(
            "Combat defeat",
            extra={
                "event": "combat_defeat"
            }
        )
        
        return {
            "combat_ended": True,
            "defeat": True,
            "game_over": True,
            "combat_log": self.combat_log.get_last_n_events()
        }
    
    def end_combat(self, game_state: GameState, victory: bool = False, defeat: bool = False, fled: bool = False):
        """Clean up after combat ends"""
        self.active_combat = False
        self.enemies = []
        
        # Clear combat-specific status effects
        game_state.status_effects = [
            e for e in game_state.status_effects
            if e["name"] not in ["defending"]
        ]
    
    def _enemy_to_dict(self, enemy: Enemy) -> Dict[str, Any]:
        """Convert enemy to dictionary for API response"""
        return {
            "name": enemy.name,
            "type": enemy.enemy_type.value,
            "level": enemy.level,
            "hp": enemy.health_points,
            "max_hp": enemy.max_health_points,
            "is_alive": enemy.is_alive,
            "is_boss": enemy.is_boss,
            "current_phase": enemy.current_phase if enemy.is_boss else None,
            "status_effects": [e["name"] for e in enemy.status_effects]
        }
    
    def _player_stats_dict(self, game_state: GameState) -> Dict[str, Any]:
        """Get player stats for combat display"""
        return {
            "hp": game_state.character_stats.health_points,
            "max_hp": game_state.character_stats.max_health_points,
            "mana": game_state.character_stats.mana_points,
            "max_mana": game_state.character_stats.max_mana_points,
            "stamina": game_state.character_stats.stamina_points,
            "max_stamina": game_state.character_stats.max_stamina_points,
            "status_effects": [e["name"] for e in game_state.status_effects]
        }