from datetime import datetime

from recipes.models import ShoppingList


def get_pluralized_unit(amount, unit):
    """Функция для правильного склонения единиц измерения"""
    units_map = {
        'стакан': ('стакан', 'стакана', 'стаканов'),
        'столовая ложка': (
            'столовая ложка', 'столовые ложки', 'столовых ложек'
        ),
        'чайная ложка': ('чайная ложка', 'чайные ложки', 'чайных ложек'),
        'грамм': ('грамм', 'грамма', 'граммов'),
        'миллилитр': ('миллилитр', 'миллилитра', 'миллилитров'),
        'литр': ('литр', 'литра', 'литров'),
    }

    if unit not in units_map:
        return unit

    forms = units_map[unit]
    if amount % 10 == 1 and amount % 100 != 11:
        return forms[0]
    elif 2 <= amount % 10 <= 4 and (amount % 100 < 10 or amount % 100 >= 20):
        return forms[1]
    return forms[2]


def generate_shopping_list_content(user):
    try:
        shopping_list = user.shoppers.latest('created_at')
    except ShoppingList.DoesNotExist:
        return None

    recipes_info = []
    ingredients_info = {}

    for recipe in shopping_list.recipe.select_related(
        'author'
    ).prefetch_related('ingredients'):
        recipes_info.append(f'{recipe.name} (автор: {recipe.author.username})')

        for ingredient in recipe.ingredients.all():
            key = (ingredient.name.lower(), ingredient.measurement_unit.lower())
            if key not in ingredients_info:
                ingredients_info[key] = {
                    'name': ingredient.name.capitalize(),
                    'unit': ingredient.measurement_unit,
                    'amount': 0
                }
            ingredients_info[key]['amount'] += ingredient.amount

    for item in ingredients_info.values():
        item['unit'] = get_pluralized_unit(item['amount'], item['unit'])

    sorted_ingredients = sorted(
        ingredients_info.values(),
        key=lambda x: x['name']
    )

    current_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    return '\n'.join([
        f'Список покупок ({current_time})',
        '\nНеобходимые ингредиенты:',
        *[f'{idx}. {item["name"]} - {item["amount"]} {item["unit"]}'
          for idx, item in enumerate(sorted_ingredients, 1)],
        '\nРецепты:',
        *[f'{idx}. {recipe}'
          for idx, recipe in enumerate(recipes_info, 1)],
        '\nПриятного приготовления!'
    ])
