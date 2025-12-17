
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Optional


class RecipeBookManager:
    def __init__(self, credentials_path: str):
        """Initialize Firebase connection"""
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.recipes_ref = self.db.collection('recipes')
    
    def create_recipe(self, user_id: str, title: str, description: str,
                     prep_time: int, cook_time: int, servings: int,
                     ingredients: List[str], instructions: List[str],
                     category: str, tags: List[str] = None) -> str:
        """Create a new recipe"""
        recipe_data = {
            'title': title,
            'description': description,
            'prepTime': prep_time,
            'cookTime': cook_time,
            'servings': servings,
            'ingredients': ingredients,
            'instructions': instructions,
            'category': category,
            'tags': tags or [],
            'userId': user_id,
            'createdAt': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = self.recipes_ref.document()
        doc_ref.set(recipe_data)
        return doc_ref.id
    
    def get_recipe(self, recipe_id: str) -> Optional[Dict]:
        """Get a single recipe by ID"""
        doc = self.recipes_ref.document(recipe_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None
    
    def update_recipe(self, recipe_id: str, user_id: str, **updates) -> bool:
        """Update a recipe"""
        try:
            recipe_ref = self.recipes_ref.document(recipe_id)
            current = recipe_ref.get()
            
            if not current.exists:
                return False
            
            if current.to_dict().get('userId') != user_id:
                return False
            
            recipe_ref.update(updates)
            return True
        except:
            return False
    
    def delete_recipe(self, recipe_id: str, user_id: str) -> bool:
        """Delete a recipe"""
        try:
            recipe_ref = self.recipes_ref.document(recipe_id)
            current = recipe_ref.get()
            
            if not current.exists:
                return False
            
            if current.to_dict().get('userId') != user_id:
                return False
            
            recipe_ref.delete()
            return True
        except:
            return False
    
    def get_user_recipes(self, user_id: str, category: str = None, 
                        tag: str = None) -> List[Dict]:
        """Get recipes for a user with optional filters"""
        query = self.recipes_ref.where('userId', '==', user_id)
        
        if category:
            query = query.where('category', '==', category)
        
        if tag:
            query = query.where('tags', 'array_contains', tag)
        
        recipes = []
        for doc in query.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            recipes.append(data)
        
        return recipes


def main():
   from recipe_book_manager import RecipeBookManager

# Initialize
manager = RecipeBookManager('/home/pward20/Documents/CSE 310/recipe-book-manager-5e83d-firebase-adminsdk-fbsvc-02ab2ebffb.json')
user_id = 'my_user_id'

# Create some recipes
cookies_id = manager.create_recipe(
    user_id=user_id,
    title='Chocolate Chip Cookies',
    description='Classic cookies',
    prep_time=15,
    cook_time=12,
    servings=24,
    ingredients=['flour', 'butter', 'sugar', 'eggs', 'chocolate chips'],
    instructions=['Mix ingredients', 'Bake at 375°F for 12 minutes'],
    category='Dessert',
    tags=['cookies', 'baking']
)

pizza_id = manager.create_recipe(
    user_id=user_id,
    title='Homemade Pizza',
    description='Delicious pizza from scratch',
    prep_time=20,
    cook_time=15,
    servings=4,
    ingredients=['pizza dough', 'tomato sauce', 'mozzarella', 'basil'],
    instructions=['Roll out dough', 'Add toppings', 'Bake at 450°F'],
    category='Main Course',
    tags=['italian', 'pizza']
)

# View all recipes
print("\n=== All My Recipes ===")
recipes = manager.get_user_recipes(user_id)
for recipe in recipes:
    print(f"- {recipe['title']} ({recipe['category']})")

# View only desserts
print("\n=== Desserts ===")
desserts = manager.get_user_recipes(user_id, category='Dessert')
for recipe in desserts:
    print(f"- {recipe['title']}")

# Update a recipe
manager.update_recipe(cookies_id, user_id, servings=36)
print("\n✓ Updated cookie recipe to serve 36")

# Get specific recipe
recipe = manager.get_recipe(cookies_id)
print(f"\nCookie Recipe Details:")
print(f"Servings: {recipe['servings']}")
print(f"Prep time: {recipe['prepTime']} minutes")


if __name__ == '__main__':
    main()