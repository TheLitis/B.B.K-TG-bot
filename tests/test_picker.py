from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from bot.services.inventory_stub import InventoryStub
from bot.utils.formatting import calc_required


def test_calc_required_with_pack_step():
    assert calc_required(100, 10, 4.0) == 112.0  # 100 * 1.1 = 110 => округление до 112
    assert calc_required(25, 0, None) == 25.0
    assert calc_required(0, 10, 5.0) == 0.0


def test_inventory_search_filters():
    inventory = InventoryStub(BASE_DIR / "data" / "catalog.json")
    results = inventory.search("Ковровая плитка", {"Область применения": "Для офиса"})
    assert results, "Ожидались результаты поиска по ковровой плитке"
    for product in results:
        assert "Для офиса" in product.use

    options = inventory.filter_options("Ковровая плитка", "Производитель")
    assert "RusCarpetTiles (RCT)" in options
