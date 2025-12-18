import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Optional
import os
import re


class RecipeBookManager:
    def __init__(self, credentials_path: str):
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.recipes_ref = self.db.collection('recipes')
        self.favorites_ref = self.db.collection('favorites')
    
    def generate_recipe_id(self, title: str, user_id: str) -> str:
        clean_title = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        clean_title = re.sub(r'\s+', '-', clean_title.strip())
        clean_title = re.sub(r'-+', '-', clean_title)
        
        base_id = clean_title[:50]
        
        recipe_id = base_id
        counter = 1
        while self.recipe_exists(recipe_id):
            recipe_id = f"{base_id}-{counter}"
            counter += 1
        
        return recipe_id
    
    def recipe_exists(self, recipe_id: str) -> bool:
        doc = self.recipes_ref.document(recipe_id).get()
        return doc.exists
    
    def create_recipe(self, user_id: str, title: str, description: str,
                     prep_time: int, cook_time: int, servings: int,
                     ingredients: List[str], instructions: List[str],
                     category: str, tags: List[str] = None) -> str:
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
        
        recipe_id = self.generate_recipe_id(title, user_id)
        
        doc_ref = self.recipes_ref.document(recipe_id)
        doc_ref.set(recipe_data)
        
        return recipe_id
    
    def get_recipe(self, recipe_id: str) -> Optional[Dict]:
        doc = self.recipes_ref.document(recipe_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None
    
    def update_recipe(self, recipe_id: str, user_id: str, **updates) -> bool:
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
        try:
            recipe_ref = self.recipes_ref.document(recipe_id)
            current = recipe_ref.get()
            
            if not current.exists:
                return False
            
            if current.to_dict().get('userId') != user_id:
                return False
            
            recipe_ref.delete()
        
            self.remove_from_favorites(recipe_id, user_id)
            
            return True
        except:
            return False
    
    def get_user_recipes(self, user_id: str, category: str = None, 
                        tag: str = None) -> List[Dict]:
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
    
    def search_recipes_by_title(self, user_id: str, search_term: str) -> List[Dict]:
        all_recipes = self.get_user_recipes(user_id)
        search_term_lower = search_term.lower()
        
        matching_recipes = [
            recipe for recipe in all_recipes 
            if search_term_lower in recipe['title'].lower()
        ]
        
        return matching_recipes
    
    def add_to_favorites(self, recipe_id: str, user_id: str, notes: str = "") -> bool:
        try:
            recipe = self.get_recipe(recipe_id)
            if not recipe:
                return False
            
            if self.is_favorited(recipe_id, user_id):
                return False
            
            favorite_id = f"fav-{user_id}-{recipe_id}"
            favorite_data = {
                'recipeId': recipe_id,
                'userId': user_id,
                'notes': notes,
                'addedDate': firestore.SERVER_TIMESTAMP
            }
            
            self.favorites_ref.document(favorite_id).set(favorite_data)
            return True
        except:
            return False
    
    def remove_from_favorites(self, recipe_id: str, user_id: str) -> bool:
        """Remove a recipe from user's favorites"""
        try:
            favorite_id = f"fav-{user_id}-{recipe_id}"
            favorite_ref = self.favorites_ref.document(favorite_id)
            
            if favorite_ref.get().exists:
                favorite_ref.delete()
                return True
            return False
        except:
            return False
    
    def is_favorited(self, recipe_id: str, user_id: str) -> bool:
        """Check if a recipe is in user's favorites"""
        favorite_id = f"fav-{user_id}-{recipe_id}"
        doc = self.favorites_ref.document(favorite_id).get()
        return doc.exists
    
    def get_user_favorites(self, user_id: str) -> List[Dict]:
        """Get all favorited recipes for a user with full recipe details"""
        favorites = []
        query = self.favorites_ref.where('userId', '==', user_id)
        
        for doc in query.stream():
            fav_data = doc.to_dict()
            recipe_id = fav_data['recipeId']
            
            recipe = self.get_recipe(recipe_id)
            if recipe:
                recipe['favoriteNotes'] = fav_data.get('notes', '')
                recipe['favoritedDate'] = fav_data.get('addedDate')
                favorites.append(recipe)
        
        return favorites
    
    def toggle_favorite(self, recipe_id: str, user_id: str) -> bool:
        """Toggle favorite status (add if not favorited, remove if favorited)"""
        if self.is_favorited(recipe_id, user_id):
            return self.remove_from_favorites(recipe_id, user_id)
        else:
            return self.add_to_favorites(recipe_id, user_id)


class RecipeBookUI:
    
    def __init__(self, credentials_path: str, user_id: str):
        self.manager = RecipeBookManager(credentials_path)
        self.user_id = user_id
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60 + "\n")
    
    def input_with_prompt(self, prompt: str, default: str = None) -> str:
        if default:
            value = input(f"{prompt} [{default}]: ").strip()
            return value if value else default
        return input(f"{prompt}: ").strip()
    
    def press_enter_to_continue(self):
        input("\nPress Enter to continue...")
    
    def show_menu(self):
        self.clear_screen()
        self.print_header("🍳 RECIPE BOOK MANAGER 🍳")
        
        print("1. Add New Recipe")
        print("2. View All Recipes")
        print("3. View Recipe Details")
        print("4. Search Recipes")
        print("5. Update Recipe")
        print("6. Delete Recipe")
        print("7. Toggle Favorite")
        print("8. View Favorites")
        print("9. Exit")
        print()
    
    def add_recipe(self):
        self.clear_screen()
        self.print_header("ADD NEW RECIPE")
        
        title = self.input_with_prompt("Recipe Title")
        description = self.input_with_prompt("Description")
        
        try:
            prep_time = int(self.input_with_prompt("Prep Time (minutes)"))
            cook_time = int(self.input_with_prompt("Cook Time (minutes)"))
            servings = int(self.input_with_prompt("Number of Servings"))
        except ValueError:
            print("\n❌ Error: Time and servings must be numbers!")
            self.press_enter_to_continue()
            return
        
        print("\nEnter ingredients (one per line, empty line when done):")
        ingredients = []
        i = 1
        while True:
            ingredient = input(f"  {i}. ").strip()
            if not ingredient:
                break
            ingredients.append(ingredient)
            i += 1
        
        if not ingredients:
            print("\n❌ Error: Recipe must have at least one ingredient!")
            self.press_enter_to_continue()
            return
        
        print("\nEnter instructions (one per line, empty line when done):")
        instructions = []
        i = 1
        while True:
            instruction = input(f"  {i}. ").strip()
            if not instruction:
                break
            instructions.append(instruction)
            i += 1
        
        if not instructions:
            print("\n❌ Error: Recipe must have at least one instruction!")
            self.press_enter_to_continue()
            return
        
        category = self.input_with_prompt("Category (e.g., Dessert, Main Course, Appetizer)")
        
        tags_input = self.input_with_prompt("Tags (comma-separated, e.g., italian, quick, healthy)")
        tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
        
        recipe_id = self.manager.create_recipe(
            user_id=self.user_id,
            title=title,
            description=description,
            prep_time=prep_time,
            cook_time=cook_time,
            servings=servings,
            ingredients=ingredients,
            instructions=instructions,
            category=category,
            tags=tags
        )
        
        print(f"\n✅ Recipe '{title}' created successfully!")
        print(f"Recipe ID: {recipe_id}")
        self.press_enter_to_continue()
    
    def view_all_recipes(self):
        self.clear_screen()
        self.print_header("ALL RECIPES")
        
        recipes = self.manager.get_user_recipes(self.user_id)
        
        if not recipes:
            print("No recipes found. Add your first recipe!")
        else:
            for i, recipe in enumerate(recipes, 1):
                total_time = recipe['prepTime'] + recipe['cookTime']
                
                is_fav = self.manager.is_favorited(recipe['id'], self.user_id)
                fav_icon = "⭐" if is_fav else "  "
                
                print(f"{fav_icon} {i}. {recipe['title']}")
                print(f"   📁 {recipe['category']} | ⏱️  {total_time} min | 🍽️  {recipe['servings']} servings")
                print(f"   ID: {recipe['id']}")
                if recipe['tags']:
                    print(f"   🏷️  {', '.join(recipe['tags'])}")
                print()
        
        print(f"Total: {len(recipes)} recipes")
        self.press_enter_to_continue()
    
    def view_recipe_details(self):
        self.clear_screen()
        self.print_header("VIEW RECIPE DETAILS")
        
        recipe_id = self.input_with_prompt("Enter Recipe ID")
        recipe = self.manager.get_recipe(recipe_id)
        
        if not recipe:
            print("\n❌ Recipe not found!")
        else:
            is_fav = self.manager.is_favorited(recipe_id, self.user_id)
            fav_status = "⭐ FAVORITED" if is_fav else "☆ Not Favorited"
            
            print(f"\n{'='*60}")
            print(f"📖 {recipe['title'].upper()} {fav_status}")
            print(f"{'='*60}")
            print(f"\n{recipe['description']}")
            print(f"\n⏱️  Prep: {recipe['prepTime']} min | Cook: {recipe['cookTime']} min | Total: {recipe['prepTime'] + recipe['cookTime']} min")
            print(f"🍽️  Servings: {recipe['servings']}")
            print(f"📁 Category: {recipe['category']}")
            
            print(f"\n📝 INGREDIENTS:")
            for ingredient in recipe['ingredients']:
                print(f"  • {ingredient}")
            
            print(f"\n👨‍🍳 INSTRUCTIONS:")
            for i, instruction in enumerate(recipe['instructions'], 1):
                print(f"  {i}. {instruction}")
            
            if recipe['tags']:
                print(f"\n🏷️  Tags: {', '.join(recipe['tags'])}")
            
            print(f"\n🆔 Recipe ID: {recipe['id']}")
            print(f"{'='*60}")
        
        self.press_enter_to_continue()
    
    def search_recipes(self):
        self.clear_screen()
        self.print_header("SEARCH RECIPES")
        
        print("1. Search by Category")
        print("2. Search by Tag")
        print("3. Search by Title")
        print()
        
        choice = self.input_with_prompt("Choose search type (1, 2, or 3)")
        
        if choice == '1':
            category = self.input_with_prompt("Enter category")
            recipes = self.manager.get_user_recipes(self.user_id, category=category)
            search_term = f"Category: {category}"
        elif choice == '2':
            tag = self.input_with_prompt("Enter tag")
            recipes = self.manager.get_user_recipes(self.user_id, tag=tag)
            search_term = f"Tag: {tag}"
        elif choice == '3':
            title_search = self.input_with_prompt("Enter title or keyword")
            recipes = self.manager.search_recipes_by_title(self.user_id, title_search)
            search_term = f"Title: {title_search}"
        else:
            print("\n❌ Invalid choice!")
            self.press_enter_to_continue()
            return
        
        print(f"\n--- Results for {search_term} ---\n")
        
        if not recipes:
            print("No recipes found.")
        else:
            for i, recipe in enumerate(recipes, 1):
                is_fav = self.manager.is_favorited(recipe['id'], self.user_id)
                fav_icon = "⭐" if is_fav else "  "
                
                print(f"{fav_icon} {i}. {recipe['title']}")
                print(f"   ID: {recipe['id']}")
                print()
        
        print(f"Found {len(recipes)} recipe(s)")
        self.press_enter_to_continue()
    
    def update_recipe(self):
        """Interactive recipe update"""
        self.clear_screen()
        self.print_header("UPDATE RECIPE")
        
        recipe_id = self.input_with_prompt("Enter Recipe ID to update")
        recipe = self.manager.get_recipe(recipe_id)
        
        if not recipe:
            print("\n❌ Recipe not found!")
            self.press_enter_to_continue()
            return
        
        print(f"\nUpdating: {recipe['title']}")
        print("Leave blank to keep current value\n")
        
        updates = {}
        
        new_title = self.input_with_prompt("New title", recipe['title'])
        if new_title != recipe['title']:
            updates['title'] = new_title
        
        new_description = self.input_with_prompt("New description", recipe['description'])
        if new_description != recipe['description']:
            updates['description'] = new_description
        
        try:
            new_servings = self.input_with_prompt("New servings", str(recipe['servings']))
            if new_servings != str(recipe['servings']):
                updates['servings'] = int(new_servings)
        except ValueError:
            print("Invalid servings number, keeping original")
        
        if updates:
            success = self.manager.update_recipe(recipe_id, self.user_id, **updates)
            if success:
                print(f"\n✅ Recipe updated successfully!")
            else:
                print(f"\n❌ Failed to update recipe!")
        else:
            print("\n⚠️  No changes made.")
        
        self.press_enter_to_continue()
    
    def delete_recipe(self):
        self.clear_screen()
        self.print_header("DELETE RECIPE")
        
        recipe_id = self.input_with_prompt("Enter Recipe ID to delete")
        recipe = self.manager.get_recipe(recipe_id)
        
        if not recipe:
            print("\n❌ Recipe not found!")
            self.press_enter_to_continue()
            return
        
        print(f"\nAre you sure you want to delete '{recipe['title']}'?")
        confirm = self.input_with_prompt("Type 'yes' to confirm").lower()
        
        if confirm == 'yes':
            success = self.manager.delete_recipe(recipe_id, self.user_id)
            if success:
                print(f"\n✅ Recipe deleted successfully!")
            else:
                print(f"\n❌ Failed to delete recipe!")
        else:
            print("\n⚠️  Deletion cancelled.")
        
        self.press_enter_to_continue()
    
    def toggle_favorite_interactive(self):
        """Toggle favorite status for a recipe"""
        self.clear_screen()
        self.print_header("TOGGLE FAVORITE")
        
        recipe_id = self.input_with_prompt("Enter Recipe ID")
        recipe = self.manager.get_recipe(recipe_id)
        
        if not recipe:
            print("\n❌ Recipe not found!")
            self.press_enter_to_continue()
            return
        
        is_currently_fav = self.manager.is_favorited(recipe_id, self.user_id)
        
        if is_currently_fav:
            print(f"\n'{recipe['title']}' is currently FAVORITED ⭐")
            confirm = self.input_with_prompt("Remove from favorites? (yes/no)").lower()
            if confirm == 'yes':
                success = self.manager.remove_from_favorites(recipe_id, self.user_id)
                if success:
                    print(f"\n✅ Removed from favorites!")
                else:
                    print(f"\n❌ Failed to remove from favorites!")
        else:
            print(f"\n'{recipe['title']}' is not currently favorited")
            confirm = self.input_with_prompt("Add to favorites? (yes/no)").lower()
            if confirm == 'yes':
                notes = self.input_with_prompt("Add notes (optional)", "")
                success = self.manager.add_to_favorites(recipe_id, self.user_id, notes)
                if success:
                    print(f"\n✅ Added to favorites! ⭐")
                else:
                    print(f"\n❌ Failed to add to favorites!")
        
        self.press_enter_to_continue()
    
    def view_favorites(self):
        """View all favorited recipes"""
        self.clear_screen()
        self.print_header("⭐ FAVORITE RECIPES ⭐")
        
        favorites = self.manager.get_user_favorites(self.user_id)
        
        if not favorites:
            print("No favorite recipes yet. Mark some recipes as favorites!")
        else:
            for i, recipe in enumerate(favorites, 1):
                total_time = recipe['prepTime'] + recipe['cookTime']
                print(f"⭐ {i}. {recipe['title']}")
                print(f"   📁 {recipe['category']} | ⏱️  {total_time} min | 🍽️  {recipe['servings']} servings")
                print(f"   ID: {recipe['id']}")
                if recipe.get('favoriteNotes'):
                    print(f"   📌 Notes: {recipe['favoriteNotes']}")
                if recipe['tags']:
                    print(f"   🏷️  {', '.join(recipe['tags'])}")
                print()
        
        print(f"Total Favorites: {len(favorites)}")
        self.press_enter_to_continue()
    
    def run(self):
        """Main program loop"""
        while True:
            self.show_menu()
            choice = input("Choose an option (1-9): ").strip()
            
            if choice == '1':
                self.add_recipe_interactive()
            elif choice == '2':
                self.view_all_recipes()
            elif choice == '3':
                self.view_recipe_details()
            elif choice == '4':
                self.search_recipes()
            elif choice == '5':
                self.update_recipe_interactive()
            elif choice == '6':
                self.delete_recipe_interactive()
            elif choice == '7':
                self.toggle_favorite_interactive()
            elif choice == '8':
                self.view_favorites()
            elif choice == '9':
                self.clear_screen()
                print("\n👋 Thanks for using Recipe Book Manager!\n")
                break
            else:
                print("\n❌ Invalid option! Please choose 1-9.")
                self.press_enter_to_continue()


def main():
    credentials_path = r"C:\Users\parke\Documents\CSE 310\recipe-book-manager-5e83d-firebase-adminsdk-fbsvc-9c141df542.json"
    
    user_id = 'Pward20'
    
    print("\n🍳 Welcome to Recipe Book Manager! 🍳\n")
    
    if not os.path.exists(credentials_path):
        print(f"❌ Error: Credentials file not found at: {credentials_path}")
        print("\nPlease update the credentials_path in the code.")
        return
    
    try:
        ui = RecipeBookUI(credentials_path, user_id)
        ui.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure your Firebase credentials are correct.")


if __name__ == '__main__':
    main()