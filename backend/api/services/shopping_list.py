from datetime import date

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
            key = (ingredient.name.lower(),
                   ingredient.measurement_unit.lower())
            if key not in ingredients_info:
                ingredients_info[key] = {
                    'name': ingredient.name,
                    'unit': ingredient.measurement_unit,
                    'amount': 0
                }
            amount = recipe_ingredient.amount
            ingredients_info[key]['amount'] += amount
    sorted_ingredients = sorted(
        ingredients_info.values(),
        key=lambda x: x['name']
    )
    today = date.today()
    months = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    formatted_date = f'{today.day} {months[today.month]} {today.year} года'
    content_lines = [
        f'Список покупок ({formatted_date})',
        '\nНеобходимые ингредиенты:',
    ]
    content_lines += [
        f'{index}. {item["name"]} - {item["amount"]} {item["unit"]}'
        for index, item in enumerate(sorted_ingredients, 1)
    ]
    content_lines.extend([
        '\nРецепты:',
    ])
    content_lines += [
        f'{index}. {recipe_info}'
        for index, recipe_info in enumerate(recipes_info, 1)
    ]
    content_lines.append('\nПриятного приготовления!')
    return '\n'.join(content_lines)
