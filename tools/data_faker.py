# tools/data_faker.py
#
# Utility script to populate the database with a large amount of realistic
# dummy data for performance testing and stress-testing the application UI.

import sys
import argparse
from pathlib import Path
from faker import Faker

# --- Setup to allow module imports ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.db_connector import DBConnector
from src.python.repository.chapter_repository import ChapterRepository
from src.python.repository.character_repository import CharacterRepository
from src.python.repository.lore_repository import LoreRepository

# --- Configuration Profiles ---
# Defines the number of entities to generate for each profile size.
DATA_PROFILES = {
    "small": {
        "chapters": 10,
        "characters": 5,
        "lore": 20,
        "max_paragraphs": 5
    },
    "medium": {
        "chapters": 50,
        "characters": 25,
        "lore": 100,
        "max_paragraphs": 10
    },
    "large": {
        "chapters": 250,
        "characters": 100,
        "lore": 500,
        "max_paragraphs": 20
    }
}

def generate_fake_data(db_connector: DBConnector, profile_name: str):
    """Generates and inserts fake data into the database based on a profile."""
    fake = Faker()
    profile = DATA_PROFILES[profile_name]
    
    NUM_CHAPTERS = profile['chapters']
    NUM_CHARACTERS = profile['characters']
    NUM_LORE_ENTRIES = profile['lore']
    MAX_PARAGRAPHS_PER_CHAPTER = profile['max_paragraphs']

    print(f"\n--- Generating Data ({profile_name.upper()} Profile) ---")
    
    # --- Chapters ---
    print(f"\n--- Generating {NUM_CHAPTERS} Chapters ---")
    
    chapter_repo = ChapterRepository(db_connector)
    # Determine the starting sort order by getting the current max
    existing_chapters = chapter_repo.get_all_chapters()
    max_sort_order = existing_chapters[-1]['Sort_Order'] if existing_chapters else 0
    
    for i in range(1, NUM_CHAPTERS + 1):
        title = f"Chapter {max_sort_order + i}: {fake.catch_phrase()}"
        
        # Generate simple HTML content with paragraphs
        html_content = "".join([f"<p>{fake.paragraph()}</p>" for _ in range(fake.random_int(min=3, max=MAX_PARAGRAPHS_PER_CHAPTER))])
        
        # Create the chapter
        chapter_id = chapter_repo.create_chapter(
            title=title, 
            sort_order=max_sort_order + i
        )
        
        if chapter_id:
            # Update content in a second step, mimicking how the UI might save
            chapter_repo.update_chapter_content(chapter_id, html_content)
        
        if i % (NUM_CHAPTERS // 5 or 1) == 0: # Print update roughly every 20%
            print(f"  ... Created {i} chapters.")
            
    # --- Characters ---
    print(f"\n--- Generating {NUM_CHARACTERS} Characters ---")
    character_repo = CharacterRepository(db_connector)
    for i in range(NUM_CHARACTERS):
        name = fake.unique.name()
        description = fake.paragraph()
        status = fake.random_element(elements=('Alive', 'Deceased', 'Unknown'))
        character_repo.create_character(name=name, description=description, status=status)
        
    # --- Lore Entries ---
    print(f"\n--- Generating {NUM_LORE_ENTRIES} Lore Entries ---")
    lore_repo = LoreRepository(db_connector)
    categories = ['Location', 'Magic', 'Culture', 'History', 'Item', 'Person']
    for i in range(NUM_LORE_ENTRIES):
        title = fake.unique.word().capitalize()
        content = fake.text(max_nb_chars=500)
        category = fake.random_element(elements=categories)
        lore_repo.create_lore_entry(title=title, content=content, category=category)
        
    print(f"\n✅ Data generation complete: {NUM_CHAPTERS} Ch, {NUM_CHARACTERS} Char, {NUM_LORE_ENTRIES} Lore.")


def run_data_faker():
    """Main execution point for the data faker utility, handling arguments."""
    print("--- Narrative Forge Data Faker Utility ---")
    
    parser = argparse.ArgumentParser(
        description="Populate the database with test data.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '--size',
        type=str,
        default='medium',
        choices=DATA_PROFILES.keys(),
        help=f"The size profile for data generation. Options: {', '.join(DATA_PROFILES.keys())}."
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help="Execute the script without the interactive confirmation warning."
    )
    
    # --- New Required Argument ---
    parser.add_argument(
        'project_path',
        type=str,
        help="The full path to the root project folder (e.g., /path/to/projects/MyProject)."
    )
    
    args = parser.parse_args()

    # Determine database path
    project_path = Path(args.project_path)
    if not project_path.is_dir():
        print(f"❌ ERROR: Project path not found or is not a directory: {project_path}")
        sys.exit(1)

    project_name = project_path.name
    dynamic_db_path = project_path / f"{project_name}.db"

    # Safety Check
    if not args.force:
        print("\n⚠️ WARNING: This will add a large amount of test data to the current project.")
        print(f"Selected profile: {args.size.upper()} ({DATA_PROFILES[args.size]['chapters']} chapters, etc.).")
        print(f"Target DB: {dynamic_db_path}")
        print("To proceed, run with the --force flag (e.g., python data_faker.py /path/to/project --force)")
        sys.exit(0)

    # --- Use Dynamic Path for DBConnector ---
    db_connector = DBConnector(db_path=str(dynamic_db_path))
    
    if not db_connector.connect():
        print("❌ ERROR: Could not connect to the database. Ensure the database has been reset first.")
        sys.exit(1)
        
    try:
        generate_fake_data(db_connector, args.size)
    except Exception as e:
        print(f"❌ FATAL ERROR during data generation: {e}")
    finally:
        db_connector.close()

if __name__ == '__main__':
    run_data_faker()