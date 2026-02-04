"""Add category_group column to CSV based on CB2 navigation structure."""
import csv
from pathlib import Path

# Mapping from sub_category to category_group based on CB2 website navigation
SUBCATEGORY_TO_GROUP = {
    # FURNITURE - LIVING ROOM FURNITURE
    'Sofas': 'LIVING ROOM FURNITURE',
    'Sectionals': 'LIVING ROOM FURNITURE',
    'Accent Chairs': 'LIVING ROOM FURNITURE',
    'Coffee Tables': 'LIVING ROOM FURNITURE',
    'Side Tables': 'LIVING ROOM FURNITURE',
    'Console Tables': 'LIVING ROOM FURNITURE',
    'Media Consoles': 'LIVING ROOM FURNITURE',
    'Benches & Ottomans': 'LIVING ROOM FURNITURE',
    
    # FURNITURE - DINING & KITCHEN FURNITURE
    'Dining Tables': 'DINING & KITCHEN FURNITURE',
    'Dining Chairs': 'DINING & KITCHEN FURNITURE',
    'Bar & Counter Stools': 'DINING & KITCHEN FURNITURE',
    'Dining Banquettes & Benches': 'DINING & KITCHEN FURNITURE',
    
    # FURNITURE - BEDROOM FURNITURE
    'Beds': 'BEDROOM FURNITURE',
    'Nightstands': 'BEDROOM FURNITURE',
    
    # FURNITURE - OFFICE FURNITURE
    'Desks': 'OFFICE FURNITURE',
    'Office Chairs': 'OFFICE FURNITURE',
    'Bookcases': 'OFFICE FURNITURE',
    
    # FURNITURE - STORAGE FURNITURE
    'Storage Cabinets': 'STORAGE FURNITURE',
    
    # OUTDOOR - OUTDOOR LOUNGE FURNITURE
    'Outdoor Sofas & Sectionals': 'OUTDOOR LOUNGE FURNITURE',
    'Outdoor Coffee Tables': 'OUTDOOR LOUNGE FURNITURE',
    
    # OUTDOOR - OUTDOOR DINING FURNITURE
    'Outdoor Dining Tables': 'OUTDOOR DINING FURNITURE',
    'Outdoor Dining Chairs': 'OUTDOOR DINING FURNITURE',
    
    # OUTDOOR - OUTDOOR DECOR
    'Outdoor Planters': 'OUTDOOR DECOR',
    'Outdoor Accessories': 'OUTDOOR DECOR',
    'Outdoor Throw Pillows': 'OUTDOOR DECOR',
    'Outdoor Entertaining': 'OUTDOOR DECOR',
    
    # LIGHTING - All lighting subcategories map to LIGHTING
    'Pendant Lights & Chandeliers': 'LIGHTING',
    'Table Lamps': 'LIGHTING',
    'Floor Lamps': 'LIGHTING',
    'Flush Mounts': 'LIGHTING',
    'Wall Sconces': 'LIGHTING',
    
    # RUGS - All rugs map to RUGS
    'Area Rugs': 'RUGS',
    'Doormats': 'RUGS',
    
    # DECOR - MIRRORS & WALL DECOR
    'Wall Mirrors': 'MIRRORS & WALL DECOR',
    'Floor Mirrors': 'MIRRORS & WALL DECOR',
    'Wall Art': 'MIRRORS & WALL DECOR',
    'Wallpaper': 'MIRRORS & WALL DECOR',
    'Picture Frames': 'MIRRORS & WALL DECOR',
    
    # DECOR - PILLOWS & THROWS
    'Poufs': 'PILLOWS & THROWS',
    'Pillow Inserts': 'PILLOWS & THROWS',
    
    # DECOR - DECORATIVE ACCESSORIES
    'Candles & Fragrances': 'DECORATIVE ACCESSORIES',
    'Decorative Accents': 'DECORATIVE ACCESSORIES',
    
    # DECOR - ORGANIZATION & HARDWARE
    'Decorative Storage': 'ORGANIZATION & HARDWARE',
    'Office Accessories': 'ORGANIZATION & HARDWARE',
    'Fireplace Accessories': 'ORGANIZATION & HARDWARE',
    'Cabinet Hardware': 'ORGANIZATION & HARDWARE',
    'Curtain Rods & Hardware': 'ORGANIZATION & HARDWARE',
    
    # DECOR - CURTAINS & CURTAIN HARDWARE
    'Curtains': 'CURTAINS & CURTAIN HARDWARE',
    
    # BEDDING & BATH - BEDDING
    'Duvet Covers': 'BEDDING',
    'Quilts & Blankets': 'BEDDING',
    'Sheet Sets': 'BEDDING',
    'Pillow Shams & Pillowcases': 'BEDDING',
    'Bedding Essentials': 'BEDDING',
    
    # BEDDING & BATH - BATH
    'Bathroom Decor': 'BATH',
    
    # TABLETOP - All tabletop subcategories map to TABLETOP
    'Dinnerware': 'TABLETOP',
    'Drinkware & Bar': 'TABLETOP',
    'Serveware': 'TABLETOP',
    'Flatware': 'TABLETOP',
    'Kitchen & Table Linens': 'TABLETOP',
    'Kitchen Storage & Tools': 'TABLETOP',
    
    # SPECIAL CATEGORIES - Keep as-is
    'All Gifts': 'GIFTS',
    'All New': 'NEW',
    'All Sale': 'SALE',
    'All Rugs': 'RUGS',
    'Decor Sale': 'DECOR',
    'Furniture Sale': 'FURNITURE',
    'Lighting Sale': 'LIGHTING',
    'Outdoor Sale': 'OUTDOOR',
    'Rugs Sale': 'RUGS',
    'Sale In-Stock Tabletop': 'TABLETOP',
    'New Lighting': 'LIGHTING',
}


def get_category_group(category, sub_category):
    """Determine category_group based on category and sub_category."""
    sub_category = sub_category.strip()
    
    # First check direct mapping
    if sub_category in SUBCATEGORY_TO_GROUP:
        return SUBCATEGORY_TO_GROUP[sub_category]
    
    # Fallback: use category name if no specific mapping
    if not sub_category:
        return category.upper() if category else ''
    
    # Default fallback
    return category.upper() if category else ''


def add_category_groups(input_csv, output_csv):
    """Add category_group column to CSV."""
    rows = []
    
    # Read CSV
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        
        # Remove duplicate category_group columns if they exist
        while 'category_group' in fieldnames:
            fieldnames.remove('category_group')
        
        # Insert category_group after sub_category
        if 'sub_category' in fieldnames:
            sub_cat_idx = fieldnames.index('sub_category')
            new_fieldnames = list(fieldnames[:sub_cat_idx + 1]) + ['category_group'] + list(fieldnames[sub_cat_idx + 1:])
        else:
            new_fieldnames = list(fieldnames) + ['category_group']
        
        for row in reader:
            category = row.get('category', '').strip()
            sub_category = row.get('sub_category', '').strip()
            
            # Remove any existing category_group from row
            if 'category_group' in row:
                del row['category_group']
            
            # Get category_group
            category_group = get_category_group(category, sub_category)
            row['category_group'] = category_group
            
            rows.append(row)
    
    # Write CSV with new column
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Added category_group column to {output_csv}")
    print(f"Processed {len(rows)} products")
    
    # Show summary
    from collections import Counter
    groups = Counter([r['category_group'] for r in rows])
    print(f"\nCategory Groups Summary:")
    for group, count in sorted(groups.items()):
        print(f"  {group}: {count}")


if __name__ == '__main__':
    input_file = Path('cb2_all_products_final.csv')
    output_file = Path('cb2_all_products_final.csv')  # Overwrite same file
    
    if not input_file.exists():
        print(f"Error: {input_file} not found!")
        exit(1)
    
    add_category_groups(input_file, output_file)
    print("\nDone!")
