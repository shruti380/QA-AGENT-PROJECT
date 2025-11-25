"""
Selenium Script Generator using RAG and LLM
"""
import re
from typing import Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from backend.vector_store import VectorStore
from backend.groq_client import GroqClient


class ScriptGenerator:
    """Generate Selenium WebDriver scripts from test cases"""
    
    def __init__(self, vector_store: VectorStore, llm_client: GroqClient):
        """
        Initialize script generator
        
        Args:
            vector_store: Vector store for document retrieval
            llm_client: LLM client for generation
        """
        self.vector_store = vector_store
        self.llm_client = llm_client
        
        self.system_prompt = """You are a Selenium WebDriver expert. Generate complete, runnable Python Selenium scripts.

REQUIREMENTS:
1. Use explicit waits (WebDriverWait) - NEVER use time.sleep() for waiting
2. Use appropriate selectors from the HTML (prefer IDs, then names, then CSS selectors)
3. Include proper error handling with try-except blocks
4. Add assertions to verify expected results using assert statements
5. Include setup (driver initialization) and teardown (driver.quit())
6. Add clear comments explaining each step
7. Make script runnable as standalone Python file with if __name__ == "__main__"
8. Import all necessary libraries
9. Use proper Selenium syntax for Chrome/Firefox WebDriver
10. Handle dynamic elements properly with WebDriverWait

CODE STRUCTURE:
- Create a test class
- Include __init__, setup, teardown, and test method
- Use descriptive method and variable names
- Add docstrings
- Include error messages in assertions

NEVER:
- Use time.sleep() for waiting (use WebDriverWait instead)
- Hardcode waits longer than 10 seconds
- Leave out error handling
- Forget to call driver.quit()
- Use deprecated Selenium methods

Generate ONLY Python code, no explanations or markdown."""
    
    def generate_selenium_script(
        self,
        test_case: Dict[str, Any],
        html_content: str,
        html_file_path: str = "checkout.html"
    ) -> str:
        """
        Generate Selenium script from test case
        
        Args:
            test_case: Test case dictionary
            html_content: HTML content for element extraction
            html_file_path: Path to HTML file (for script)
            
        Returns:
            Complete Python Selenium script
        """
        # Extract HTML elements for selectors
        html_elements = self._extract_html_elements(html_content)
        
        # Retrieve relevant documentation
        feature = test_case.get('feature', '')
        search_results = self.vector_store.similarity_search(feature, k=5)
        context = self._build_context(search_results)
        
        # Build prompt
        prompt = self._build_script_prompt(test_case, html_elements, context, html_file_path)
        
        # Generate script
        print(f"Generating Selenium script for {test_case['test_id']}...")
        try:
            script = self.llm_client.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,
                max_tokens=3000
            )
            
            # Clean script (remove markdown if present)
            script = self._clean_script(script)
            
            # Validate script
            self._validate_script(script)
            
            print(f"Generated script for {test_case['test_id']}")
            return script
            
        except Exception as e:
            raise Exception(f"Error generating script: {str(e)}")
    
    def _extract_html_elements(self, html_content: str) -> Dict[str, Any]:
        """Extract relevant HTML elements and their selectors"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        elements = {
            'ids': [],
            'names': [],
            'buttons': [],
            'inputs': [],
            'selects': []
        }
        
        # Extract elements with IDs
        for elem in soup.find_all(id=True):
            elem_id = elem.get('id')
            elem_info = {
                'id': elem_id,
                'tag': elem.name,
                'type': elem.get('type', ''),
                'selector': f"#{elem_id}"
            }
            elements['ids'].append(elem_info)
        
        # Extract form inputs
        for inp in soup.find_all(['input', 'textarea']):
            inp_info = {
                'tag': inp.name,
                'id': inp.get('id', ''),
                'name': inp.get('name', ''),
                'type': inp.get('type', 'text'),
                'placeholder': inp.get('placeholder', '')
            }
            elements['inputs'].append(inp_info)
        
        # Extract buttons
        for btn in soup.find_all(['button', 'input']):
            if btn.name == 'button' or btn.get('type') in ['submit', 'button']:
                btn_info = {
                    'tag': btn.name,
                    'id': btn.get('id', ''),
                    'onclick': btn.get('onclick', ''),
                    'text': btn.get_text(strip=True) if btn.name == 'button' else btn.get('value', '')
                }
                elements['buttons'].append(btn_info)
        
        # Extract select elements
        for sel in soup.find_all('select'):
            elements['selects'].append({
                'id': sel.get('id', ''),
                'name': sel.get('name', '')
            })
        
        return elements
    
    def _build_context(self, search_results) -> str:
        """Build context from search results"""
        context_parts = []
        for result in search_results:
            source = result['metadata'].get('source', 'unknown')
            content = result['content'][:500]  # Limit length
            context_parts.append(f"[{source}] {content}")
        return "\n".join(context_parts)
    
    def _build_script_prompt(
        self,
        test_case: Dict[str, Any],
        html_elements: Dict[str, Any],
        context: str,
        html_file_path: str
    ) -> str:
        """Build prompt for script generation"""
        
        # Format test steps
        test_steps_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(test_case['test_steps'])])
        
        # Format HTML elements
        elements_str = f"""Available HTML Elements:

IDs:
{self._format_elements(html_elements['ids'])}

Inputs:
{self._format_elements(html_elements['inputs'])}

Buttons:
{self._format_elements(html_elements['buttons'])}
"""
        
        prompt = f"""Generate a complete Python Selenium script for this test case:

TEST CASE:
- ID: {test_case['test_id']}
- Feature: {test_case['feature']}
- Scenario: {test_case['test_scenario']}
- Type: {test_case.get('test_type', 'positive')}

TEST STEPS:
{test_steps_str}

EXPECTED RESULT:
{test_case['expected_result']}

{elements_str}

CONTEXT FROM DOCUMENTATION:
{context}

REQUIREMENTS:
1. Create a test class named Test{test_case['test_id'].replace('-', '')}
2. Use file path: file://{html_file_path} (update as needed)
3. Use WebDriverWait for all element interactions
4. Add assertions for the expected result
5. Include error handling
6. Add comments for clarity
7. Make it executable as a standalone script

Generate the complete Python script now."""
        
        return prompt
    
    def _format_elements(self, elements: list) -> str:
        """Format elements for display"""
        if not elements:
            return "  None found"
        
        lines = []
        for elem in elements[:10]:  # Limit to first 10
            elem_str = "  - "
            if isinstance(elem, dict):
                for key, value in elem.items():
                    if value:
                        elem_str += f"{key}='{value}' "
            lines.append(elem_str)
        
        return "\n".join(lines)
    
    def _clean_script(self, script: str) -> str:
        """Clean generated script"""
        # Remove markdown code blocks
        script = re.sub(r'^```python\s*', '', script, flags=re.MULTILINE)
        script = re.sub(r'^```\s*', '', script, flags=re.MULTILINE)
        script = script.strip()
        
        return script
    
    def _validate_script(self, script: str) -> None:
        """Validate script syntax"""
        # Check for required imports
        required_imports = ['selenium', 'webdriver']
        for imp in required_imports:
            if imp not in script:
                print(f"Warning: Script may be missing '{imp}' import")
        
        # Check for basic structure
        if 'class ' not in script:
            raise Exception("Script missing class definition")
        
        if 'def ' not in script:
            raise Exception("Script missing method definitions")
        
        # Try to compile (syntax check)
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            raise Exception(f"Script has syntax error: {str(e)}")
    
    def save_script(self, script: str, filename: str, output_dir: str = "tests/generated_scripts") -> str:
        """
        Save generated script to file
        
        Args:
            script: Script content
            filename: Output filename
            output_dir: Output directory
            
        Returns:
            Full path to saved file
        """
        import os
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Ensure .py extension
        if not filename.endswith('.py'):
            filename += '.py'
        
        # Full path
        filepath = os.path.join(output_dir, filename)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script)
        
        print(f"Script saved to: {filepath}")
        return filepath


def test_script_generator():
    """Test the script generator"""
    from backend.vector_store import VectorStore
    from backend.groq_client import GroqClient
    
    print("Testing Script Generator...")
    
    # Mock test case
    test_case = {
        'test_id': 'TC-001',
        'feature': 'Discount Code',
        'test_scenario': 'Apply valid discount code SAVE15',
        'test_type': 'positive',
        'test_steps': [
            'Open checkout page',
            'Add item to cart',
            'Enter discount code SAVE15',
            'Click Apply button',
            'Verify discount is applied'
        ],
        'expected_result': '15% discount applied to order total',
        'grounded_in': 'product_specs.md'
    }
    
    # Simple HTML
    html_content = '''
    <html>
    <body>
        <input type="text" id="discount-code-input" />
        <button id="apply-discount-btn">Apply</button>
        <span id="discount-amount">$0.00</span>
    </body>
    </html>
    '''
    
    # Create components
    vs = VectorStore(index_path="test_vector_db")
    vs.add_documents([{
        'content': 'SAVE15 applies 15% discount',
        'metadata': {'source': 'product_specs.md'}
    }])
    
    llm = GroqClient()
    generator = ScriptGenerator(vs, llm)
    
    # Generate script
    try:
        script = generator.generate_selenium_script(test_case, html_content)
        print("\nGenerated script preview:")
        print(script[:500] + "...")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    test_script_generator()