"""
Quick test to generate a script
Save as: quick_test.py
Run: python quick_test.py
"""
import os
import sys

print("Testing Script Generator - Windows")
print("=" * 60)

# Check if we're in the right directory
if not os.path.exists("backend"):
    print("ERROR: Please run this from your project root directory")
    sys.exit(1)

try:
    from backend.script_generator import ScriptGenerator
    from backend.vector_store import VectorStore
    from backend.groq_client import GroqClient
    print("✓ Imports successful")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Initialize
print("\nInitializing components...")
vs = VectorStore(index_path="test_vector_db")
llm = GroqClient()
generator = ScriptGenerator(vs, llm)
print("✓ Components ready")

# Add minimal docs
print("\nAdding test documents...")
vs.add_documents([{
    'content': 'SAVE15 discount code applies 15% discount',
    'metadata': {'source': 'test.md'}
}])
print("✓ Documents added")

# Test case
test_case = {
    'test_id': 'TC-001',
    'feature': 'Discount Code',
    'test_scenario': 'Apply discount code',
    'test_type': 'positive',
    'test_steps': ['Open page', 'Enter code', 'Click apply'],
    'expected_result': '15% discount applied',
    'grounded_in': 'test.md'
}

# HTML
html = '<input id="code"/><button id="apply">Apply</button>'

# Generate!
print("\nGenerating script...")
print("This may take 10-30 seconds...")

try:
    script = generator.generate_selenium_script(test_case, html, "checkout.html")
    
    # Save it
    output_dir = "tests\\generated_scripts"
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, "test_tc001.py")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(script)
    
    print(f"\n✅ SUCCESS!")
    print(f"Script saved to: {filepath}")
    print(f"File size: {len(script)} characters")
    print("\nPreview (first 500 chars):")
    print("-" * 60)
    print(script[:500])
    print("...")
    print("-" * 60)
    
    # Verify file exists
    if os.path.exists(filepath):
        print(f"\n✓ File verified at: {os.path.abspath(filepath)}")
        print(f"  You can now view it with: type {filepath}")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()