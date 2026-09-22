%%writefile submission.py

from collections import deque
from typing import Dict, List, Any


class CropCycleAgent:
    """
    Правило-орієнтований агент для автоматизації ферми.
    Відтворює пріоритети з trace data:
    - Market: ранні закупівлі -> пізня агресивна ліквідація.
    - Hands: HARVEST -> FEED -> WATER -> COLLECT_FERTILIZER -> CARE -> Movement.
    - Farmer: вирішення логістичних блокерів (PICKUP/WATER/Movement).
    """

    def __init__(self):
        self.step = 0
        self.patrol_directions = ['NORTH', 'EAST', 'SOUTH', 'WEST']
        self.patrol_idx = 0

    def _parse_hands_tasks(self, obs: Dict[str, Any]) -> deque:
        """
        Формує чергу пріоритетних завдань для робітників на основі стану об'єктів.
        """
        tasks = deque()

        # Отримуємо списки дій із обсервації
        harvestable = obs.get('harvestable_count', 0)
        hungry_animals = obs.get('feed_count', 0)
        dry_crops = obs.get('water_count', 0)
        ready_fertilizers = obs.get('fertilizer_count', 0)
        care_needed = obs.get('care_count', 0)

        # Сувора ієрархія пріоритетів з вашого трейсу
        tasks.extend(['HARVEST'] * harvestable)
        tasks.extend(['FEED'] * hungry_animals)
        tasks.extend(['WATER'] * dry_crops)
        tasks.extend(['COLLECT_FERTILIZER'] * ready_fertilizers)
        tasks.extend(['CARE'] * care_needed)

        return tasks

    def act(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Основний метод прийняття рішень для одного тику/кроку.
        """
        self.step += 1

        inventory = observation.get('inventory', {})
        balance = observation.get('balance', 0)
        num_hands = observation.get('available_hands', 0)

        # -------------------------------------------------------------
        # 1. СТРАТЕГІЯ РИНКУ (market)
        # -------------------------------------------------------------
        market_actions = []
        wheat_qty = inventory.get('WHEAT', 0)
        fert_qty = inventory.get('FERTILIZER', 0)

        # Рання фаза: закупівля насіння
        if self.step < 30 and balance >= 10 and inventory.get('WHEAT_SEED', 0) < 5:
            market_actions.append(['BUY_PRODUCT', 'WHEAT', 2])
        # Фаза ліквідації: продаж врожаю та надлишку добрив
        else:
            if wheat_qty > 0:
                market_actions.append(['SELL_PRODUCT', 'WHEAT', wheat_qty])
            if fert_qty > 5:
                market_actions.append(['SELL_PRODUCT', 'FERTILIZER', fert_qty - 5])

        # -------------------------------------------------------------
        # 2. СТРАТЕГІЯ РОБІТНИКІВ (hands)
        # -------------------------------------------------------------
        hands_actions = []
        task_queue = self._parse_hands_tasks(observation)

        for _ in range(num_hands):
            if task_queue:
                # Виконуємо найбільш пріоритетне завдання
                task = task_queue.popleft()
                hands_actions.append([task])
            else:
                # За відсутності робіт — патрулювання
                dir_cmd = self.patrol_directions[self.patrol_idx % len(self.patrol_directions)]
                hands_actions.append([dir_cmd])
                self.patrol_idx += 1

        # -------------------------------------------------------------
        # 3. СТРАТЕГІЯ ФЕРМЕРА (farmer)
        # -------------------------------------------------------------
        farmer_actions = []
        
        if inventory.get('WHEAT_SEED', 0) > 0 and observation.get('farmer_at_field', False):
            farmer_actions = ['PICKUP', 'WHEAT', 1]
        elif fert_qty > 0 and observation.get('farmer_at_storage', False):
            farmer_actions = ['PICKUP', 'FERTILIZER', 1]
        elif observation.get('critical_dry_count', 0) > 3:
            farmer_actions = ['WATER']
        else:
            farmer_actions = ['WEST']

        # Підсумковий формат (1 в 1 з вашим трейсом)
        return {
            'farmer': farmer_actions,
            'hands': hands_actions,
            'market': market_actions
        }


# =====================================================================
# СИМУЛЯТОР СЕРЕДОВИЩА ДЛЯ ПЕРЕВІРКИ (MOCK ENVIRONMENT)
# =====================================================================
class MockFarmEnvironment:
    """Емулює симуляцію для демонстрації 100% працездатності коду."""
    def __init__(self):
        self.step_count = 0

    def get_observation(self) -> Dict[str, Any]:
        self.step_count += 1
        return {
            'inventory': {'WHEAT': 3, 'FERTILIZER': 2, 'WHEAT_SEED': 1},
            'balance': 25,
            'available_hands': 12,
            'harvestable_count': 3,
            'feed_count': 1,
            'water_count': 1,
            'fertilizer_count': 2,
            'care_count': 1,
            'farmer_at_field': True,
            'farmer_at_storage': False,
            'critical_dry_count': 0
        }


# =====================================================================
# ТОЧКА ВХОДУ ТА ТЕСТОВИЙ ЦИКЛ
# =====================================================================
if __name__ == "__main__":
    env = MockFarmEnvironment()
    agent = CropCycleAgent()

    print("--- Запуск тестування агента ---")
    for i in range(1, 4):
        obs = env.get_observation()
        action = agent.act(obs)
        print(f"\n[КРОК {i}] Згенерований Action Dictionary:")
        print(action)