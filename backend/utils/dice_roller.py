import random
from utils.logger import get_logger, log_performance

# Initialize logger
dice_logger = get_logger("dice")

@log_performance(dice_logger)
def roll_dice(sides: int = 20) -> int:
    """
    Roll a dice with given sides (default d20).
    
    Args:
        sides: Number of sides on the dice (default 20)
        
    Returns:
        int: The result of the dice roll
    """
    if sides < 1:
        dice_logger.error(
            "Invalid dice sides specified",
            extra={
                "sides": sides,
                "error": "sides_must_be_positive",
                "event": "dice_roll_error"
            }
        )
        raise ValueError("Dice must have at least 1 side")
    
    dice_logger.debug(
        f"Rolling d{sides} dice",
        extra={
            "dice_type": f"d{sides}",
            "event": "dice_roll_start"
        }
    )
    
    try:
        result = random.randint(1, sides)
        
        # Determine if it's a critical result
        is_critical_success = result == sides
        is_critical_failure = result == 1
        is_high_roll = result >= (sides * 0.8)  # Top 20%
        is_low_roll = result <= (sides * 0.2)   # Bottom 20%
        
        dice_logger.info(
            f"Dice roll result: {result}",
            extra={
                "dice_type": f"d{sides}",
                "result": result,
                "is_critical_success": is_critical_success,
                "is_critical_failure": is_critical_failure,
                "is_high_roll": is_high_roll,
                "is_low_roll": is_low_roll,
                "success_threshold": 10 if sides == 20 else sides // 2,
                "event": "dice_rolled"
            }
        )
        
        # Log special cases
        if is_critical_success:
            dice_logger.info(
                "Critical success rolled!",
                extra={
                    "result": result,
                    "dice_type": f"d{sides}",
                    "event": "critical_success"
                }
            )
        elif is_critical_failure:
            dice_logger.info(
                "Critical failure rolled!",
                extra={
                    "result": result,
                    "dice_type": f"d{sides}",
                    "event": "critical_failure"
                }
            )
        
        return result
        
    except Exception as e:
        dice_logger.error(
            "Error occurred during dice roll",
            exc_info=True,
            extra={
                "dice_type": f"d{sides}",
                "error_type": type(e).__name__,
                "event": "dice_roll_failed"
            }
        )
        raise

def roll_multiple_dice(count: int, sides: int = 20) -> list[int]:
    """
    Roll multiple dice and return all results.
    
    Args:
        count: Number of dice to roll
        sides: Number of sides on each die (default 20)
        
    Returns:
        list[int]: List of all dice roll results
    """
    if count < 1:
        dice_logger.error(
            "Invalid dice count specified",
            extra={
                "count": count,
                "error": "count_must_be_positive",
                "event": "multiple_dice_error"
            }
        )
        raise ValueError("Must roll at least 1 die")
    
    if count > 100:  # Reasonable limit
        dice_logger.warning(
            "Large number of dice requested",
            extra={
                "count": count,
                "sides": sides,
                "event": "large_dice_roll"
            }
        )
    
    dice_logger.info(
        f"Rolling {count}d{sides}",
        extra={
            "count": count,
            "sides": sides,
            "event": "multiple_dice_start"
        }
    )
    
    try:
        results = []
        for i in range(count):
            result = roll_dice(sides)
            results.append(result)
        
        total = sum(results)
        average = total / count
        max_possible = count * sides
        min_possible = count
        
        dice_logger.info(
            f"Multiple dice roll completed: {results}",
            extra={
                "count": count,
                "sides": sides,
                "results": results,
                "total": total,
                "average": round(average, 2),
                "max_possible": max_possible,
                "min_possible": min_possible,
                "percentage_of_max": round((total / max_possible) * 100, 1),
                "event": "multiple_dice_complete"
            }
        )
        
        return results
        
    except Exception as e:
        dice_logger.error(
            "Error occurred during multiple dice roll",
            exc_info=True,
            extra={
                "count": count,
                "sides": sides,
                "error_type": type(e).__name__,
                "event": "multiple_dice_failed"
            }
        )
        raise

def roll_with_modifier(sides: int = 20, modifier: int = 0) -> tuple[int, int]:
    """
    Roll a dice with a modifier applied.
    
    Args:
        sides: Number of sides on the dice (default 20)
        modifier: Modifier to add to the roll (can be negative)
        
    Returns:
        tuple[int, int]: (base_roll, modified_result)
    """
    dice_logger.debug(
        f"Rolling d{sides} with modifier {modifier:+d}",
        extra={
            "sides": sides,
            "modifier": modifier,
            "event": "modified_roll_start"
        }
    )
    
    try:
        base_roll = roll_dice(sides)
        modified_result = base_roll + modifier
        
        # Ensure result is not negative (minimum 1)
        final_result = max(1, modified_result)
        
        dice_logger.info(
            f"Modified dice roll: {base_roll} + {modifier:+d} = {final_result}",
            extra={
                "sides": sides,
                "base_roll": base_roll,
                "modifier": modifier,
                "modified_result": modified_result,
                "final_result": final_result,
                "was_clamped": final_result != modified_result,
                "event": "modified_roll_complete"
            }
        )
        
        return base_roll, final_result
        
    except Exception as e:
        dice_logger.error(
            "Error occurred during modified dice roll",
            exc_info=True,
            extra={
                "sides": sides,
                "modifier": modifier,
                "error_type": type(e).__name__,
                "event": "modified_roll_failed"
            }
        )
        raise

def advantage_roll(sides: int = 20) -> tuple[int, int, int]:
    """
    Roll with advantage (roll twice, take higher).
    
    Args:
        sides: Number of sides on the dice (default 20)
        
    Returns:
        tuple[int, int, int]: (roll1, roll2, result)
    """
    dice_logger.debug(
        f"Rolling d{sides} with advantage",
        extra={
            "sides": sides,
            "roll_type": "advantage",
            "event": "advantage_roll_start"
        }
    )
    
    try:
        roll1 = roll_dice(sides)
        roll2 = roll_dice(sides)
        result = max(roll1, roll2)
        
        dice_logger.info(
            f"Advantage roll: {roll1}, {roll2} → {result}",
            extra={
                "sides": sides,
                "roll1": roll1,
                "roll2": roll2,
                "result": result,
                "advantage_gained": result - min(roll1, roll2),
                "roll_type": "advantage",
                "event": "advantage_roll_complete"
            }
        )
        
        return roll1, roll2, result
        
    except Exception as e:
        dice_logger.error(
            "Error occurred during advantage roll",
            exc_info=True,
            extra={
                "sides": sides,
                "roll_type": "advantage",
                "error_type": type(e).__name__,
                "event": "advantage_roll_failed"
            }
        )
        raise

def disadvantage_roll(sides: int = 20) -> tuple[int, int, int]:
    """
    Roll with disadvantage (roll twice, take lower).
    
    Args:
        sides: Number of sides on the dice (default 20)
        
    Returns:
        tuple[int, int, int]: (roll1, roll2, result)
    """
    dice_logger.debug(
        f"Rolling d{sides} with disadvantage",
        extra={
            "sides": sides,
            "roll_type": "disadvantage",
            "event": "disadvantage_roll_start"
        }
    )
    
    try:
        roll1 = roll_dice(sides)
        roll2 = roll_dice(sides)
        result = min(roll1, roll2)
        
        dice_logger.info(
            f"Disadvantage roll: {roll1}, {roll2} → {result}",
            extra={
                "sides": sides,
                "roll1": roll1,
                "roll2": roll2,
                "result": result,
                "disadvantage_penalty": max(roll1, roll2) - result,
                "roll_type": "disadvantage",
                "event": "disadvantage_roll_complete"
            }
        )
        
        return roll1, roll2, result
        
    except Exception as e:
        dice_logger.error(
            "Error occurred during disadvantage roll",
            exc_info=True,
            extra={
                "sides": sides,
                "roll_type": "disadvantage",
                "error_type": type(e).__name__,
                "event": "disadvantage_roll_failed"
            }
        )
        raise