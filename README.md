# Overview

I developed this Recipe Book Manager to deepen my understanding of cloud database integration and CRUD operations in real-world applications. This project demonstrates how to build a practical, user-friendly command-line application that stores and manages data in the cloud, making it accessible from anywhere.

The Recipe Book Manager is a Python-based application that integrates with Google Firebase Firestore to provide a complete recipe management system. Users can create, read, update, and delete recipes with detailed information including ingredients, instructions, cooking times, and categorization. The software features readable recipe IDs (like "chocolate-chip-cookies" instead of random strings), making recipes easy to search and reference. Additionally, the application includes an optional email notification system that sends real-time updates whenever recipes are created, modified, or deleted.

**How to Use:**
1. Install required dependencies: `pip install firebase-admin`
2. Download your Firebase credentials JSON file from the Firebase Console
3. Update the `credentials_path` in the code to point to your credentials file
4. Set your `user_id` in the main function
5. Run the program: `python recipe_book_manager.py`
6. Navigate the menu to add, view, search, update, or delete recipes
7. Use the favorites feature to mark your favorite recipes with the ⭐ icon


[Software Demo Video](https://youtu.be/kU6zXB5d2nE)

# Cloud Database

This project uses **Google Firebase Firestore**, a flexible, scalable NoSQL cloud database. Firestore was chosen for its real-time synchronization capabilities, simple setup, and generous free tier. It provides automatic scaling and built-in security features, making it ideal for learning cloud database integration.

**Database Structure:**

The database uses a **relational NoSQL design** with multiple collections that reference each other:

```
recipes (collection)
  └── {recipe-id} (document)
      ├── title: string
      ├── description: string
      ├── prepTime: integer (minutes)
      ├── cookTime: integer (minutes)
      ├── servings: integer
      ├── ingredients: array of strings
      ├── instructions: array of strings
      ├── category: string (e.g., "Dessert", "Main Course")
      ├── tags: array of strings (e.g., ["italian", "quick", "healthy"])
      ├── userId: string (identifies recipe owner)
      └── createdAt: timestamp

favorites (collection) - Related table for user favorites
  └── fav-{userId}-{recipeId} (document)
      ├── recipeId: string (references recipes collection)
      ├── userId: string (identifies user)
      ├── notes: string (optional personal notes)
      └── addedDate: timestamp
```

Recipe IDs are generated from the recipe title (e.g., "Chocolate Chip Cookies" becomes "chocolate-chip-cookies"), making them human-readable and easy to reference. 

**Relationship Design:**
- The `favorites` collection creates a many-to-many relationship between users and recipes
- Each favorite document uses a composite ID (`fav-{userId}-{recipeId}`) to ensure uniqueness
- When a recipe is deleted, the application automatically removes it from all users' favorites to maintain referential integrity
- The database uses compound queries to efficiently filter recipes by category, tags, or user ID, and to retrieve all favorited recipes with their full details

# Development Environment

**Tools Used:**
- Visual Studio Code (code editor)
- Python 3.x
- Firebase Console (database management)
- Git/GitHub (version control)
- Windows Command Prompt (application interface)

**Programming Language and Libraries:**

- **Python 3.x** - Primary programming language
- **firebase-admin** - Official Firebase Admin SDK for Python, providing authentication and database access
- **re** (Regular Expressions) - Used for generating clean, readable recipe IDs from titles
- **os** - For cross-platform terminal commands and file path handling
- **typing** - For type hints to improve code readability and maintainability

# Useful Websites

- [Firebase Documentation](https://firebase.google.com/docs) - Comprehensive guides for Firebase setup and usage
- [Firestore Python SDK Reference](https://firebase.google.com/docs/firestore/quickstart#python) - Official Python API documentation
- [Firebase Admin SDK Setup](https://firebase.google.com/docs/admin/setup) - Instructions for initializing the Admin SDK
- [Python Regular Expressions](https://docs.python.org/3/library/re.html) - Documentation for text processing and ID generation
- [Firestore Data Model](https://firebase.google.com/docs/firestore/data-model) - Understanding NoSQL document structure

# Future Work

- **Ratings & Reviews System** - Allow users to rate recipes (1-5 stars) and add detailed reviews after cooking
- **Cooking History Tracker** - Log every time a recipe is made with notes about modifications and success
- **Recipe Collections** - Create custom recipe collections/folders (e.g., "Holiday Recipes", "Quick Weeknight Dinners")
- **Email Notifications** - Send email updates when recipes are created, updated, or deleted
- **Export/Import Functionality** - Add ability to export recipes to PDF or import from popular recipe websites