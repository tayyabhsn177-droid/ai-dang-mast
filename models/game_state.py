from typing import Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

class AttributeType(str, Enum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    INTELLIGENCE = "intelligence"
    CONSTITUTION = "constitution"
    WISDOM = "wisdom"
    CHARISMA = "charisma"

class Attributes(BaseModel):
    strength: int = Field(default=10, ge=1, le=20, description="Affects melee damage, carry capacity, physical skill checks")
    dexterity: int = Field(default=10, ge=1, le=20, description="Affects ranged damage, dodge chance, stealth, lockpicking")
    intelligence: int = Field(default=10, ge=1, le=20, description="Affects magic damage, mana pool, knowledge skills, puzzle solving")
    constitution: int = Field(default=10, ge=1, le=20, description="Affects health points, stamina, resistance to disease/poison")
    wisdom: int = Field(default=10, ge=1, le=20, description="Affects perception, insight, spell accuracy, social interactions")
    charisma: int = Field(default=10, ge=1, le=20, description="Affects persuasion, intimidation, leadership, NPC reactions")
    
    def get_modifier(self, attribute: AttributeType) -> int:
        """Calculate attribute modifier using D&D style formula: (attribute - 10) // 2"""
        value = getattr(self, attribute.value)
        return (value - 10) // 2
    
    def get_all_modifiers(self) -> Dict[str, int]:
        """Get all attribute modifiers as a dictionary"""
        return {attr.value: self.get_modifier(attr) for attr in AttributeType}

class CharacterStats(BaseModel):
    # Core resources
    health_points: int = Field(default=100, ge=0, description="Current health")
    max_health_points: int = Field(default=100, ge=1, description="Maximum health")
    mana_points: int = Field(default=50, ge=0, description="Current mana for magic")
    max_mana_points: int = Field(default=50, ge=1, description="Maximum mana")
    stamina_points: int = Field(default=75, ge=0, description="Current stamina for physical actions")
    max_stamina_points: int = Field(default=75, ge=1, description="Maximum stamina")
    
    # Progression
    level: int = Field(default=1, ge=1, description="Character level")
    experience_points: int = Field(default=0, ge=0, description="Current XP")
    experience_to_next_level: int = Field(default=1000, ge=1, description="XP needed for next level")
    available_attribute_points: int = Field(default=0, ge=0, description="Unspent attribute points")
    available_skill_points: int = Field(default=0, ge=0, description="Unspent skill points")
    
    def calculate_max_health(self, constitution_modifier: int) -> int:
        """Calculate max health based on level and constitution"""
        base_health = 50
        health_per_level = 10
        constitution_bonus = constitution_modifier * 5
        return base_health + (self.level * health_per_level) + constitution_bonus
    
    def calculate_max_mana(self, intelligence_modifier: int) -> int:
        """Calculate max mana based on level and intelligence"""
        base_mana = 20
        mana_per_level = 5
        intelligence_bonus = intelligence_modifier * 3
        return max(0, base_mana + (self.level * mana_per_level) + intelligence_bonus)
    
    def calculate_max_stamina(self, constitution_modifier: int, strength_modifier: int) -> int:
        """Calculate max stamina based on level, constitution, and strength"""
        base_stamina = 30
        stamina_per_level = 7
        stat_bonus = (constitution_modifier + strength_modifier) * 2
        return base_stamina + (self.level * stamina_per_level) + stat_bonus
    
    def calculate_xp_to_next_level(self) -> int:
        """Calculate XP needed for next level (exponential scaling)"""
        return (self.level * 1000) + ((self.level - 1) * 500)
    
    def can_level_up(self) -> bool:
        """Check if character has enough XP to level up"""
        return self.experience_points >= self.experience_to_next_level
    
    def get_health_percentage(self) -> float:
        """Get health as percentage (0.0 to 1.0)"""
        return self.health_points / self.max_health_points if self.max_health_points > 0 else 0.0
    
    def get_mana_percentage(self) -> float:
        """Get mana as percentage (0.0 to 1.0)"""
        return self.mana_points / self.max_mana_points if self.max_mana_points > 0 else 0.0
    
    def get_stamina_percentage(self) -> float:
        """Get stamina as percentage (0.0 to 1.0)"""
        return self.stamina_points / self.max_stamina_points if self.max_stamina_points > 0 else 0.0

class GameState(BaseModel):
    # Player identification
    player_name: str = ""
    character_class: str = ""
    
    # Character progression system
    attributes: Attributes = Field(default_factory=Attributes)
    character_stats: CharacterStats = Field(default_factory=CharacterStats)
    
    # Game world
    setting: str = ""
    preferences: Dict[str, Any] = {}
    game_started: bool = False
    
    # World data
    world_intro: str = ""
    location_intro: str = ""
    npcs: List[str] = []
    main_quest: str = ""
    side_quests: List[str] = []
    
    # Game flow
    current_scene: str = ""
    available_actions: List[str] = []
    selected_action: str = ""
    action_result: str = ""
    new_available_actions: List[str] = []
    
    # Dice and outcomes
    last_dice_roll: int = 0
    last_roll_outcome: str = ""
    
    # Inventory and items
    inventory: List[str] = []
    
    # System
    latest_narration: str = ""
    voice_output_disabled: bool = False
    
    def update_character_stats(self):
        """Update character stats based on attributes and level"""
        modifiers = self.attributes.get_all_modifiers()
        
        # Update max values
        self.character_stats.max_health_points = self.character_stats.calculate_max_health(
            modifiers['constitution']
        )
        self.character_stats.max_mana_points = self.character_stats.calculate_max_mana(
            modifiers['intelligence']
        )
        self.character_stats.max_stamina_points = self.character_stats.calculate_max_stamina(
            modifiers['constitution'], modifiers['strength']
        )
        
        # Update XP requirements
        self.character_stats.experience_to_next_level = self.character_stats.calculate_xp_to_next_level()
        
        # Ensure current values don't exceed max values
        self.character_stats.health_points = min(
            self.character_stats.health_points, 
            self.character_stats.max_health_points
        )
        self.character_stats.mana_points = min(
            self.character_stats.mana_points, 
            self.character_stats.max_mana_points
        )
        self.character_stats.stamina_points = min(
            self.character_stats.stamina_points, 
            self.character_stats.max_stamina_points
        )
    
    def add_experience(self, xp: int) -> bool:
        """Add experience points and return True if leveled up"""
        self.character_stats.experience_points += xp
        
        leveled_up = False
        while self.character_stats.can_level_up():
            # Level up!
            self.character_stats.experience_points -= self.character_stats.experience_to_next_level
            self.character_stats.level += 1
            
            # Award points for leveling up
            self.character_stats.available_attribute_points += 2
            self.character_stats.available_skill_points += 5
            
            leveled_up = True
        
        # Update all stats after potential level up
        self.update_character_stats()
        return leveled_up
    
    def spend_attribute_point(self, attribute: AttributeType) -> bool:
        """Spend an attribute point to increase an attribute by 1"""
        if self.character_stats.available_attribute_points <= 0:
            return False
        
        current_value = getattr(self.attributes, attribute.value)
        if current_value >= 20:  # Cap at 20
            return False
        
        # Increase attribute
        setattr(self.attributes, attribute.value, current_value + 1)
        self.character_stats.available_attribute_points -= 1
        
        # Update character stats
        self.update_character_stats()
        return True
    
    def take_damage(self, damage: int, damage_type: str = "physical") -> Dict[str, Any]:
        """Apply damage to the character and return damage info"""
        # Apply constitution modifier to reduce damage (minimum 1)
        constitution_mod = self.attributes.get_modifier(AttributeType.CONSTITUTION)
        reduced_damage = max(1, damage - constitution_mod)  # Constitution reduces damage
        
        old_hp = self.character_stats.health_points
        self.character_stats.health_points = max(0, self.character_stats.health_points - reduced_damage)
        actual_damage = old_hp - self.character_stats.health_points
        
        return {
            "damage_dealt": actual_damage,
            "damage_reduced": damage - actual_damage,
            "remaining_hp": self.character_stats.health_points,
            "is_unconscious": self.character_stats.health_points <= 0,
            "damage_type": damage_type
        }
    
    def heal(self, healing: int) -> int:
        """Heal the character and return actual healing done"""
        old_hp = self.character_stats.health_points
        self.character_stats.health_points = min(
            self.character_stats.max_health_points, 
            self.character_stats.health_points + healing
        )
        actual_healing = self.character_stats.health_points - old_hp
        
        return actual_healing
    
    def use_mana(self, mana_cost: int) -> bool:
        """Use mana if available, return True if successful"""
        if self.character_stats.mana_points >= mana_cost:
            self.character_stats.mana_points -= mana_cost
            return True
        return False
    
    def use_stamina(self, stamina_cost: int) -> bool:
        """Use stamina if available, return True if successful"""
        if self.character_stats.stamina_points >= stamina_cost:
            self.character_stats.stamina_points -= stamina_cost
            return True
        return False
    
    def rest(self, rest_type: str = "short") -> Dict[str, int]:
        """Rest to recover resources"""
        recovered = {"health": 0, "mana": 0, "stamina": 0}
        
        if rest_type == "short":
            # Short rest: recover 25% of stamina and mana
            stamina_recovery = int(self.character_stats.max_stamina_points * 0.25)
            mana_recovery = int(self.character_stats.max_mana_points * 0.25)
            
            self.character_stats.stamina_points = min(
                self.character_stats.max_stamina_points,
                self.character_stats.stamina_points + stamina_recovery
            )
            self.character_stats.mana_points = min(
                self.character_stats.max_mana_points,
                self.character_stats.mana_points + mana_recovery
            )
            
            recovered["stamina"] = stamina_recovery
            recovered["mana"] = mana_recovery
            
        elif rest_type == "long":
            # Long rest: fully recover all resources
            recovered["health"] = self.character_stats.max_health_points - self.character_stats.health_points
            recovered["mana"] = self.character_stats.max_mana_points - self.character_stats.mana_points  
            recovered["stamina"] = self.character_stats.max_stamina_points - self.character_stats.stamina_points
            
            self.character_stats.health_points = self.character_stats.max_health_points
            self.character_stats.mana_points = self.character_stats.max_mana_points
            self.character_stats.stamina_points = self.character_stats.max_stamina_points
        
        return recovered
    
    def get_character_summary(self) -> str:
        """Get a formatted character summary for display"""
        modifiers = self.attributes.get_all_modifiers()
        
        summary = f"""
=== CHARACTER SHEET ===
Name: {self.player_name} | Class: {self.character_class} | Level: {self.character_stats.level}
XP: {self.character_stats.experience_points:,} / {self.character_stats.experience_to_next_level:,}

ATTRIBUTES:
STR: {self.attributes.strength} ({modifiers['strength']:+d}) | CON: {self.attributes.constitution} ({modifiers['constitution']:+d})
DEX: {self.attributes.dexterity} ({modifiers['dexterity']:+d}) | WIS: {self.attributes.wisdom} ({modifiers['wisdom']:+d})  
INT: {self.attributes.intelligence} ({modifiers['intelligence']:+d}) | CHA: {self.attributes.charisma} ({modifiers['charisma']:+d})

RESOURCES:
Health: {self.character_stats.health_points}/{self.character_stats.max_health_points} ({self.character_stats.get_health_percentage():.0%})
Mana: {self.character_stats.mana_points}/{self.character_stats.max_mana_points} ({self.character_stats.get_mana_percentage():.0%})
Stamina: {self.character_stats.stamina_points}/{self.character_stats.max_stamina_points} ({self.character_stats.get_stamina_percentage():.0%})

AVAILABLE POINTS:
Attribute Points: {self.character_stats.available_attribute_points}
Skill Points: {self.character_stats.available_skill_points}

INVENTORY: {', '.join(self.inventory) if self.inventory else 'Empty'}
"""
        return summary.strip()