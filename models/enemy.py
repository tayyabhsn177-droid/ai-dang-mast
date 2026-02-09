from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import random

class EnemyType(str, Enum):
    GOBLIN = "goblin"
    ORC = "orc"
    SKELETON = "skeleton"
    DRAGON = "dragon"
    DEMON = "demon"
    WOLF = "wolf"
    BANDIT = "bandit"
    NECROMANCER = "necromancer"
    BOSS_DRAGON = "boss_dragon"
    BOSS_LICH = "boss_lich"

class AIBehavior(str, Enum):
    AGGRESSIVE = "aggressive"  # Always attacks, prefers high damage
    DEFENSIVE = "defensive"    # Uses defensive abilities, heals when low HP
    TACTICAL = "tactical"      # Mixes attacks and buffs strategically
    BERSERKER = "berserker"    # More aggressive when low HP
    SUPPORT = "support"        # Focuses on buffs and debuffs

class EnemyAbility(BaseModel):
    name: str
    damage: int = 0
    healing: int = 0
    status_effect: Optional[str] = None
    status_duration: int = 0
    mana_cost: int = 0
    cooldown: int = 0
    description: str = ""
    targeting: str = "enemy"  # "enemy", "self", "all_enemies"
    
class Enemy(BaseModel):
    name: str
    enemy_type: EnemyType
    level: int = 1
    
    # Stats
    health_points: int
    max_health_points: int
    mana_points: int = 0
    max_mana_points: int = 0
    
    # Combat attributes
    attack_power: int
    defense: int
    speed: int  # Determines turn order
    
    # AI
    behavior: AIBehavior
    abilities: List[EnemyAbility] = []
    ability_cooldowns: Dict[str, int] = {}
    
    # Status
    status_effects: List[Dict[str, Any]] = []
    is_alive: bool = True
    is_boss: bool = False
    
    # Boss-specific
    current_phase: int = 1
    max_phases: int = 1
    phase_thresholds: List[float] = [0.5]  # HP % to trigger phase change
    
    # Loot
    experience_reward: int = 50
    gold_reward: int = 10
    loot_table: List[str] = []
    
    def get_health_percentage(self) -> float:
        """Get current health as percentage"""
        return self.health_points / self.max_health_points if self.max_health_points > 0 else 0.0
    
    def take_damage(self, damage: int) -> Dict[str, Any]:
        """Apply damage to enemy"""
        # Apply defense reduction
        reduced_damage = max(1, damage - (self.defense // 2))
        
        old_hp = self.health_points
        self.health_points = max(0, self.health_points - reduced_damage)
        actual_damage = old_hp - self.health_points
        
        if self.health_points <= 0:
            self.is_alive = False
        
        return {
            "damage_dealt": actual_damage,
            "damage_reduced": damage - actual_damage,
            "remaining_hp": self.health_points,
            "is_dead": not self.is_alive
        }
    
    def heal(self, healing: int) -> int:
        """Heal the enemy"""
        old_hp = self.health_points
        self.health_points = min(self.max_health_points, self.health_points + healing)
        actual_healing = self.health_points - old_hp
        return actual_healing
    
    def add_status_effect(self, effect_name: str, duration: int, **kwargs):
        """Add a status effect to the enemy"""
        effect = {
            "name": effect_name,
            "duration": duration,
            "applied_turn": 0,
            **kwargs
        }
        self.status_effects.append(effect)
    
    def update_status_effects(self) -> List[Dict[str, Any]]:
        """Update status effect durations and remove expired ones"""
        effects_triggered = []
        
        remaining_effects = []
        for effect in self.status_effects:
            effect["duration"] -= 1
            
            # Trigger effect
            effect_result = self._trigger_status_effect(effect)
            if effect_result:
                effects_triggered.append(effect_result)
            
            # Keep effect if duration > 0
            if effect["duration"] > 0:
                remaining_effects.append(effect)
        
        self.status_effects = remaining_effects
        return effects_triggered
    
    def _trigger_status_effect(self, effect: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Trigger a status effect's impact"""
        effect_name = effect["name"]
        
        if effect_name == "poisoned":
            damage = effect.get("damage_per_turn", 3)
            result = self.take_damage(damage)
            return {
                "effect": "poisoned",
                "target": self.name,
                "damage": result["damage_dealt"]
            }
        
        elif effect_name == "bleeding":
            damage = effect.get("damage_per_turn", 5)
            result = self.take_damage(damage)
            return {
                "effect": "bleeding",
                "target": self.name,
                "damage": result["damage_dealt"]
            }
        
        elif effect_name == "stunned":
            return {
                "effect": "stunned",
                "target": self.name,
                "message": f"{self.name} is stunned and cannot act!"
            }
        
        elif effect_name == "weakened":
            return {
                "effect": "weakened",
                "target": self.name,
                "message": f"{self.name} is weakened (attack power reduced)"
            }
        
        return None
    
    def has_status_effect(self, effect_name: str) -> bool:
        """Check if enemy has a specific status effect"""
        return any(effect["name"] == effect_name for effect in self.status_effects)
    
    def check_phase_change(self) -> bool:
        """Check if boss should change phase"""
        if not self.is_boss or self.current_phase >= self.max_phases:
            return False
        
        hp_percentage = self.get_health_percentage()
        
        # Check if we've crossed a phase threshold
        if self.current_phase <= len(self.phase_thresholds):
            threshold = self.phase_thresholds[self.current_phase - 1]
            if hp_percentage <= threshold:
                self.current_phase += 1
                return True
        
        return False
    
    def choose_action(self, player_hp_percentage: float) -> EnemyAbility:
        """AI chooses which ability to use based on behavior"""
        available_abilities = [
            ability for ability in self.abilities
            if ability.name not in self.ability_cooldowns or self.ability_cooldowns[ability.name] == 0
        ]
        
        if not available_abilities:
            # Use basic attack if all abilities on cooldown
            return EnemyAbility(
                name="Basic Attack",
                damage=self.attack_power,
                description=f"{self.name} attacks!"
            )
        
        # AI decision making based on behavior
        if self.behavior == AIBehavior.AGGRESSIVE:
            # Choose highest damage ability
            return max(available_abilities, key=lambda a: a.damage)
        
        elif self.behavior == AIBehavior.DEFENSIVE:
            # Heal if low HP, otherwise attack
            if self.get_health_percentage() < 0.3:
                healing_abilities = [a for a in available_abilities if a.healing > 0]
                if healing_abilities:
                    return random.choice(healing_abilities)
            return random.choice(available_abilities)
        
        elif self.behavior == AIBehavior.TACTICAL:
            # Mix of attacks and status effects
            if random.random() < 0.3:  # 30% chance to use status effect
                status_abilities = [a for a in available_abilities if a.status_effect]
                if status_abilities:
                    return random.choice(status_abilities)
            return random.choice(available_abilities)
        
        elif self.behavior == AIBehavior.BERSERKER:
            # More aggressive when low HP
            if self.get_health_percentage() < 0.5:
                damage_abilities = [a for a in available_abilities if a.damage > 0]
                if damage_abilities:
                    return max(damage_abilities, key=lambda a: a.damage)
            return random.choice(available_abilities)
        
        else:  # SUPPORT
            # Prefer buffs and debuffs
            status_abilities = [a for a in available_abilities if a.status_effect]
            if status_abilities and random.random() < 0.6:
                return random.choice(status_abilities)
            return random.choice(available_abilities)
    
    def update_cooldowns(self):
        """Reduce all ability cooldowns by 1"""
        for ability_name in list(self.ability_cooldowns.keys()):
            if self.ability_cooldowns[ability_name] > 0:
                self.ability_cooldowns[ability_name] -= 1


# Enemy Templates
def create_goblin(level: int = 1) -> Enemy:
    """Create a goblin enemy"""
    return Enemy(
        name="Goblin Warrior",
        enemy_type=EnemyType.GOBLIN,
        level=level,
        health_points=30 + (level * 5),
        max_health_points=30 + (level * 5),
        mana_points=10,
        max_mana_points=10,
        attack_power=8 + level,
        defense=3 + level,
        speed=12,
        behavior=AIBehavior.AGGRESSIVE,
        abilities=[
            EnemyAbility(
                name="Slash",
                damage=12 + level,
                description="A quick slash attack"
            ),
            EnemyAbility(
                name="Poison Dagger",
                damage=8,
                status_effect="poisoned",
                status_duration=3,
                description="Attacks with a poisoned dagger"
            )
        ],
        experience_reward=50 * level,
        gold_reward=10 * level,
        loot_table=["Goblin Dagger", "Rusty Sword", "Health Potion"]
    )

def create_orc(level: int = 1) -> Enemy:
    """Create an orc enemy"""
    return Enemy(
        name="Orc Berserker",
        enemy_type=EnemyType.ORC,
        level=level,
        health_points=60 + (level * 10),
        max_health_points=60 + (level * 10),
        mana_points=5,
        max_mana_points=5,
        attack_power=15 + (level * 2),
        defense=8 + level,
        speed=8,
        behavior=AIBehavior.BERSERKER,
        abilities=[
            EnemyAbility(
                name="Heavy Strike",
                damage=20 + (level * 2),
                description="A devastating heavy attack"
            ),
            EnemyAbility(
                name="Rage",
                damage=25 + (level * 3),
                cooldown=3,
                description="Enters a rage, dealing massive damage"
            )
        ],
        experience_reward=75 * level,
        gold_reward=15 * level,
        loot_table=["Orcish Axe", "Leather Armor", "Health Potion", "Strength Elixir"]
    )

def create_necromancer(level: int = 1) -> Enemy:
    """Create a necromancer enemy"""
    return Enemy(
        name="Dark Necromancer",
        enemy_type=EnemyType.NECROMANCER,
        level=level,
        health_points=40 + (level * 6),
        max_health_points=40 + (level * 6),
        mana_points=50 + (level * 5),
        max_mana_points=50 + (level * 5),
        attack_power=10 + level,
        defense=5 + level,
        speed=10,
        behavior=AIBehavior.TACTICAL,
        abilities=[
            EnemyAbility(
                name="Shadow Bolt",
                damage=15 + (level * 2),
                mana_cost=10,
                description="Launches a bolt of dark energy"
            ),
            EnemyAbility(
                name="Curse of Weakness",
                damage=5,
                status_effect="weakened",
                status_duration=4,
                mana_cost=15,
                description="Curses the target, reducing their strength"
            ),
            EnemyAbility(
                name="Life Drain",
                damage=12,
                healing=12,
                mana_cost=20,
                cooldown=2,
                description="Drains life from the target"
            )
        ],
        experience_reward=100 * level,
        gold_reward=25 * level,
        loot_table=["Necromancer Staff", "Dark Tome", "Mana Crystal", "Soul Gem"]
    )

def create_dragon_boss(level: int = 1) -> Enemy:
    """Create a dragon boss enemy"""
    return Enemy(
        name="Ancient Dragon",
        enemy_type=EnemyType.BOSS_DRAGON,
        level=level,
        health_points=200 + (level * 30),
        max_health_points=200 + (level * 30),
        mana_points=100,
        max_mana_points=100,
        attack_power=25 + (level * 3),
        defense=15 + (level * 2),
        speed=15,
        behavior=AIBehavior.TACTICAL,
        is_boss=True,
        max_phases=3,
        phase_thresholds=[0.66, 0.33],
        abilities=[
            EnemyAbility(
                name="Claw Strike",
                damage=30 + (level * 3),
                description="Strikes with massive claws"
            ),
            EnemyAbility(
                name="Fire Breath",
                damage=40 + (level * 4),
                cooldown=2,
                description="Breathes devastating fire"
            ),
            EnemyAbility(
                name="Tail Sweep",
                damage=25 + (level * 2),
                status_effect="stunned",
                status_duration=1,
                description="Sweeps tail, stunning the target"
            ),
            EnemyAbility(
                name="Dragon Roar",
                damage=15,
                status_effect="weakened",
                status_duration=3,
                cooldown=3,
                description="Roars, weakening all enemies"
            ),
            EnemyAbility(
                name="Ancient Fury",
                damage=60 + (level * 5),
                cooldown=4,
                description="Unleashes ultimate power (only in phase 3)"
            )
        ],
        experience_reward=500 * level,
        gold_reward=200 * level,
        loot_table=[
            "Dragon Scale Armor",
            "Dragon Fang Sword",
            "Ancient Amulet",
            "Dragon Heart",
            "Legendary Potion",
            "Gold Coins (500)"
        ]
    )

def create_skeleton(level: int = 1) -> Enemy:
    """Create a skeleton enemy"""
    return Enemy(
        name="Skeleton Warrior",
        enemy_type=EnemyType.SKELETON,
        level=level,
        health_points=25 + (level * 4),
        max_health_points=25 + (level * 4),
        attack_power=10 + level,
        defense=6 + level,
        speed=9,
        behavior=AIBehavior.AGGRESSIVE,
        abilities=[
            EnemyAbility(
                name="Bone Strike",
                damage=12 + level,
                description="Strikes with a bone weapon"
            ),
            EnemyAbility(
                name="Rattle",
                damage=5,
                status_effect="stunned",
                status_duration=1,
                cooldown=3,
                description="Rattles bones to stun the enemy"
            )
        ],
        experience_reward=40 * level,
        gold_reward=8 * level,
        loot_table=["Bone Dagger", "Ancient Coin", "Health Potion"]
    )

def create_wolf(level: int = 1) -> Enemy:
    """Create a wolf enemy"""
    return Enemy(
        name="Dire Wolf",
        enemy_type=EnemyType.WOLF,
        level=level,
        health_points=35 + (level * 6),
        max_health_points=35 + (level * 6),
        attack_power=12 + level,
        defense=4 + level,
        speed=14,
        behavior=AIBehavior.AGGRESSIVE,
        abilities=[
            EnemyAbility(
                name="Bite",
                damage=14 + level,
                description="Bites with sharp fangs"
            ),
            EnemyAbility(
                name="Bleeding Bite",
                damage=10,
                status_effect="bleeding",
                status_duration=3,
                description="A vicious bite that causes bleeding"
            )
        ],
        experience_reward=45 * level,
        gold_reward=5 * level,
        loot_table=["Wolf Pelt", "Sharp Fang", "Health Potion"]
    )


# Enemy spawning based on location/difficulty
def spawn_random_enemy(difficulty: int = 1) -> Enemy:
    """Spawn a random enemy based on difficulty"""
    enemy_pool = [
        (create_goblin, 0.3),
        (create_skeleton, 0.25),
        (create_wolf, 0.2),
        (create_orc, 0.15),
        (create_necromancer, 0.1),
    ]
    
    # Choose enemy type
    rand = random.random()
    cumulative = 0
    for enemy_func, probability in enemy_pool:
        cumulative += probability
        if rand <= cumulative:
            return enemy_func(level=difficulty)
    
    # Fallback
    return create_goblin(level=difficulty)