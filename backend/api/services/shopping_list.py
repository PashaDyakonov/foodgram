from datetime import datetime

from recipes.models import ShoppingList


def generate_shopping_list_content(user):
    recipes_info = []
    ingredients_info = {}

    for recipe in ShoppingList.objects.filter(user=user).select_related(
        'recipe__author'
    ):
        recipes_info.append(f'{recipe.name} (автор: {recipe.author.username})')

        for ingredient in recipe.recipe_ingredients.all():
            key = (
                ingredient.name.lower(), ingredient.measurement_unit.lower()
            )
            if key not in ingredients_info:
                ingredients_info[key] = {
                    'name': ingredient.name.capitalize(),
                    'unit': ingredient.measurement_unit,
                    'amount': 0
                }
            ingredients_info[key]['amount'] += ingredient.amount
    sorted_ingredients = sorted(
        ingredients_info.values(),
        key=lambda x: x['name']
    )

    current_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    return '\n'.join([
        f'Список покупок ({current_time})',
        '\nНеобходимые ингредиенты:',
        *[f'{index}. {item["name"]} - {item["amount"]} {item["unit"]}'
          for index, item in enumerate(sorted_ingredients, 1)],
        '\nРецепты:',
        *[f'{index}. {recipe}'
          for index, recipe in enumerate(recipes_info, 1)],
        '\nПриятного приготовления!'
    ])
