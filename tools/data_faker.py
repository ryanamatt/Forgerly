# tools/data_faker.py

import sys
import argparse
from pathlib import Path
from faker import Faker
import random

# --- Setup to allow module imports ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.python.db_connector import DBConnector
from src.python.repository.chapter_repository import ChapterRepository
from src.python.repository.character_repository import CharacterRepository
from src.python.repository.lore_repository import LoreRepository

# --- Configuration Profiles ---
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
    """Generates and inserts fake data into the database based on the V1 schema."""
    fake = Faker()
    profile = DATA_PROFILES[profile_name]
    
    NUM_CHAPTERS = profile['chapters']
    NUM_CHARACTERS = profile['characters']
    NUM_LORE_ENTRIES = profile['lore']
    MAX_PARAGRAPHS_PER_CHAPTER = profile['max_paragraphs']

    print(f"\n--- Generating Data ({profile_name.upper()} Profile) ---")
    
    # --- 1. Characters (Generate first to assign to POV) ---
    print(f"\n--- Generating {NUM_CHARACTERS} Characters ---")
    character_repo = CharacterRepository(db_connector)
    character_ids = []

    for i in range(NUM_CHARACTERS):
        char_id = character_repo.create_character(
            name=fake.unique.name(),
            description=fake.paragraph(),
            status=fake.random_element(elements=('Alive', 'Deceased', 'Unknown', 'Major', 'Minor')),
            # New V1 Fields:
            age=random.randint(5, 150) if random.random() > 0.2 else None,
            date_of_birth=fake.date() if random.random() > 0.5 else None,
            occupation_school=fake.job(),
            physical_description=f"Eyes: {fake.color_name()}, Height: {random.randint(140, 200)}cm. {fake.sentence()}"
        )
        if char_id:
            character_ids.append(char_id)
        
    # --- 2. Chapters ---
    print(f"\n--- Generating {NUM_CHAPTERS} Chapters ---")
    chapter_repo = ChapterRepository(db_connector)
    existing_chapters = chapter_repo.get_all_chapters()
    max_sort_order = existing_chapters[-1]['Sort_Order'] if existing_chapters else 0
    
    for i in range(1, NUM_CHAPTERS + 1):
        title = f"Chapter {max_sort_order + i}: {fake.catch_phrase()}"
        html_content = "".join([f"<p>{fake.paragraph()}</p>" for _ in range(fake.random_int(min=3, max=MAX_PARAGRAPHS_PER_CHAPTER))])
        
        # New: Assign a POV Character ID from our generated list
        pov_id = random.choice(character_ids) if character_ids and random.random() > 0.3 else None

        chapter_id = chapter_repo.create_chapter(
            title=title, 
            sort_order=max_sort_order + i,
            pov_character_id=pov_id # Assuming repo is updated to accept this
        )
        
        if chapter_id:
            chapter_repo.update_chapter_content(chapter_id, html_content)
        
        if i % (max(1, NUM_CHAPTERS // 5)) == 0:
            print(f"  ... Created {i} chapters.")
            
    # --- 3. Lore Entries (with Hierarchy) ---
    print(f"\n--- Generating {NUM_LORE_ENTRIES} Lore Entries ---")
    lore_repo = LoreRepository(db_connector)
    categories = ['Magic', 'Culture', 'History', 'Item', 'Person', 'Mythology']
    lore_ids = []

    for i in range(NUM_LORE_ENTRIES):
        # 20% chance to be a sub-entry of an existing lore entry
        parent_id = random.choice(lore_ids) if (lore_ids and random.random() < 0.2) else None
        
        title = f"{fake.unique.word().capitalize()} {random.randint(1, 999)}"
        content = fake.text(max_nb_chars=800)
        category = fake.random_element(elements=categories)
        
        l_id = lore_repo.create_lore_entry(
            title=title, 
            content=content, 
            category=category,
            parent_lore_id=parent_id, # New V1 Field
            sort_order=random.randint(0, 10)
        )
        if l_id:
            lore_ids.append(l_id)
        
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