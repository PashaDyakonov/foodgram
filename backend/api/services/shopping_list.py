from django.template.loader import render_to_string
from datetime import datetime


def generate_shopping_list_content(user):
    shopping_list = user.shoppers.latest('created_at')
    ingredients = {}
    recipes = set()

    for recipe in shopping_list.recipe.all():
        recipes.add((recipe.name, recipe.author.username))
        for ingredient in recipe.ingredients.all():
            key = (ingredient.name, ingredient.measurement_unit)
            amount = ingredient.amount
            ingredients[key] = ingredients.get(key, 0) + amount

    formatted_ingredients = sorted(
        [
            (name.capitalize(), amount, unit)
            for (name, unit), amount in ingredients.items()
        ],
        key=lambda x: x[0]
    )

    return render_to_string('shopping_list.txt', {
        'date': datetime.now().strftime('%d.%m.%Y'),
        'ingredients': formatted_ingredients,
        'recipes': recipes,
    })
