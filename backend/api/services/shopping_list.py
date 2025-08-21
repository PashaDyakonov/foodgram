from datetime import datetime

from recipes.models import ShoppingList


from datetime import datetime
from collections import defaultdict

from recipes.models import ShoppingList, RecipeIngredient


def generate_shopping_list_content(user):
    recipes_info = []
    ingredients_info = {}
    shopping_items = ShoppingList.objects.filter(user=user).select_related(
        'recipe', 'recipe__author'
    )
    for item in shopping_items:
        recipe = item.recipe
        recipes_info.append(f'{recipe.name} (автор: {recipe.author.username})')
        recipe_ingredients = RecipeIngredient.objects.filter(
            recipe=recipe
        ).select_related('ingredient')
        for recipe_ingredient in recipe_ingredients:
            ingredient = recipe_ingredient.ingredient
            key = (ingredient.name.lower(), ingredient.measurement_unit.lower())
            if key not in ingredients_info:
                ingredients_info[key] = {
                    'name': ingredient.name.capitalize(),
                    'unit': ingredient.measurement_unit,
                    'amount': 0
                }
            try:
                amount = float(recipe_ingredient.amount)
            except (ValueError, TypeError):
                amount = 0
            ingredients_info[key]['amount'] += amount
    sorted_ingredients = sorted(
        ingredients_info.values(),
        key=lambda x: x['name']
    )
    current_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    content_lines = [
        f'Список покупок ({current_time})',
        '\nНеобходимые ингредиенты:',
    ]
    for index, item in enumerate(sorted_ingredients, 1):
        content_lines.append(
            f'{index}. {item["name"]} - {item["amount"]} {item["unit"]}')
    content_lines.extend([
        '\nРецепты:',
    ])
    for index, recipe_info in enumerate(recipes_info, 1):
        content_lines.append(f'{index}. {recipe_info}')
    content_lines.append('\nПриятного приготовления!')
    return '\n'.join(content_lines)
