def add_item_to_inventory(inventory: list, item: str) -> list:
    """Add an item to the inventory."""
    inventory.append(item)
    return inventory

def remove_item_from_inventory(inventory: list, item: str) -> list:
    if item in inventory:
        inventory.remove(item)
    return inventory

def show_inventory(inventory: list) -> str:
    if not inventory:
        return "Your inventory is empty."
    return "\n".join(f"- {item}" for item in inventory)
